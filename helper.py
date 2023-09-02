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
# openai.api_key = os.getenv("OPENAI_API_KEY")
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
                    "type": "number",
                    "description": """
This parameter measures the rudeness or politeness metric for the salesperson where a rating of 1 means the salesperson was extremely rude on the call and a rating of 5 means the salesperson was extremely polite

Refer to this Rating Scale:
Rating 1:    Extremely Rude: Conversational content displays severe disrespect, offensive language, or explicit rudeness. There is a complete disregard for decorum or consideration.
Rating 2:    Moderately Rude: The conversation contains elements of disrespect or rudeness, but it is not as intense as the previous category. Sarcasm or mild offensive language might be present.
Rating 3:    Neutral or Polite: The conversation is respectful, courteous, and maintains a professional or friendly tone. There is no rudeness or offense detected.
Rating 4:    Moderately Polite: The conversation leans towards a higher level of politeness. It may include courteous language, expressions of consideration, and a friendly tone.
Rating 5:    Extremely Polite: The conversation is exceptionally polite, possibly demonstrating formal language, deferential phrases, and a strong focus on being respectful and considerate.

""",
                },
                "salesperson_company_introduction": {
                    "type": "number",
                    "description": """
Rate the level of introduction and explanation that salesperson gives to the other end about the organization, if they explains where they are from and positive perks about the organization they shouldreceive a higher rating. Consider some pointers written below as the knowledge base and if salesperson recite these words, it should be considered -

Knowledge Base:
'Hi! Am calling from Square Yards'
'Hi! Am calling from Square Yards. Square Yards is India’s largest integrated platform for Real Estate'
'Hi! Am calling from Square Yards. We are operating as largest Real Estate Platform and are here to help you with every possible need related to real estate. I can see that you have enquired about a property or specific locality.'

'Square Yards is India’s largest integrated platform for Real Estate and has a presence in UAE, Rest of Middle East, Australia & Canada. It offers a complete homebuying journey, providing the widest range of inventory from developers at the best prices. Square Yards assists with property search, site visits, home loans, documentation, and post-sales customer service. Notably, there are no brokerage charges for customers. Additional services include home interiors, renting, and property management.'

On the basis of utterance of company introduction, rate this particular parameter on the basis of below written criteria -

Rating 1 - The salesperson just said - 'Hi! Am calling from Square Yards' and moving forward do not
describe anything about the organization and what it stands for, then please provide rating - 1.
Rating 2 - If the salesperson, describes - 'Hi! Am calling from Square Yards. Square Yards is India’s largest
integrated platform for Real Estate', or anything relevant to this, then please rate them as 2.
Rating 3 - If salesperson gave at least a 10-20 words of description about the company and is
enthusiastically making user understand where he/she is from, then rate it 3.Rating 4 - If salesperson utters 'Square Yards' multiple times and explains about the organization on a broader level, telling the customer about the facilities of the company then rate it as 4.
Rating 5 - If the salesperson, describes the company in a very elaborate way as per what is written in the knowledge base and provides a total description of the perks in why should the customer be associated with Square Yards, then give them rating 5.

""",
                },
                "meeting_request": {
                    "type": "number",
                    "description": """
As a moderator, you have to rate the level of attempts and convincing abilities the salesperson uses to convince the customer to approve a meeting request or approve for visiting properties. In order to give a proper rating, here are some guidelines which should be used to judge the salesperson and give them that respective rating -
    Rating 0 – If salesperson did not have any discussion for the meeting and have not pitched this to the very customer. Their was no use of ‘site visit’ or ‘meeting’ in the conversation.
    Rating 1 – If the salesperson asked about the whatsapp number and confirmed the contact details of the customer, but did not had any discussion on the meeting, then rate them as 1.
    Rating 2 – If the salesperson made a clear attempt to push the customer towards meeting or site visit but was not persuasive and agrees to whatsoever the customer says.
    Rating 3 – If the salesperson describes the perks of site visit and pitch the same to the customer with a pro-active approach.
    Rating 4 – If the salesperson, persuade the customer to engage a site visit or meeting to have a look at the properties and describe them the perks of it. Customer might give a yes or no, but judgement has to be on the basis of concerns addressed by the customer.
    Rating 5 – If the customer, agrees to get the site visit done and have a look at the properties, they confirm that they want to visit the property then give 5 as a rating to the salesperson.
                    """,
                },
                "salesperson_understanding_of_customer_requirements": {
                    "type": "number",
                    "description": """
Rate the salesperson's ability to understand customer requirements based on the following criteria, using a scale of 1 to 5, where 1 indicates poor performance and 5 indicates effective performance:

    Awareness of Customer Requirements: How well did the salesperson demonstrate an awareness of the customer's requirements based on their query on the Square Yards website?

    Engagement in Meaningful Conversation: To what extent did the salesperson engage the customer in a meaningful conversation, showing active interest and involvement?

    Grasping Client's Needs and Requirements: How effectively did the salesperson grasp and comprehend the client's needs and requirements during the interaction?

    Market Knowledge and Relevant Options: Did the salesperson exhibit a strong understanding of the market and provide relevant property options that aligned with the customer's needs?

    Active Listening and Appropriate Responses: Evaluate the salesperson's ability to actively listen to the customer's inquiries, understand their concerns, and respond appropriately.

    Please assign a rating from 1 to 5 for each of the criteria mentioned above, where:

        Rating 1: The salesperson's performance was poor in the specified area.
        Rating 2: The salesperson's performance was below average in the specified area.
        Rating 3: The salesperson's performance was satisfactory in the specified area.
        Rating 4: The salesperson's performance was good in the specified area.
        Rating 5: The salesperson's performance was highly effective in the specified area.

                    """,
                },
                "customer_sentiment_by_the_end_of_call": {
                    "type": "number",
                    "description": """
Rate the customer's sentiment by the end of the call based on their satisfaction and likelihood to continue engagement with the salesperson. Use a scale of 1 to 5, where 1 indicates the lowest level of satisfaction or likelihood, and 5 indicates the highest level of satisfaction or likelihood.

    Rating Descriptions:

    Very Dissatisfied & Unlikely to Continue (Rating 1): The customer seems highly dissatisfied with the conversation and shows no interest or intention to further engage with the salesperson. They may have expressed frustration or dissatisfaction with the interaction.

    Dissatisfied & Unlikely to Continue (Rating 2): The customer is dissatisfied with the call and is unlikely to continue engagement with the salesperson. Their tone and demeanor suggest disappointment or lack of interest.

    Neutral (Rating 3): The customer's sentiment is neutral by the end of the call. They neither express strong satisfaction nor dissatisfaction, and their likelihood to continue engagement is uncertain.

    Satisfied & Likely to Continue (Rating 4): The customer appears satisfied with the conversation and is inclined to continue engagement with the salesperson. They may have shown interest in further discussions or future interactions.

    Highly Satisfied & Very Likely to Continue (Rating 5): The customer is highly satisfied with the call and expresses a strong willingness to continue engagement with the salesperson. They may have conveyed enthusiasm, positivity, and eagerness to move forward.

    Please assign a rating from 1 to 5 based on your assessment of the customer's sentiment by the end of the call, considering both their satisfaction level and likelihood to continue engaging with the salesperson.
""",
                },
                "customer_eagerness_to_buy": {
                    "type": "number",
                    "description": """
Evaluate the customer's willingness to buy the property based on their level of enthusiasm and interest, using a scale of 1 to 5, where 1 indicates minimal eagerness and 5 indicates strong eagerness to buy in the near future.

    Rating Descriptions:

    Not Eager to Buy (Rating 1): The customer's tone and expressions suggest a lack of interest or eagerness to make a purchase. They may have expressed doubts, hesitation, or disinterest in proceeding with the property transaction.

    Slightly Interested (Rating 2): The customer exhibits mild interest in buying the property, but their enthusiasm is limited. They may have asked questions or shown some curiosity, but their overall eagerness remains subdued.

    Moderately Interested (Rating 3): The customer displays a moderate level of interest in purchasing the property. They may have inquired about specific details, benefits, or terms, indicating a genuine consideration for the purchase.

    Very Interested (Rating 4): The customer is highly interested in buying the property and expresses enthusiasm about its features, potential benefits, or suitability. They may have mentioned specific reasons for their interest.

    Extremely Eager to Buy (Rating 5): The customer is extremely eager and enthusiastic about buying the property in the near future. They may have shown strong excitement, mentioned intentions of proceeding, or expressed a sense of urgency.

    Please assign a rating from 1 to 5 of the customer's eagerness to buy the property. Consider their tone, expressions, specific statements, and overall enthusiasm when making your evaluation.

""",
                },
                "customer_budget": {
                    "type": "string",
                    "description": """
If the customer mentioned a budget for the property during the conversation, please classify their budget into one of the following buckets based on the phrases the
    customer says to denote their budget:

    Conversation – Budget Bucket
    40 lakhs OR around 40 OR 30 to 40 - Less than 40 lakhs
    around 60 to 70, 60-70 - 40 to 75 lakhs
    around 70 OR 70 to 80 or around 1 Cr - 75 lakhs to 1.25cr
    above 1 OR 1 to 1.25 Cr or Around 2 Cr - 1.25cr to 2cr
    Between 2 Cr to 3 Cr OR 2 to 3 - 2cr to 3cr
    More than 3cr
    Budget not disclosed

    Please carefully consider the customer's explicit statements, if any, about their budget and use your judgment to categorize their budget into the appropriate bucket specifying the bucket name. If the customer did not disclose their budget, "Budget not disclosed." In your classification, ensure that you base your decision solely on the information provided by the customer during the conversation. If the customer's budget falls within a specific range but is not directly mentioned, you can make an informed judgment based on their discussions related to affordability and property
                    """,
                },
                "customer_preferences": {
                    "type": "string",
                    "description": "Analyze the customer's preferences for purchasing a property based on the provided conversation transcript. Specifically, focus on identifying any explicit mentions of preferred locality, project, or builder, as well as details about the type and size of the property.If the customer's preferences are clear and specific, please provide a representation of their preferences. Please carefully review the conversation and extract any relevant information about the customer's preferences. Consider both explicit statements and implied preferences to capture a comprehensive understanding of what the customer is looking for.",
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
