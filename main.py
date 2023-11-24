import uvicorn
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from fastapi import FastAPI, HTTPException, Request, Security, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import APIKeyHeader

from config import CALL_ANALYSIS_API_KEY
from models import (
    AudioRequest,
    CallMetadata,
    DetailedAudioResponse,
    UsageObject,
    DiarizedTranscriptObject,
    RatingsObject,
    SummaryObject,
)
from mongodb import collection
from enums import HttpStatusCode
from pipelines import prepare_analysis

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
            raise HTTPException(
                status_code=HttpStatusCode.UNAUTHORIZED.value, detail="Invalid API Key"
            )
    else:
        raise HTTPException(
            status_code=HttpStatusCode.BAD_REQUEST.value,
            detail="Please enter an API key",
        )


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
    print()
    print()
    print("-" * 150)
    print()
    print(f"\033[36mprocessing call: {audio_url.mp3_url}\033[0m")
    print()

    mp3 = audio_url.mp3_url

    try:
        mp3_to_insert = {"mp3": mp3}
        inserted_object = collection.insert_one(mp3_to_insert)
        inserted_object_id = inserted_object.inserted_id

        try:
            processed_analysis = prepare_analysis(audio_url)

            log = {
                "status": "SUCCESS",
                "error_class": "",
                "error_description": "",
            }

            document = {
                "sales_lead_info": audio_url.sales_lead_info.dict(), 
                "timestamp": ObjectId(inserted_object_id).generation_time,
                "logs": log,
            }

        except HTTPException as e:
            log = {
                "status": "FAILED",
                "error_class": str(type(e).__name__),
                "error_description": str(e.detail),
            }
            document = {
                "sales_lead_info": audio_url.sales_lead_info.dict(),
                "timestamp": ObjectId(inserted_object_id).generation_time,
                "logs": log,
            }

        collection.update_one({"_id": inserted_object_id}, {"$set": document})

        print()
        print("\033[36mcall processed!\033[0m")
        print()
        print("-" * 150)
        print()

        return processed_analysis

    except DuplicateKeyError:
        fetched_object = collection.find_one({"mp3": audio_url.mp3_url})

        try:
            sales_lead = fetched_object["sales_lead_info"]
            sales_lead_info = CallMetadata(**sales_lead)
        except KeyError:
            sales_lead_info = None

        try:
            mp3 = fetched_object["mp3"]
        except KeyError:
            mp3 = None

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
            mp3=mp3,
            sales_lead_info=sales_lead_info,
            ratings=ratings,
            script=transcript,
            summary=summary,
            token_usage=token_usage,
        )

        print()
        print("\033[36mcall analysis already exists in the database!\033[0m")
        print()
        print("-" * 150)
        print()
        print()
        print()

        return processed_analysis


if __name__ == "__main__":
    with app:
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
