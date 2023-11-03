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

from config import AZURE_OPENAI_PARAMS, DEEPGRAM_TOKEN
from functions import FUNCTIONS_4, FUNCTIONS_8, DIARIZATION, CALL_SUMMARY
from models import (
    DiarizedTranscriptObject,
    SummaryObject,
    UsageObject,
    RatingsObject,
    DetailedAudioResponse,
)


def convert_url(url: str) -> Union[BytesIO, HTTPException]:
    if not validators.url(url):
        raise HTTPException(
            status_code=400,
            detail="The server cannot process your request because the provided URL syntax is invalid or malformed!",
        )

    try:
        response = requests.get(url)

        if response.status_code == 200:
            mp3_content = response.content
            buffer = BytesIO(mp3_content)
            buffer.name = "temp.mp3"
            return buffer
        elif response.status_code == 404:
            raise HTTPException(
                status_code=404, detail="The input resource could not be found!"
            )
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail="An error occurred while fetching the MP3 file!",
            )

    except requests.RequestException:
        raise HTTPException(
            status_code=500, detail="An error occurred while making the HTTP request!"
        )


def get_diarized_output(audio_data):
    api_url = "https://api.deepgram.com/v1/listen?model=whisper-large&language=en-IN&diarize=true&punctuate=true&utterances=true"

    headers = {
        "Authorization": f"Token {DEEPGRAM_TOKEN}",
        "content-type": "audio/mp3",
    }

    response = requests.post(api_url, headers=headers, data=audio_data)

    diarized_output = []

    if response.status_code == 200:
        response_json = response.json()

        filter_query = '.results.utterances[] | "[Speaker:\(.speaker)] \(.transcript)"'
        result = jq(filter_query).input(response_json)

        for item in result.all():
            print(item)
            diarized_output.append(item)

    else:
        raise HTTPException(
            status_code=400,
            detail=f"An error occured while getting results from deepgram API, {response.status_code}:\n{response.text}",
        )

    return "\n".join(diarized_output)


def speaker_labels(diarized_output):
    speaker_classification = openai.ChatCompletion.create(
        **AZURE_OPENAI_PARAMS,
        messages=[
            {
                "role": "user",
                "content": diarized_output,
            },
            {
                "role": "system",
                "content": "You are a classification expert. You will be given a diariation with Speaker 1 and Speaker 0. Your job is to identify which one is a salesperson and which one is a customer",
            },
        ],
        functions=DIARIZATION,
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
            status_code=400, detail=f"Error occured while labelling speakers"
        )


def get_summary(transcript):
    summary = openai.ChatCompletion.create(
        **AZURE_OPENAI_PARAMS,
        messages=[
            {
                "role": "user",
                "content": "Conversation: \n\n" + transcript,
            },
            {
                "role": "system",
                "content": "You are an expert call analyst at Square Yards. You will be given a conversation between a customer and salesperson, your task is to generate a summary based on various parameters.",
            },
        ],
        functions=CALL_SUMMARY,
        temperature=0.0,
        function_call={"name": "summarize"},
    )
    try:
        return (
            json.loads(summary["choices"][0]["message"]["function_call"]["arguments"]),
            summary["usage"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate summary")


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
            status_code=500,
            detail=f"Failed to generate transcript, {e.__class__}!\n{e._message}",
        )

    try:
        completion = openai.ChatCompletion.create(
            **AZURE_OPENAI_PARAMS,
            messages=[
                {
                    "role": "system",
                    "content": """
                        You are a helpful real-estate sales assistant. Based on the transcript log between a human salesperson and a customer, analyze the following parameters:
                        {}
                    """.format(
                        "\n".join(FUNCTIONS_8[0]["parameters"]["properties"].keys())
                    ),
                },
                {"role": "user", "content": f"{diarized_transcript}"},
            ],
            functions=functions,
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
            status_code=500,
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

    ratings_object = completion["choices"][0]["message"]["function_call"]["arguments"]

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

    diarizedTranscriptObject = DiarizedTranscriptObject(diarized_transcript=diarized_transcript)

    # Prepare Usage

    analysis_usage = completion["usage"]
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
        summary=summaryObject,
        ratings=ratingsObject,
        script=diarizedTranscriptObject,
        token_usage=usageObject,
    )


def get_analysis_8(audio_file) -> DetailedAudioResponse:
    return get_analysis(audio_file, FUNCTIONS_8)
