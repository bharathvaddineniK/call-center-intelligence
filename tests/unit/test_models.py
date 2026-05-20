import pytest
from pydantic import ValidationError

from src.pipeline_models import PipelineState, QAResult, TranscriptionSegment


def test_pipeline_state():
    """Test that PipelineState can be created only with audio path"""

    state = PipelineState(
        audio_path="src/path/to/audio"
    )

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
    
def test_transcription_segment():
    """Test that TranscriptionSegment accepts a valid segment"""
    segment = TranscriptionSegment(
        start=0.0,
        end=5.2,
        text="911 what is your emergency",
        speaker="SPEAKER_00",
        confidence=0.95
    )
    assert segment.text == "911 what is your emergency"
    assert segment.speaker == "SPEAKER_00"
