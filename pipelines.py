from starlette.exceptions import HTTPException
from openai.error import (
    Timeout,
    RateLimitError,
    APIError,
    ServiceUnavailableError,
    AuthenticationError,
    APIConnectionError,
    InvalidRequestError,
)

from helper import (
    convert_url,
    get_diarized_output,
    get_ratings,
    get_summary,
    count_tokens,
    get_speaker_labels,
    validate_speaker_count,
)
from config import (
    DEEPGRAM_API_BASE,
    DEEPGRAM_TOKEN,
    AZURE_OPENAI_PARAMS_16K,
    AZURE_OPENAI_PARAMS_4K,
    TOKENS_FACTOR_OF_SAFTEY,
)
from mongodb import collection
from functions import EVALUATE_PARAMETERS, SUMMARIZE_CALL, LABEL_SPEAKERS
from models import (
    DiarizedTranscriptObject,
    SummaryObject,
    UsageObject,
    RatingsObject,
    AudioRequest,
    DetailedAudioResponse,
)
from exceptions import InvalidSpeakerCountException
from enums import HttpStatusCode


def prepare_analysis(audio: AudioRequest) -> DetailedAudioResponse:
    """This pipeline generates an end-to-end AI powered call analysis"""

    mp3 = audio.mp3_url

    mp3_bytes = convert_url(mp3)

    labelling_usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }

    try:
        # Step 1: Get the Diarization & Transcript
        raw_diarization = get_diarized_output(
            mp3_bytes, DEEPGRAM_TOKEN, DEEPGRAM_API_BASE
        )

        if count_tokens(transcript) >= TOKENS_FACTOR_OF_SAFTEY:
            AZURE_OPENAI_PARAMS = AZURE_OPENAI_PARAMS_16K
            model_config = "16k"
        else:
            AZURE_OPENAI_PARAMS = AZURE_OPENAI_PARAMS_4K
            model_config = "4k"

        collection.update_one(
            {"mp3": mp3},
            {
                "$set": {
                    "model_config": model_config,
                }
            },
        )

        try:
            print(AZURE_OPENAI_PARAMS)
            # Step 1.1.1: Validate if there are 2 speakers
            raw_diarization = validate_speaker_count(raw_diarization)

            # Step 1.2.1: Label the un-labelled speakers (Speaker:0 & Speaker:1) as salesperson and customer
            labels, labelling_usage = get_speaker_labels(
                raw_diarization, LABEL_SPEAKERS, AZURE_OPENAI_PARAMS
            )

            # Step 1.3.1: Replace the labels in the raw transcript
            print("Replacing labelled roles")
            transcript = raw_diarization.replace(
                "[Speaker:0]", labels["speaker_0"]
            ).replace("[Speaker:1]", labels["speaker_1"])
            diarizedTranscriptObject = DiarizedTranscriptObject(
                diarized_transcript=transcript
            )
            collection.update_one(
                {"mp3": mp3},
                {
                    "$set": {
                        "transcript": diarizedTranscriptObject.dict(),
                    },
                },
            )

        except InvalidSpeakerCountException:
            print()
            print("\033[31mInvalid Number of speakers found, fixing transcript!\033[0m")
            print()

            # Step 1.1.2: Remove the wrong labels (Single speaker / More than 2 speakers) to avoid a possible confusion to the LLM
            transcript = (
                raw_diarization.replace("[Speaker:0]", "")
                .replace("[Speaker:1]", "")
                .replace("[Speaker:2]", "")
                .replace("[Speaker:3]", "")
            )
            diarizedTranscriptObject = DiarizedTranscriptObject(
                raw_transcript=transcript
            )
            collection.update_one(
                {"mp3": mp3},
                {
                    "$set": {
                        "transcript": diarizedTranscriptObject.dict(),
                    },
                },
            )

        # Step 2: Prepare Summary
        print("Preparing Summary")
        summary, summarizing_usage = get_summary(
            transcript, SUMMARIZE_CALL, AZURE_OPENAI_PARAMS
        )
        summaryObject = SummaryObject(**summary)
        collection.update_one(
            {"mp3": mp3},
            {
                "$set": {
                    "summary": summaryObject.dict(),
                }
            },
        )

        # Step 3: Evaluate Ratings
        ratings, rating_usage = get_ratings(
            transcript, EVALUATE_PARAMETERS, AZURE_OPENAI_PARAMS
        )
        ratingsObject = RatingsObject(**ratings)
        collection.update_one(
            {"mp3": mp3},
            {
                "$set": {
                    "analysis": ratingsObject.dict(),
                }
            },
        )

        # Step 4: Analyze the API Calls' Usage
        print("Preparing Usage")
        usage = {}
        usage["prompt_tokens"] = (
            rating_usage["prompt_tokens"]
            + labelling_usage["prompt_tokens"]
            + summarizing_usage["prompt_tokens"]
        )
        usage["completion_tokens"] = (
            rating_usage["completion_tokens"]
            + labelling_usage["completion_tokens"]
            + summarizing_usage["completion_tokens"]
        )
        usage["total_tokens"] = (
            rating_usage["total_tokens"]
            + labelling_usage["total_tokens"]
            + summarizing_usage["total_tokens"]
        )
        usageObject = UsageObject(**usage)
        collection.update_one(
            {"mp3": mp3},
            {
                "$set": {
                    "gpt35_usage": usageObject.dict(),
                }
            },
        )

        # Step 5: Clubbing all the objects together
        analysis_object = {
            "mp3": mp3,
            "sales_lead_info": audio.sales_lead_info,
            "ratings": ratingsObject,
            "summary": summaryObject,
            "script": diarizedTranscriptObject,
            "token_usage": usageObject,
        }

        return DetailedAudioResponse(**analysis_object)

    except (
        Timeout,
        RateLimitError,
        APIError,
        ServiceUnavailableError,
        AuthenticationError,
        APIConnectionError,
        InvalidRequestError,
    ) as e:
        raise HTTPException(
            status_code=HttpStatusCode.INTERNAL_SERVER_ERROR.value,
            detail=f"Failed to execute pipeline, {e.__class__}!\n{e._message}",
        )
