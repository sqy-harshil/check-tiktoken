import json
import os
import validators
import requests
from io import BytesIO

from typing import Union
import openai
from fastapi import HTTPException
from pydantic.error_wrappers import ValidationError
from openai.error import (
    Timeout,
    RateLimitError,
    APIError,
    ServiceUnavailableError,
    AuthenticationError,
    APIConnectionError,
    InvalidRequestError,
)

from config import OPENAI_API_PARAMS, AZURE_OPENAI_PARAMS
from prompts import FUNCTIONS_4, FUNCTIONS_8
from models import SimpleAudioResponse, DetailedAudioResponse
from named_tuples import AnalysisJSON


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


def get_analysis(
    audio_file, functions, analysis_type
) -> Union[AnalysisJSON, HTTPException]:
    try:
        call_log = openai.Audio.translate(
            model="whisper-1",
            file=audio_file,
            **OPENAI_API_PARAMS,
        )
        transcript = call_log["text"]
    except (
        Timeout,
        RateLimitError,
        APIError,
        ServiceUnavailableError,
        AuthenticationError,
        APIConnectionError,
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
                    "content": f"""
                        You are a helpful real-estate sales assistant. Based on the transcript log between a human salesperson and a customer, analyze the following parameters:
                        {analysis_type}
                    """,
                },
                {"role": "user", "content": f"{transcript}"},
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

    arguments = completion["choices"][0]["message"]["function_call"]["arguments"]
    usage = completion["usage"]
    json_object = json.loads(arguments)

    try:
        response_model = (
            SimpleAudioResponse
            if analysis_type == "FUNCTIONS_4"
            else DetailedAudioResponse
        )
        response_model(**json_object)
    except ValidationError as validationError:
        raise HTTPException(
            status_code=400,
            detail=f"Missing keys from response!\n{validationError.json()}",
        )

    return AnalysisJSON(
        json_object=json_object, token_usage=usage.to_dict(), script=str(transcript)
    )


def get_analysis_4(audio_file) -> Union[AnalysisJSON, HTTPException]:
    return get_analysis(audio_file, FUNCTIONS_4, "FUNCTIONS_4")


def get_analysis_8(audio_file) -> Union[AnalysisJSON, HTTPException]:
    return get_analysis(audio_file, FUNCTIONS_8, "FUNCTIONS_8")
