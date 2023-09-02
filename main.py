import os
from typing import Dict
from datetime import datetime, timedelta

import uvicorn
import pymongo
from fastapi import FastAPI, HTTPException, Request, Security, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import APIKeyHeader

from models import AudioRequest, SimpleAudioResponse, DetailedAudioResponse
from helper import get_analysis_4, get_analysis_8, convert_url


MONGODB_URI = os.getenv("MONGODB_URI")
client = pymongo.MongoClient(MONGODB_URI)

db = client["sqy-call-analysis"]

app = FastAPI(
    title="EchoSensai",
    description="An advanced AI-powered call analysis API designed to provide comprehensive insights and intelligent recommendations for your conversations.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Call Analysis", "description": "Endpoints for call analysis"},
    ],
)

templates = Jinja2Templates(directory="templates")

key = os.getenv("CALL_ANALYSIS_API_KEY")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header:
        if api_key_header == key:
            return key
        else:
            raise HTTPException(status_code=401, detail="Invalid API Key")
    else:
        raise HTTPException(status_code=400, detail="Please enter an API key")


@app.get("/", tags=["Index"], response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post(
    "/get_simple_call_analysis",
    tags=["Call Analysis"],
    response_model=SimpleAudioResponse,
    description="Get a call analysis of an audio input on 4 parameters",
    name="Echo-Quad-Sensai",
)
async def process(
    audio_url: AudioRequest, api_key: str = Depends(get_api_key)
) -> Dict[str, str]:
    analysis = get_analysis_4(convert_url(audio_url.mp3_url))

    simple_analysis = db["simple_analysis"]

    current_utc_timestamp = datetime.utcnow()
    ist_offset = timedelta(hours=5, minutes=30)
    current_ist_timestamp = current_utc_timestamp + ist_offset

    obj = {
        "timestamp": current_ist_timestamp,
        "mp3": audio_url.mp3_url,
        "analysis": analysis.json_object,
        "transcript": analysis.script,
    }
    simple_analysis.insert_one(obj)

    return analysis.json_object


@app.post(
    "/get_detailed_call_analysis",
    tags=["Call Analysis"],
    response_model=DetailedAudioResponse,
    description="Get a call analysis of an audio input on 8 parameters (This is currently in prototyping phase)",
    name="Echo-Octa-Sensai (Beta)",
)
def process(
    audio_url: AudioRequest, api_key: str = Depends(get_api_key)
) -> Dict[str, str]:
    analysis = get_analysis_8(convert_url(audio_url.mp3_url))

    detailed_analysis = db["detailed_analysis"]

    current_utc_timestamp = datetime.utcnow()
    ist_offset = timedelta(hours=5, minutes=30)
    current_ist_timestamp = current_utc_timestamp + ist_offset

    obj = {
        "timestamp": current_ist_timestamp,
        "mp3": audio_url.mp3_url,
        "analysis": analysis.json_object,
        "transcript": analysis.script,
    }
    detailed_analysis.insert_one(obj)

    return analysis.json_object


if __name__ == "__main__":
    with app:
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
