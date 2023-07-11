import openai
import json
import os
import validators
import requests
from fastapi import HTTPException
from io import BytesIO
from typing import Dict, Union

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
openai.api_key = OPENAI_API_KEY


functions = [
    {
        "name": "call_analysis",
        "description": "Shows a detailed analysis of the call.",
        "parameters": {
            "type": "object",
            "properties": {
                "call_summary": {
                    "type": "string",
                    "description": "Detailed summary of the call.",
                },
                "next_action_item": {
                    "type": "string",
                    "description": "Detailed description of the next action item.",
                },
                "customer_sentiment": {
                    "type": "string",
                    "description": "Detailed description of the customer's sentiment",
                },
                "performance_of_the_salesperson": {
                    "type": "string",
                    "description": "Detailed description of the performance of the salesperson",
                },
            },
        },
    }
]


def convert_url(url: str) -> Union[BytesIO, HTTPException]:
    if not validators.url(url):
        raise HTTPException(
            status_code=400,
            detail="The server cannot process your request because the provided URL syntax is invalid or malformed!",
        )

    if not url.endswith(".mp3"):
        raise HTTPException(
            status_code=400, detail="The provided URL is not an MP3 file."
        )

    response = requests.get(url)

    if response.status_code == 200:
        mp3_content = response.content
        buffer = BytesIO(mp3_content)

        def named_bytes_io(content, name):
            buffer = BytesIO(content)
            buffer.name = name
            return buffer

        return named_bytes_io(mp3_content, "temp.mp3")

    raise HTTPException(
        status_code=400, detail="The input resource could not be found!"
    )


def get_analysis(audio_file) -> Dict[str, str]:
    call_log = openai.Audio.translate("whisper-1", audio_file)

    transcript = call_log["text"]

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": """You are a helpful real-estate sales assistant. Based on the transcript log between a human salesperson and a customer, answer the following questions:
        1. Summary of the call
        2. What is the next action item?
        3. What is the customer's sentiment?
        4. How was the performance of the salesperson
        """,
            },
            {"role": "user", "content": f"{transcript}"},
        ],
        functions=functions,
        function_call={"name": "call_analysis"},
    )

    arguments = completion["choices"][0]["message"]["function_call"]["arguments"]
    json_obj = json.loads(arguments)
    return json_obj
