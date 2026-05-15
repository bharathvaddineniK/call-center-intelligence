"""Factory for creating chat LLM clients from the configured provider."""

import config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI


SUPPORTED_PROVIDERS = ("openai", "groq", "gemini")


def _get_provider() -> str:
    """Return the configured provider in a normalized form."""
    return config.LLM_PROVIDER.lower().strip()


def _build_openai_llm(temperature: float):
    """Create an OpenAI chat model client."""
    return ChatOpenAI(
        api_key=config.OPENAI_API_KEY,
        model=config.OPENAI_MODEL,
        temperature=temperature,
    )


def _build_groq_llm(temperature: float):
    """Create a Groq chat model client."""
    return ChatGroq(
        api_key=config.GROQ_API_KEY,
        model=config.GROQ_LLM_MODEL,
        temperature=temperature,
    )


def _build_gemini_llm(temperature: float):
    """Create a Gemini chat model client."""
    return ChatGoogleGenerativeAI(
        google_api_key=config.GEMINI_API_KEY,
        model=config.GEMINI_MODEL,
        temperature=temperature,
    )


def get_llm(temperature: float = 0):
    """Create an LLM client for the provider configured in config.LLM_PROVIDER."""
    provider = _get_provider()

    if provider == "openai":
        return _build_openai_llm(temperature)

    if provider == "groq":
        return _build_groq_llm(temperature)

    if provider == "gemini":
        return _build_gemini_llm(temperature)

    supported = ", ".join(SUPPORTED_PROVIDERS)
    raise ValueError(f"Unsupported LLM provider '{provider}'. Use one of: {supported}.")

def get_fallback_llm(temperature: float = 0) -> ChatGroq:
    """Return Groq as the fallback LLM when the primary provider fails."""
    return _build_groq_llm(temperature)
