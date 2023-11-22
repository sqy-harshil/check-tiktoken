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
    get_speaker_labels,
)
from config import DEEPGRAM_API_BASE, DEEPGRAM_TOKEN
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
    mp3: str = audio.mp3_url

    mp3_bytes = convert_url(mp3)

    try:
        # Step 1: Prepare Diarization & store it in the Database
        raw_diarization = get_diarized_output(mp3_bytes, DEEPGRAM_TOKEN, DEEPGRAM_API_BASE)            


        # Step 2: Determine the speakers (Salesperson & Customer) & store it in the Database
        labels, labelling_usage = get_speaker_labels(raw_diarization, LABEL_SPEAKERS)


        # Step 3: Replace the actual speaker roles in the raw transcript & store it in the Database
        print("Replacing labelled roles")
        diarized_transcript = raw_diarization.replace("[Speaker:0]", labels["speaker_0"]).replace("[Speaker:1]", labels["speaker_1"])
        diarizedTranscriptObject = DiarizedTranscriptObject(
            diarized_transcript=diarized_transcript
        )
        collection.update_one(
            {"mp3": mp3},
            {
                "$set": {
                    "transcript": diarizedTranscriptObject.dict(),
                },
            },
        )


        # Step 4: Prepare Summary & store it in the Database
        print("Preparing Summary")
        summary, summarizing_usage = get_summary(diarized_transcript, SUMMARIZE_CALL)
        summaryObject = SummaryObject(
            title=summary["title"],
            discussion_points=summary["discussion_points"],
            customer_queries=summary["customer_queries"],
            meeting_request_attempt=summary["meeting_request_attempt"],
            next_action_items=summary["next_action_items"],
        )
        collection.update_one(
            {"mp3": mp3},
            {
                "$set": {
                    "summary": summaryObject.dict()
                }
            },
        )


        # Step 5: Prepare Ratings & store it in the Database
        ratings, rating_usage = get_ratings(diarized_transcript, EVALUATE_PARAMETERS)
        ratingsObject = RatingsObject(
            customer_budget=ratings["customer_budget"],
            customer_eagerness_to_buy=ratings["customer_eagerness_to_buy"],
            customer_preferences=ratings["customer_preferences"],
            customer_sentiment_by_the_end_of_call=ratings["customer_sentiment_by_the_end_of_call"],
            meeting_request=ratings["meeting_request"],
            rudeness_or_politeness_metric=ratings["rudeness_or_politeness_metric"],
            salesperson_company_introduction=ratings["salesperson_company_introduction"],
            salesperson_understanding_of_customer_requirements=ratings["salesperson_understanding_of_customer_requirements"],
        )
        collection.update_one(
            {"mp3": mp3},
            {
                "$set": {
                    "analysis": ratingsObject.dict(),
                }
            },
        )


        # Step 6: Prepare the Usage Object & store it in the Database
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
        usageObject = UsageObject(
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            total_tokens=usage["total_tokens"],
        )
        collection.update_one(
            {"mp3": mp3},
            {
                "$set": {
                    "gpt35_usage": usageObject.dict()
                }
            },
        )


        # Step 7: Clubbing everything together
        analysis_object = {
            "mp3": audio,
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
