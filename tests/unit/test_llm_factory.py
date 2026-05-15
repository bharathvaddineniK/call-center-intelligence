import pytest
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

import config
from src.agents.llm_factory import get_llm


def test_openai_provider_returns_chat_openai():
    """Return a ChatOpenAI client when OpenAI is configured."""
    original_provider = config.LLM_PROVIDER

    try:
        config.LLM_PROVIDER = "openai"
        result = get_llm()

        assert isinstance(result, ChatOpenAI)
    finally:
        config.LLM_PROVIDER = original_provider


def test_groq_provider_returns_chat_groq():
    """Return a ChatGroq client when Groq is configured."""
    original_provider = config.LLM_PROVIDER

    try:
        config.LLM_PROVIDER = "groq"
        result = get_llm()

        assert isinstance(result, ChatGroq)
    finally:
        config.LLM_PROVIDER = original_provider


def test_invalid_provider_raises():
    """Raise ValueError when an unsupported provider is configured."""
    original_provider = config.LLM_PROVIDER

    try:
        config.LLM_PROVIDER = "invalid"

        with pytest.raises(ValueError):
            get_llm()
    finally:
        config.LLM_PROVIDER = original_provider
