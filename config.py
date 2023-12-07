import os


MONGODB_URI = os.getenv("MONGO_URI")

CALL_ANALYSIS_API_KEY = os.getenv("CALL_ANALYSIS_API_KEY")

DEEPGRAM_API_BASE = os.getenv("DEEPGRAM_API_BASE")
DEEPGRAM_TOKEN = os.getenv("DEEPGRAM_API_KEY")

AZURE_OPENAI_PARAMS_4K = {
    "engine": os.getenv("AZURE_DEPLOYMENT_NAME_4K"),
    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
    "api_base": os.getenv("AZURE_OPENAI_API_BASE"),
    "api_type": os.getenv("AZURE_OPENAI_API_TYPE"),
    "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
}

AZURE_OPENAI_PARAMS_16K = {
    "engine": os.getenv("AZURE_DEPLOYMENT_NAME_16K"),
    "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
    "api_base": os.getenv("AZURE_OPENAI_API_BASE"),
    "api_type": os.getenv("AZURE_OPENAI_API_TYPE"),
    "api_version": os.getenv("AZURE_OPENAI_API_VERSION"),
}

TOKENS_FACTOR_OF_SAFTEY = 3000
TIKTOKEN_MODEL_NAME = "gpt-3.5-turbo"
SEED = 123
