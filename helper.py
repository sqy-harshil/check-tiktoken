import openai, json, os, requests
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
                    "description": "Summary of the call.",
                },
                "next_action_item": {
                    "type": "string",
                    "description": "Detailed analysis of the next action item? (In Detail)",
                },
                "customer_sentiment": {
                    "type": "string",
                    "description": "Detailed analysis of the customer's sentiment? (In Detail)",
                },
                "performance_of_the_salesperson": {
                    "type": "string",
                    "description": "Detailed analysis of the performance of the salesperson? ",
                },
            },
        },
    }
]


def convert_url(url: str) -> Union[BytesIO, None]:
    response = requests.get(url)

    if response.status_code == 200:
        mp3_content = response.content
        buffer = BytesIO(mp3_content)

        def named_bytes_io(content, name):
            buffer = BytesIO(content)
            buffer.name = name
            return buffer

        return named_bytes_io(mp3_content, "temp.mp3")

    return None


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
        4. How was the performance of the salesperson""",
            },
            {"role": "user", "content": f"{transcript}"},
        ],
        functions=functions,
        function_call={"name": functions[0]["name"]},
    )

    arguments = completion["choices"][0]["message"]["function_call"]["arguments"]
    json_obj = json.loads(arguments)
    return json_obj