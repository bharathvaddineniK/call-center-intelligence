import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT")

LLM_MODEL = "gpt-4o"
AUDIO_MODEL = "whisper-large-v3"
FALLBACK_AUDIO_MODEL = "large-v2"
BEAM_SIZE = 5
MAX_AUDIO_DURATION = 300 # seconds
MAX_FILE_SIZE = 15 # MB
CONFIDENCE_THRESHOLD = 0.7 # avg_logprob scale 0-1

BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "data" / "audio"
REPORTS_DIR = BASE_DIR / "data" / "reports"
CACHE_DIR = BASE_DIR /  "data" / "cache"
DATABASE_PATH = BASE_DIR / "data" / "call_center.db"

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "call-center-intelligence")

# security

SUPPORTED_AUDIO_FORMATS = [".mp3", ".wav", ".m4a", ".ogg"]
PII_ENTITIES = ["PHONE_NUMBER", "EMAIL_ADDRESS", "US_SSN", "CREDIT_CARD"]