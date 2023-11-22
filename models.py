from typing import Optional
from pydantic import BaseModel


class AudioRequest(BaseModel):
    mp3_url: Optional[str]


class RatingsObject(BaseModel):
    rudeness_or_politeness_metric: Optional[int]
    salesperson_company_introduction: Optional[int]
    meeting_request: Optional[int]
    salesperson_understanding_of_customer_requirements: Optional[int]
    customer_sentiment_by_the_end_of_call: Optional[int]
    customer_eagerness_to_buy: Optional[int]
    customer_budget: Optional[str]
    customer_preferences: Optional[str]


class SummaryObject(BaseModel):
    title: Optional[str]
    discussion_points: Optional[str]
    customer_queries: Optional[str]
    meeting_request_attempt: Optional[str]
    next_action_items: Optional[str]


class UsageObject(BaseModel):
    prompt_tokens: Optional[int]
    completion_tokens: Optional[int]
    total_tokens: Optional[int]


class DiarizedTranscriptObject(BaseModel):
    diarized_transcript: Optional[str]


class DetailedAudioResponse(BaseModel):
    mp3: Optional[AudioRequest]
    ratings: Optional[RatingsObject] 
    summary: Optional[SummaryObject] 
    script: Optional[DiarizedTranscriptObject] 
    token_usage: Optional[UsageObject] 
