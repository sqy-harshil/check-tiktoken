from pydantic import BaseModel


class AudioRequest(BaseModel):
    mp3_url: str


class AudioResponse(BaseModel):
    call_summary: str
    next_action_item: str
    customer_sentiment: str
    salesperson_performance: str
