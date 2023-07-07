from pydantic import BaseModel

class AudioRequest(BaseModel):
    mp3_url: str