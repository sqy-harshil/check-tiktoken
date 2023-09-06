import os
from typing import Dict, Union

import uvicorn
import pymongo
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from fastapi import FastAPI, HTTPException, Request, Security, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import APIKeyHeader

from models import AudioRequest, SimpleAudioResponse, DetailedAudioResponse
from helper import get_analysis_4, get_analysis_8, convert_url


MONGODB_URI = os.getenv("MONGODB_URI")
client = pymongo.MongoClient(MONGODB_URI)
db = client.get_default_database()

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
    simple_analysis = db["simple_analysis"]

    try:
        mp3_to_insert = {"mp3": audio_url.mp3_url}
        inserted_object = simple_analysis.insert_one(mp3_to_insert)
        inserted_object_id = inserted_object.inserted_id

        processed_analysis = get_analysis_4(convert_url(audio_url.mp3_url))

        analysis = processed_analysis.json_object
        script = processed_analysis.script

        document = {
            "timestamp": ObjectId(inserted_object_id).generation_time,
            "analysis": analysis,
            "transcript": script,
        }

        simple_analysis.update_one({"_id": inserted_object_id}, {"$set": document})

    except DuplicateKeyError:
        existing_object = simple_analysis.find_one({"mp3": audio_url.mp3_url})
        analysis = existing_object["analysis"]

    return analysis


@app.post(
    "/get_detailed_call_analysis",
    tags=["Call Analysis"],
    response_model=DetailedAudioResponse,
    description="Get a call analysis of an audio input on 8 parameters (This is currently in prototyping phase)",
    name="Echo-Octa-Sensai (Beta)",
)
def process(
    audio_url: AudioRequest, api_key: str = Depends(get_api_key)
) -> Dict[str, Union[int, str]]:
    detailed_analysis = db["detailed_analysis"]

    try:
        mp3_to_insert = {"mp3": audio_url.mp3_url}
        inserted_object = detailed_analysis.insert_one(mp3_to_insert)
        inserted_object_id = inserted_object.inserted_id

        processed_analysis = get_analysis_8(convert_url(audio_url.mp3_url))

        analysis = processed_analysis.json_object
        script = processed_analysis.script

        document = {
            "timestamp": ObjectId(inserted_object_id).generation_time,
            "analysis": analysis,
            "transcript": script,
        }

        detailed_analysis.update_one({"_id": inserted_object_id}, {"$set": document})

    except DuplicateKeyError:
        existing_object = detailed_analysis.find_one({"mp3": audio_url.mp3_url})
        analysis = existing_object["analysis"]

    return analysis


if __name__ == "__main__":
    with app:
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
