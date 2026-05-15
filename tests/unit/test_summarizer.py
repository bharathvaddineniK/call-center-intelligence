from src.agents.summarizer import summarize
from src.pipeline_models import SummaryResult


MOCK_TRANSCRIPT = """
Agent: Thank you for calling support, how can I help you?
Caller: My internet is not working since this morning.
Agent: I understand, let me help you troubleshoot that.
""".strip()

VALID_SENTIMENTS = {"positive", "negative", "neutral"}
REQUIRED_TEXT_FIELDS = ("summary", "intent", "sentiment", "agent_behavior")

_cached_result = None


def get_result() -> SummaryResult:
    """Run the summarizer once and reuse the result across tests."""
    global _cached_result

    if _cached_result is None:
        _cached_result = summarize(MOCK_TRANSCRIPT)

    return _cached_result


def test_summarize_returns_summary_result():
    """Return a structured summary result with the expected text fields."""
    result = get_result()

    assert isinstance(result, SummaryResult)
    for field_name in REQUIRED_TEXT_FIELDS:
        assert getattr(result, field_name)

    # key_entities can be empty, but it should still be returned as a list.
    assert isinstance(result.key_entities, list)


def test_summarize_sentiment_values():
    """Return one of the supported sentiment labels."""
    result = get_result()

    assert result.sentiment in VALID_SENTIMENTS
