import os

OPENAI_API_PARAMS = {
    "api_key": os.getenv("OPENAI_API_KEY"),
    "api_base": os.getenv("OPENAI_API_BASE"),
    "api_type": os.getenv("OPENAI_API_TYPE"),
    "api_version": os.getenv("OPENAI_API_VERSION"),
}

AZURE_OPENAI_PARAMS = {
    "engine": os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
    "api_base": os.getenv("AZURE_OPENAI_API_BASE"),
    "api_type": os.getenv("AZURE_OPENAI_API_TYPE"),
    "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
}

MONGODB_URI = os.getenv("MONGODB_URI_DEV")
CALL_ANALYSIS_API_KEY = os.getenv("CALL_ANALYSIS_API_KEY")
