import json
import os
import validators
import requests
from io import BytesIO

import openai
from typing import Union
from jq import jq
from fastapi import HTTPException
from openai.error import (
    Timeout,
    RateLimitError,
    APIError,
    ServiceUnavailableError,
    AuthenticationError,
    APIConnectionError,
    InvalidRequestError,
)

from config import AZURE_OPENAI_PARAMS, DEEPGRAM_TOKEN, DEEPGRAM_API_BASE
from functions import *
from prompts import *
from enums import HttpStatusCode
from models import (
    DiarizedTranscriptObject,
    SummaryObject,
    UsageObject,
    RatingsObject,
    AudioRequest,
    DetailedAudioResponse,
)


def convert_url(url: str) -> Union[BytesIO, HTTPException]:
    if not validators.url(url):
        raise HTTPException(
            status_code=HttpStatusCode.BAD_REQUEST.value,
            detail="The server cannot process your request because the provided URL syntax is invalid or malformed!",
        )

    try:
        response = requests.get(url)

        if response.status_code == HttpStatusCode.OK.value:
            mp3_content = response.content
            buffer = BytesIO(mp3_content)
            buffer.name = "temp.mp3"
            return buffer
        elif response.status_code == HttpStatusCode.NOT_FOUND.value:
            raise HTTPException(
                status_code=HttpStatusCode.NOT_FOUND.value,
                detail="The input resource could not be found!",
            )
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="An error occurred while fetching the MP3 file!",
            )

    except requests.RequestException:
        raise HTTPException(
            status_code=HttpStatusCode.INTERNAL_SERVER_ERROR.value,
            detail="An error occurred while making the HTTP request!",
        )


def get_diarized_output(audio_data):
    print("Preparing diarization")

    headers = {
        "Authorization": f"Token {DEEPGRAM_TOKEN}",
        "content-type": "audio/mp3",
    }

    response = requests.post(DEEPGRAM_API_BASE, headers=headers, data=audio_data)

    diarized_output = []

    if response.status_code == HttpStatusCode.OK.value:
        response_json = response.json()

        filter_query = '.results.utterances[] | "[Speaker:\(.speaker)] \(.transcript)"'
        result = jq(filter_query).input(response_json)

        for item in result.all():
            print(item)
            diarized_output.append(item)

    else:
        raise HTTPException(
            status_code=HttpStatusCode.BAD_REQUEST.value,
            detail=f"An error occured while getting results from deepgram API, {response.status_code}:\n{response.text}",
        )

    return "\n".join(diarized_output)


def speaker_labels(diarized_output):
    print("Assigning Speakers")
    speaker_classification = openai.ChatCompletion.create(
        **AZURE_OPENAI_PARAMS,
        messages=[
            {
                "role": "user",
                "content": diarized_output,
            },
            {
                "role": "system",
                "content": diarization_system_prompt,
            },
        ],
        functions=[DIARIZATION],
        temperature=0.0,
        function_call={"name": "speaker_classifier"},
    )
    try:
        return (
            json.loads(
                speaker_classification["choices"][0]["message"]["function_call"][
                    "arguments"
                ]
            ),
            speaker_classification["usage"],
        )
    except Exception:
        raise HTTPException(
            status_code=HttpStatusCode.BAD_REQUEST.value,
            detail=f"Error occured while labelling speakers",
        )


def get_summary(transcript):
    print("Generating Summary")
    summary = openai.ChatCompletion.create(
        **AZURE_OPENAI_PARAMS,
        messages=[
            {
                "role": "user",
                "content": "Conversation: \n\n" + transcript,
            },
            {
                "role": "system",
                "content": summary_system_prompt,
            },
        ],
        functions=[CALL_SUMMARY],
        temperature=0.0,
        function_call={"name": "summarize"},
    )
    try:
        return (
            json.loads(summary["choices"][0]["message"]["function_call"]["arguments"]),
            summary["usage"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=HttpStatusCode.BAD_REQUEST.value,
            detail=f"Failed to generate summary",
        )


def get_analysis(audio_file, functions) -> DetailedAudioResponse:
    try:
        diarized_output = get_diarized_output(audio_file)
        print(diarized_output)
        labels, labels_call_usage = speaker_labels(diarized_output)
        diarized_transcript = diarized_output.replace(
            "[Speaker:0]", labels["speaker_0"]
        ).replace("[Speaker:1]", labels["speaker_1"])
    except (
        Timeout,
        RateLimitError,
        APIError,
        ServiceUnavailableError,
        AuthenticationError,
        APIConnectionError,
        HTTPException,
    ) as e:
        raise HTTPException(
            status_code=HttpStatusCode.INTERNAL_SERVER_ERROR.value,
            detail=f"Failed to generate transcript, {e.__class__}!\n{e._message}",
        )

    try:
        print("Preparing Analysis")
        ratings_completion = openai.ChatCompletion.create(
            **AZURE_OPENAI_PARAMS,
            messages=[
                {"role": "system", "content": ratings_system_prompt},
                {"role": "user", "content": diarized_transcript},
            ],
            functions=[functions],
            function_call={"name": "call_analysis"},
        )
    except (
        Timeout,
        RateLimitError,
        APIError,
        ServiceUnavailableError,
        AuthenticationError,
        APIConnectionError,
        InvalidRequestError,
    ) as e:
        raise HTTPException(
            status_code=HttpStatusCode.INTERNAL_SERVER_ERROR.value,
            detail=f"Failed to generate LLM Response, {e.__class__}!\n{e._message}",
        )

    # Prepare Summary

    summary, sumamry_usage = get_summary(diarized_transcript)
    summaryObject = SummaryObject(
        title=summary["title"],
        discussion_points=summary["discussion_points"],
        customer_queries=summary["customer_queries"],
        next_action_items=summary["next_action_items"],
    )

    # Prepare Ratings

    ratings_object = ratings_completion["choices"][0]["message"]["function_call"][
        "arguments"
    ]

    ratings = json.loads(ratings_object)

    ratingsObject = RatingsObject(
        customer_budget=ratings["customer_budget"],
        customer_eagerness_to_buy=ratings["customer_eagerness_to_buy"],
        customer_preferences=ratings["customer_preferences"],
        customer_sentiment_by_the_end_of_call=ratings[
            "customer_sentiment_by_the_end_of_call"
        ],
        meeting_request=ratings["meeting_request"],
        rudeness_or_politeness_metric=ratings["rudeness_or_politeness_metric"],
        salesperson_company_introduction=ratings["salesperson_company_introduction"],
        salesperson_understanding_of_customer_requirements=ratings[
            "salesperson_understanding_of_customer_requirements"
        ],
    )

    # Prepare Diarized Transcript

    diarizedTranscriptObject = DiarizedTranscriptObject(
        diarized_transcript=diarized_transcript
    )

    # Prepare an empty MP3

    mp3Object = AudioRequest(mp3_url=None)

    # Prepare Usage

    analysis_usage = ratings_completion["usage"]
    label_usage = labels_call_usage

    usage = {}
    usage["prompt_tokens"] = (
        analysis_usage["prompt_tokens"]
        + label_usage["prompt_tokens"]
        + sumamry_usage["prompt_tokens"]
    )
    usage["completion_tokens"] = (
        analysis_usage["completion_tokens"]
        + label_usage["completion_tokens"]
        + sumamry_usage["completion_tokens"]
    )
    usage["total_tokens"] = (
        analysis_usage["total_tokens"]
        + label_usage["total_tokens"]
        + sumamry_usage["total_tokens"]
    )

    usageObject = UsageObject(
        prompt_tokens=usage["prompt_tokens"],
        completion_tokens=usage["completion_tokens"],
        total_tokens=usage["total_tokens"],
    )

    return DetailedAudioResponse(
        mp3=mp3Object,
        summary=summaryObject,
        ratings=ratingsObject,
        script=diarizedTranscriptObject,
        token_usage=usageObject,
    )


def get_analysis_8(audio_file) -> DetailedAudioResponse:
    return get_analysis(audio_file, FUNCTIONS_8)
