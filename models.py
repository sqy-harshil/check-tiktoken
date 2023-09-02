from pydantic import BaseModel


class AudioRequest(BaseModel):
    mp3_url: str


class SimpleAudioResponse(BaseModel):
    call_summary: str
    next_action_item: str
    customer_sentiment: str
    salesperson_performance: str


class DetailedAudioResponse(BaseModel):
    rudeness_or_politeness_metric: int
    salesperson_company_introduction: int
    meeting_request: int
    salesperson_understanding_of_customer_requirements: int
    customer_sentiment_by_the_end_of_call: int
    customer_eagerness_to_buy: int
    customer_budget: str
    customer_preferences: str
