import openai
import json
import os
import validators
import requests
from io import BytesIO
from typing import Union

from fastapi import HTTPException

from named_tuples import AnalysisJSON

openai.api_base = "https://api.openai.com/v1"
openai.api_key = os.getenv("SQY_API_KEY")
openai.api_type = "open_ai"
openai.api_version = "2020-10-01"


functions_4 = [
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
                    "description": "Detailed analysis of the next action item? (In Detail)",
                },
                "customer_sentiment": {
                    "type": "string",
                    "description": "Detailed analysis of the customer's sentiment? (In Detail)",
                },
                "salesperson_performance": {
                    "type": "string",
                    "description": "Detailed analysis of the performance of the salesperson? ",
                },
            },
        },
    }
]
functions_8 = [
    {
        "name": "call_analysis",
        "description": "Shows a detailed analysis of the call.",
        "parameters": {
            "type": "object",
            "properties": {
                "rudeness_or_politeness_metric": {
                    "type": "string",
                    "description": "This parameter can be measured on a scale of 1-5, where 1 represents extreme rudeness and 5 represents high politeness for the salesperson.",
                },
                "salesperson_company_introduction": {
                    "type": "string",
                    "description": "This parameter can be measured on a scale of 1-5, indicating how well the salesperson introduced Square Yards. Square Yards is India’s largest integrated platform for Real Estate and has presence in UAE, Rest of Middle East, Australia & Canada. It offers complete homebuying journey providing widest range of inventory from developers at the best price and takes care of property search, site visits, home loans, documentation & post sales customer service. It doesn’t charge any brokerage from the customers. It also offers a wide range of home related services like home interiors, renting & property management. A higher score represents a more effective introduction explaining why customer should use Square Yards’ services for his/her home search ",
                },
                "meeting_request": {
                    "type": "string",
                    "description": """
                        Rate how persuasive the salesperson was in requesting a meeting or site visit with the customer on a scale of 1 to 5. If the conversation didn't take place and no meeting request was made, please assign a rating of 1 (hardly tried). If the salesperson was very persuasive without being pushy in requesting a meeting, assign a rating of 5 (very persuasive). Use the following scale:
                                1: Hardly tried (Conversation didn't take place)
                                2: Tried, but not persuasive
                                3: Moderately persuasive
                                4: Quite persuasive
                                5: Very persuasive without being pushy
                    """,
                },
                "salesperson_understanding_of_customer_requirements": {
                    "type": "string",
                    "description": """

                        This parameters rates salesperson's ability on a scale of 1 to 5 to achieve the following:
                        • Is aware of the customer requirement basis his query on the Square Yards website
                        • engages the customer into a meaningful conversation
                        • ability to grasp the client's needs and requirements
                        • market knowledge to provide relevant options
                        • actively listen, understand, and respond appropriately 
                        1 means poor performance on the above parameters and 5 means an effective performance.
                    """,
                },
                "customer_sentiment_by_the_end_of_call": {
                    "type": "string",
                    "description": "By the end of the call, on a scale of 1-5, how satisfied does the customer seem after the conversation with the salesperson and how likely he is to continue the engagement with salesperson",
                },
                "customer_eagerness_to_buy": {
                    "type": "string",
                    "description": "Assess the customer's willingness to buy the property on a scale of 1-5, where 1 represents the customer not being eager to buy, and 5 signifies the customer being eager to buy in near future. Consider the customer's tone, enthusiasm, and specific statements or expressions of interest to determine their level of willingness to make a purchase.",
                },
                "customer_budget": {
                    "type": "string",
                    "description": """
                        Determine the customer's budget for the property from the following buckets:
                        • Less than 40 lakhs
                        • 40 to 75 lakhs
                        • 75 lakhs to 1.25cr
                        • 1.25cr to 2cr
                        • 2cr to 3cr
                        • More than 3cr
                        • Budget not disclosed
                        Look for any explicit statements made by the customer carefully regarding their budget, as well as any hints or clues about their financial capacity. TIt's crucial to be diligent and meticulous in this task. Avoid making assumptions or misclassifications, and always base your decision on concrete information provided in the transcript. Remember, accuracy is paramount, and your thorough analysis will ensure the best possible assistance to the customer. Example: 1cr: 75 lakhs to 1.25cr, within 1cr: 40 to 75 lakhs
                    """,
                },
                "customer_preferences": {
                    "type": "string",
                    "description": "Identify and understand the customer's specific locality or project or developer preferences for purchasing a property. Look for any explicit mentions of preferred project name, developer name, neighborhood, region, or proximity to certain landmarks such as proximity to, workplace, transportation hub, recreational area. Additionally, consider any implicit cues or contextual information that might hint at the customer's preference.",
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


def get_analysis_4(audio_file) -> AnalysisJSON:
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
4. How was the performance of the salesperson?""",
            },
            {"role": "user", "content": f"{transcript}"},
        ],
        functions=functions_4,
        function_call={"name": "call_analysis"},
    )

    arguments = completion["choices"][0]["message"]["function_call"]["arguments"]
    usage = completion["usage"]
    json_object = json.loads(arguments)
    return AnalysisJSON(
        json_object=json_object, token_usage=usage.to_dict(), script=str(transcript)
    )


def get_analysis_8(audio_file) -> AnalysisJSON:
    call_log = openai.Audio.translate("whisper-1", audio_file)

    transcript = call_log["text"]

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": f"{transcript}"},
            {
                "role": "system",
                "content": """
                    You are a helpful real-estate sales assistant. Based on the transcript log between a human salesperson and a customer, analyze the following parameters:
                        1. rudeness_or_politeness_metric
                        2. salesperson_company_introduction
                        3. meeting_request
                        4. salesperson_understanding_of_customer_requirements
                        5. customer_sentiment_by_the_end_of_call
                        6. customer_eagerness_to_buy
                        7. customer_budget
                        8. customer_preferences
                """,
            },
        ],
        functions=functions_8,
        function_call={"name": "call_analysis"},
    )
    arguments = completion["choices"][0]["message"]["function_call"]["arguments"]
    usage = completion["usage"]
    json_object = json.loads(arguments)
    return AnalysisJSON(
        json_object=json_object, token_usage=usage.to_dict(), script=str(transcript)
    )
