from prompts import *


ANALYZE = {
    "name": "call_analysis",
    "description": "Shows a detailed analysis of the call.",
    "parameters": {
        "type": "object",
        "properties": {
            "rudeness_or_politeness_metric": {
                "type": "number",
                "description": ratings_rudeness_politeness,
            },
            "salesperson_company_introduction": {
                "type": "number",
                "description": ratings_company_introduction,
            },
            "meeting_request": {
                "type": "number",
                "description": ratings_meeting_request,
            },
            "salesperson_understanding_of_customer_requirements": {
                "type": "number",
                "description": ratings_requirement_understanding,
            },
            "customer_sentiment_by_the_end_of_call": {
                "type": "number",
                "description": ratings_customer_sentiment,
            },
            "customer_eagerness_to_buy": {
                "type": "number",
                "description": ratings_customer_eagerness,
            },
            "customer_budget": {
                "type": "string",
                "description": ratings_customer_budget,
            },
            "customer_preferences": {
                "type": "string",
                "description": ratings_customer_preferences,
            },
        },
    },
}


LABEL_SPEAKERS = {
    "name": "speaker_classifier",
    "description": "Identifies between salesperson and customer",
    "parameters": {
        "type": "object",
        "properties": {
            "speaker_0": {
                "type": "string",
                "enum": ["salesperson: ", "customer: "],
                "description": diarization_speaker_0,
            },
            "speaker_1": {
                "type": "string",
                "enum": ["salesperson: ", "customer: "],
                "description": diarization_speaker_1,
            },
        },
    },
}

SUMMARIZE_CALL = {
    "name": "summarize",
    "description": "Summarizes the conversion and highlights key points.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": summary_title,
            },
            "discussion_points": {
                "type": "string",
                "description": summary_discussion_points,
            },
            "customer_queries": {
                "type": "string",
                "description": summary_customer_queries,
            },
            "next_action_items": {
                "type": "string",
                "description": summary_next_action_items,
            },
            "meeting_request_attempt": {
                "type": "string",
                "description": summary_meeting_request_attempt,
            },
        },
    },
}
