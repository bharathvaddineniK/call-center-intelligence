import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

def _env(name: str, default: str | None = None) -> str | None:
    """Read env vars defensively so accidental quotes/spaces do not become IDs."""
    value = os.getenv(name, default)
    if value is None:
        return None
    return value.strip().strip("\"'")


LLM_PROVIDER = _env("LLM_PROVIDER", "openai")  # openai, gemini, groq
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = _env("LANGSMITH_PROJECT")
LANGSMITH_PROJECT_URL = os.getenv(
    "LANGSMITH_PROJECT_URL",
    "https://smith.langchain.com/o/34705563-e589-4622-92b2-c70cf7707476/projects/p/e4543352-646b-4097-a796-f9041aca6c44",
)
HF_TOKEN = os.getenv("HF_TOKEN")

OPENAI_MODEL = _env("OPENAI_MODEL", "gpt-4o")
GROQ_LLM_MODEL = _env("GROQ_LLM_MODEL", "llama-3.3-70b-versatile")
GEMINI_MODEL = _env("GEMINI_MODEL", "gemini-2.0-flash")
AUDIO_MODEL_FALLBACK = _env("AUDIO_MODEL_FALLBACK", "whisper-large-v3-turbo")
AUDIO_MODEL = "whisper-large-v3"
FALLBACK_AUDIO_MODEL = "large-v2"
BEAM_SIZE = 1
MAX_AUDIO_DURATION = 3600 # seconds
MAX_FILE_SIZE = 50 # MB
CONFIDENCE_THRESHOLD = 0.7 # avg_logprob scale 0-1
MIN_CONFIDENCE_THRESHOLD = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", "0.4"))
MAX_AUDIO_AGE_HOURS = int(os.getenv("MAX_AUDIO_AGE_HOURS", "24"))

BASE_DIR = Path(__file__).parent
AUDIO_DIR = BASE_DIR / "data" / "audio"
REPORTS_DIR = BASE_DIR / "data" / "reports"
CACHE_DIR = BASE_DIR /  "data" / "cache"
DATABASE_PATH = BASE_DIR / "data" / "call_center.db"

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "call-center-intelligence")

# security

SUPPORTED_AUDIO_FORMATS = {".mp3", ".wav", ".m4a", ".flac"}
PII_ENTITIES = ["PHONE_NUMBER", "EMAIL_ADDRESS", "US_SSN", "CREDIT_CARD"]
