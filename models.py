from pydantic import BaseModel


class AudioRequest(BaseModel):
    mp3_url: str


class SimpleAudioResponse(BaseModel):
    call_summary: str
    next_action_item: str
    customer_sentiment: str
    salesperson_performance: str


class DetailedAudioResponse(BaseModel):
    rudeness_or_politeness_metric: str
    salesperson_company_introduction: str
    meeting_request: str
    salesperson_understanding_of_customer_requirements: str
    customer_sentiment_by_the_end_of_call: str
    customer_eagerness_to_buy: str
    customer_budget: str
    customer_preferences: str
