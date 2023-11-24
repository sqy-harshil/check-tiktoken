from typing import Optional
from pydantic import BaseModel


class CallMetadata(BaseModel):
    lead_id: int
    salesperson_name: str


class AudioRequest(BaseModel):
    mp3_url: str
    sales_lead_info: CallMetadata


class RatingsObject(BaseModel):
    rudeness_or_politeness_metric: Optional[int] = None
    salesperson_company_introduction: Optional[int] = None
    meeting_request: Optional[int] = None
    salesperson_convincing_abilities: Optional[int] = None
    salesperson_understanding_of_customer_requirements: Optional[int] = None
    customer_sentiment_by_the_end_of_call: Optional[int] = None
    customer_eagerness_to_buy: Optional[int] = None
    customer_budget: Optional[str] = None
    customer_preferences: Optional[str] = None


class SummaryObject(BaseModel):
    title: Optional[str] = None
    discussion_points: Optional[str] = None
    customer_queries: Optional[str] = None
    meeting_request_attempt: Optional[str] = None
    next_action_items: Optional[str] = None


class UsageObject(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class DiarizedTranscriptObject(BaseModel):
    diarized_transcript: Optional[str] = None
    raw_transcript: Optional[str] = None


class DetailedAudioResponse(BaseModel):
    mp3: str = None
    sales_lead_info: Optional[CallMetadata] = None
    ratings: Optional[RatingsObject] = None
    summary: Optional[SummaryObject] = None
    script: Optional[DiarizedTranscriptObject] = None
    token_usage: Optional[UsageObject] = None
