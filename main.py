import json

import uvicorn
import pymongo
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from fastapi import FastAPI, HTTPException, Request, Security, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import APIKeyHeader

from config import MONGODB_URI, CALL_ANALYSIS_API_KEY
from models import (
    AudioRequest,
    DetailedAudioResponse,
    UsageObject,
    DiarizedTranscriptObject,
    RatingsObject,
    SummaryObject,
)
from enums import HttpStatusCode
from helper import get_analysis_8, convert_url


client = pymongo.MongoClient(MONGODB_URI)
db = client.get_default_database()

app = FastAPI(
    title="EchoSensai",
    description="An advanced AI-powered call analysis API designed to provide comprehensive insights and intelligent recommendations for your conversations.",
    version="1.3.2",
    openapi_tags=[
        {"name": "Call Analysis", "description": "Endpoints for call analysis"},
    ],
)

templates = Jinja2Templates(directory="templates")


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header:
        if api_key_header == CALL_ANALYSIS_API_KEY:
            return CALL_ANALYSIS_API_KEY
        else:
            raise HTTPException(status_code=HttpStatusCode.UNAUTHORIZED.value, detail="Invalid API Key")
    else:
        raise HTTPException(status_code=HttpStatusCode.BAD_REQUEST.value, detail="Please enter an API key")


@app.get("/", tags=["Index"], response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post(
    "/get_detailed_call_analysis",
    tags=["Call Analysis"],
    response_model=DetailedAudioResponse,
    description="Get a call analysis of an audio input on 8 parameters.",
    name="Echo-Octa-Sensai",
)
def process(
    audio_url: AudioRequest, api_key: str = Depends(get_api_key)
) -> DetailedAudioResponse:
    detailed_analysis = db["detailed_analysis"]
    mp3 = ""
    ratings = ""
    summary = ""
    token_usage = ""
    script = ""

    try:
        mp3_to_insert = {"mp3": audio_url.mp3_url}
        inserted_object = detailed_analysis.insert_one(mp3_to_insert)
        inserted_object_id = inserted_object.inserted_id

        try:
            processed_analysis = get_analysis_8(convert_url(audio_url.mp3_url))

            processed_analysis.mp3 = audio_url

            ratings = json.loads(processed_analysis.ratings.json())
            summary = json.loads(processed_analysis.summary.json())
            script = json.loads(processed_analysis.script.json())
            token_usage = json.loads(processed_analysis.token_usage.json())

            log = {
                "status": "SUCCESS",
                "error_class": "",
                "error_description": "",
            }

            document = {
                "timestamp": ObjectId(inserted_object_id).generation_time,
                "analysis": ratings,
                "transcript": script,
                "summary": summary,
                "gpt35_usage": token_usage,
                "logs": log,
            }

        except HTTPException as e:
            log = {
                "status": "FAILED",
                "error_class": str(type(e).__name__),
                "error_description": str(e.detail),
            }

            document = {
                "timestamp": ObjectId(inserted_object_id).generation_time,
                "analysis": ratings,
                "transcript": script,
                "summary": summary,
                "gpt35_usage": token_usage,
                "logs": log,
            }

        detailed_analysis.update_one({"_id": inserted_object_id}, {"$set": document})

    except DuplicateKeyError:
        fetched_object = detailed_analysis.find_one({"mp3": audio_url.mp3_url})

        try:
            audio = fetched_object["mp3"]
            audio_url = AudioRequest(mp3_url=audio)
        except KeyError:
            audio_url = None

        try:
            mongodb_ratings = fetched_object["analysis"]
            ratings = RatingsObject(**mongodb_ratings)
        except KeyError:
            ratings = None

        try:
            mongodb_transcript = fetched_object["transcript"]
            transcript = DiarizedTranscriptObject(**mongodb_transcript)
        except KeyError:
            transcript = None

        try:
            mongodb_summary = fetched_object["summary"]
            summary = SummaryObject(**mongodb_summary)
        except KeyError:
            summary = None

        try:
            mongodb_token_usage = fetched_object["gpt35_usage"]
            token_usage = UsageObject(**mongodb_token_usage)
        except KeyError:
            token_usage = None

        processed_analysis = DetailedAudioResponse(
            mp3=audio_url,
            ratings=ratings,
            script=transcript,
            summary=summary,
            token_usage=token_usage,
        )

    return processed_analysis


if __name__ == "__main__":
    with app:
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
