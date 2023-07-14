import os
import uvicorn
from fastapi import FastAPI, Security, HTTPException, Depends
from fastapi.security import APIKeyHeader, APIKeyQuery
from typing import Dict
from models import AudioRequest, AudioResponse
from helper import get_analysis, convert_url
from starlette.responses import HTMLResponse


app = FastAPI(
    title="EchoSensai",
    description="An advanced AI-powered call analysis API designed to provide comprehensive insights and intelligent recommendations for your conversations.",
    version="1.0.0",
    openapi_tags=[
        {"name": "Call Analysis", "description": "Endpoints for call analysis"},
    ],
)


def get_api_key(
    api_key_header: str = Security(APIKeyHeader(name="Call Analysis API Key")),
    api_key_query: str = Security(APIKeyQuery(name="Call Analysis API Key")),
):
    key = os.getenv("CALL_ANALYSIS_API_KEY")
    if api_key_header == key or api_key_query == key:
        return key
    raise HTTPException(status_code=401, detail="Invalid API Key")


@app.get("/", tags=["Index"])
def index():
    html_content = """
    <html>
        <head>
            <style>
                body {
                    background-color: black;
                    color: white;
                    font-family: Verdana, sans-serif;
                    overflow: hidden
                }
                .center {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    text-align: center;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="center">
                <h1>EchoSensai: An API Endpoint for AI-Powered Call Analysis</h1>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@app.post("/get_call_analysis", tags=["Call Analysis"], response_model=AudioResponse)
async def process(
    audio_url: AudioRequest, api_key: str = Depends(get_api_key)
) -> Dict[str, str]:
    print(f"Using audio file at: {audio_url.mp3_url}")
    analysis = await get_analysis(convert_url(audio_url.mp3_url))
    return analysis


if __name__ == "__main__":
    with app:
        uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
