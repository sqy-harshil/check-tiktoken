import os


MONGODB_URI = os.getenv("MONGODB_URI")

CALL_ANALYSIS_API_KEY = os.getenv("CALL_ANALYSIS_API_KEY")

DEEPGRAM_API_BASE = os.getenv("DEEPGRAM_API_BASE")
DEEPGRAM_TOKEN = os.getenv("DEEPGRAM_API_KEY")

AZURE_OPENAI_PARAMS = {
    "engine": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME_GPT_35"),
    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
    "api_base": os.getenv("AZURE_OPENAI_API_BASE"),
    "api_type": os.getenv("AZURE_OPENAI_API_TYPE"),
    "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
}
