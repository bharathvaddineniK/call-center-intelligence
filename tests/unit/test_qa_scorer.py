import pytest

from src.agents.qa_scorer import score
from src.pipeline_models import QAResult, SummaryResult

pytestmark = pytest.mark.integration

MOCK_TRANSCRIPT = """
Agent: Thank you for calling support, how can I help you?
Caller: My internet is not working since this morning.
Agent: I understand. Let me help you troubleshoot that now.
Caller: Thank you, I appreciate it.
""".strip()

MOCK_SUMMARY = SummaryResult(
    summary="Customer called about internet outage.",
    call_purpose="Report internet outage",
    sentiment="negative",
    agent_behavior="Helpful and calm",
    key_entities=["internet", "outage"],
    key_discussion_points=["Internet not working", "Troubleshooting steps"],
    action_items=["Agent to escalate to technical team"],
    resolution_status="unresolved",
    sentiment_trajectory="Frustrated → Calm"
)

SCORE_FIELDS = (
    "empathy_score",
    "resolution_score",
    "compliance_score",
    "communication_score",
    "professionalism_score",
    "overall_score",
)
MAX_REASONABLE_SCORE_DELTA = 10

_cached_result = None
_cached_repeat_result = None


def get_result() -> QAResult:
    """Run the QA scorer once and reuse the result across tests."""
    global _cached_result

    if _cached_result is None:
        _cached_result = score(MOCK_TRANSCRIPT, MOCK_SUMMARY)

    return _cached_result


def get_repeat_result() -> QAResult:
    """Run the QA scorer a second time for consistency checks."""
    global _cached_repeat_result

    if _cached_repeat_result is None:
        _cached_repeat_result = score(MOCK_TRANSCRIPT, MOCK_SUMMARY)

    return _cached_repeat_result


def assert_valid_score(value: float) -> None:
    """Assert that a QA score is inside the supported 0-100 range."""
    assert 0 <= value <= 100


def test_score_returns_qa_result():
    """Return a structured QA result with all expected score fields."""
    result = get_result()

    assert isinstance(result, QAResult)
    for field_name in SCORE_FIELDS:
        assert_valid_score(getattr(result, field_name))

    assert isinstance(result.compliance_flag, bool)
    assert result.reasoning


def test_overall_score_is_deterministic():
    """Keep repeated overall scores within a reasonable tolerance."""
    first_result = get_result()
    second_result = get_repeat_result()

    score_delta = abs(first_result.overall_score - second_result.overall_score)

    assert score_delta <= MAX_REASONABLE_SCORE_DELTA
