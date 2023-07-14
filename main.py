import os
from typing import Dict, Union

import uvicorn
from validators import url as validate_url
from fastapi import FastAPI, HTTPException, Request, Security, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import APIKeyHeader

from models import AudioRequest, AudioResponse
from helper import get_analysis, convert_url

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

api_key_header = APIKeyHeader(name="Call Analysis API Key", auto_error=False)


async def get_api_key(
    api_key_header: str = Security(api_key_header),
) -> Union[str, HTTPException]:
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


@app.post("/get_call_analysis", tags=["Call Analysis"], response_model=AudioResponse)
def process(
    audio_url: AudioRequest, api_key: str = Depends(get_api_key)
) -> Dict[str, str]:
    if not validate_url(audio_url.mp3_url):
        raise HTTPException(status_code=400, detail="Invalid audio URL")

    analysis = get_analysis(convert_url(audio_url.mp3_url))
    return analysis


if __name__ == "__main__":
    with app:
        uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
