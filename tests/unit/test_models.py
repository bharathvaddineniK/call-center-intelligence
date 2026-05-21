import pytest
from pydantic import ValidationError

from src.pipeline_models import PipelineState, QAResult, SummaryResult, TranscriptionSegment


def test_pipeline_state():
    """Test that PipelineState can be created only with audio path"""

    state = PipelineState(audio_path="src/path/to/audio")

    assert state["audio_path"] == "src/path/to/audio", "Audio path should be src/path/to/audio"
    assert state.get("file_hash") is None, "File hash should be none"


def test_qa_result():
    """Test that QAResult validates 1-5 rubric scores."""

    qa = QAResult(
        empathy_score=4,
        resolution_score=3,
        compliance_score=5,
        communication_score=4,
        professionalism_score=4,
        overall_score=4,
        compliance_flag=True,
        compliance_severity="medium",
        violation_description="Caller hold disclosure was incomplete",
        timestamp_evidence=["00:42"],
        reasoning="some reasoning",
    )

    assert qa.overall_score == 4

    with pytest.raises(ValidationError):
        QAResult(
            empathy_score=6,
            resolution_score=3,
            compliance_score=5,
            communication_score=4,
            professionalism_score=4,
            overall_score=4,
            compliance_flag=True,
            compliance_severity="medium",
            violation_description="Caller hold disclosure was incomplete",
            timestamp_evidence=["00:42"],
            reasoning="some reasoning",
        )

    with pytest.raises(ValidationError):
        QAResult(
            empathy_score=0,
            resolution_score=3,
            compliance_score=5,
            communication_score=4,
            professionalism_score=4,
            overall_score=4,
            compliance_flag=True,
            compliance_severity="medium",
            violation_description="Caller hold disclosure was incomplete",
            timestamp_evidence=["00:42"],
            reasoning="some reasoning",
        )


def test_qa_result_defaults_provider_prone_fields():
    """Allow LLM providers to omit fields that are normalized downstream."""
    qa = QAResult(
        empathy_score=4,
        resolution_score=4,
        compliance_score=5,
        communication_score=4,
        professionalism_score=5,
    )

    assert qa.overall_score == 0.0
    assert qa.compliance_flag is False
    assert qa.compliance_severity == "none"
    assert qa.violation_description == "No violation detected"
    assert qa.timestamp_evidence == []
    assert qa.reasoning == ""


def test_qa_result_normalizes_provider_variants():
    """Normalize common structured-output differences across LLM providers."""
    qa = QAResult(
        empathy_score=4,
        resolution_score=4,
        compliance_score=2,
        communication_score=4,
        professionalism_score=4,
        compliance_flag=True,
        compliance_severity="CRITICAL",
        violation_description="",
        timestamp_evidence="02:15",
    )

    assert qa.compliance_severity == "critical"
    assert qa.violation_description == "Compliance issue detected"
    assert qa.timestamp_evidence == ["02:15"]


def test_summary_result_normalizes_provider_variants():
    """Normalize common structured-output differences across LLM providers."""
    summary = SummaryResult(
        summary="Caller was rescued.",
        sentiment="Neutral",
        agent_behavior="Helpful",
        key_entities="Elizabeth",
        call_purpose="Emergency assistance",
        key_discussion_points="Vehicle in water",
        action_items="Dispatch emergency services",
        resolution_status="Resolved",
        sentiment_trajectory="Frustrated -> Relieved",
    )

    assert summary.sentiment == "neutral"
    assert summary.key_entities == ["Elizabeth"]
    assert summary.key_discussion_points == ["Vehicle in water"]
    assert summary.action_items == ["Dispatch emergency services"]
    assert summary.resolution_status == "resolved"


def test_summary_result_requires_core_fields_without_strict_enums():
    """Require summary fields while allowing provider casing variants."""
    with pytest.raises(ValidationError):
        SummaryResult()

    schema = SummaryResult.model_json_schema()

    assert "resolution_status" in schema["required"]
    assert "enum" not in schema["properties"]["resolution_status"]


def test_transcription_segment():
    """Test that TranscriptionSegment accepts a valid segment"""
    segment = TranscriptionSegment(
        start=0.0, end=5.2, text="911 what is your emergency", speaker="SPEAKER_00", confidence=0.95
    )
    assert segment.text == "911 what is your emergency"
    assert segment.speaker == "SPEAKER_00"
