import json
import validators
import requests
import re
from io import BytesIO

import openai
from typing import Union
from jq import jq
from fastapi import HTTPException

from config import (
    AZURE_OPENAI_PARAMS,
    SEED,
)
from prompts import *
from exceptions import InvalidSpeakerCountException
from enums import HttpStatusCode


def remove_whitespace_between_brackets(text):
    """Remove whitespace between brackets as a precaution"""

    pattern = re.compile(r"\[\s*Speaker:\s*(\d+)\s*\]")

    result = re.sub(pattern, lambda match: f"[Speaker:{match.group(1)}]", text)

    return result


def convert_url(url: str) -> Union[BytesIO, HTTPException]:
    """Convert an MP3 URL of a string object into BytesIO object"""

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


def get_diarized_output(audio_data, token, deepgram_api_base):
    """Get a diarized output from Deepgram API"""

    print("Preparing diarization")

    headers = {
        "Authorization": f"Token {token}",
        "content-type": "audio/mp3",
    }

    response = requests.post(deepgram_api_base, headers=headers, data=audio_data)

    diarized_output = []

    if response.status_code == HttpStatusCode.OK.value:
        response_json = response.json()

        filter_query = '.results.utterances[] | "[Speaker:\(.speaker)] \(.transcript)"'
        result = jq(filter_query).input(response_json)

        for item in result.all():
            diarized_output.append(item)

    else:
        raise HTTPException(
            status_code=HttpStatusCode.BAD_REQUEST.value,
            detail=f"An error occured while getting results from deepgram API, {response.status_code}:\n{response.text}",
        )

    return remove_whitespace_between_brackets("\n".join(diarized_output))


def get_speaker_labels(diarized_output, function):
    """Get the corresponding labels for the speakers on the basis of a diarized transcript"""

    print("Labelling Speakers")

    speaker_classification = openai.ChatCompletion.create(
        **AZURE_OPENAI_PARAMS,
        seed=SEED,
        messages=[
            {"role": "user", "content": diarized_output},
            {"role": "system", "content": diarization_system_prompt},
        ],
        functions=[function],
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


def get_summary(transcript, function):
    """Get an AI powered call summary"""

    summary = openai.ChatCompletion.create(
        **AZURE_OPENAI_PARAMS,
        messages=[
            {"role": "user", "content": "Conversation: \n\n" + transcript},
            {"role": "system", "content": summary_system_prompt},
        ],
        functions=[function],
        temperature=0.0,
        function_call={"name": "summarize"},
    )
    try:
        return (
            json.loads(summary["choices"][0]["message"]["function_call"]["arguments"]),
            summary["usage"],
        )
    except Exception:
        raise HTTPException(
            status_code=HttpStatusCode.BAD_REQUEST.value,
            detail=f"Failed to generate summary",
        )


def get_ratings(diarized_transcript, function):
    """Get an AI powered parameter evaluation"""

    print("Evaluating Ratings")

    ratings_completion = openai.ChatCompletion.create(
        **AZURE_OPENAI_PARAMS,
        seed=SEED,
        messages=[
            {"role": "system", "content": ratings_system_prompt},
            {"role": "user", "content": diarized_transcript},
        ],
        functions=[function],
        function_call={"name": "call_analysis"},
    )
    return (
        json.loads(
            ratings_completion["choices"][0]["message"]["function_call"]["arguments"]
        ),
        ratings_completion["usage"],
    )


def validate_speaker_count(text: str):
    """Validate if the Deepgram API generates only two speakers"""

    pattern = re.compile(r"\[speaker:(\d+)\]")

    matches = pattern.findall(text.lower())

    unique_speakers = set(matches)

    if len(unique_speakers) == 2:
        return text
    else:
        raise InvalidSpeakerCountException(
            "Invalid number of speakers. Expected 2, found {}".format(
                len(unique_speakers)
            )
        )
