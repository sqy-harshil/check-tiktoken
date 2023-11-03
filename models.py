from typing import Union
from pydantic import BaseModel


class AudioRequest(BaseModel):
    mp3_url: str


class RatingsObject(BaseModel):
    rudeness_or_politeness_metric: int
    salesperson_company_introduction: int
    meeting_request: int
    salesperson_understanding_of_customer_requirements: int
    customer_sentiment_by_the_end_of_call: int
    customer_eagerness_to_buy: int
    customer_budget: str
    customer_preferences: str


class SummaryObject(BaseModel):
    title: str
    discussion_points: str
    customer_queries: str
    next_action_items: str


class UsageObject(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class DiarizedTranscriptObject(BaseModel):
    diarized_transcript: str


class DetailedAudioResponse(BaseModel):
    ratings: Union[RatingsObject, None] 
    summary: Union[SummaryObject, None] 
    script: Union[DiarizedTranscriptObject, None] 
    token_usage: Union[UsageObject, None] 
