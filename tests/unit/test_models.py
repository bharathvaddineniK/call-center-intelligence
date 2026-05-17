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
    """Test that QAResult raises a validation error if a score is outside 0-100"""

    qa = QAResult(
        empathy_score=25,
        resolution_score=24,
        compliance_score=99,
        communication_score=75,
        professionalism_score=44.5,
        overall_score=55,
        compliance_flag=True,
        reasoning="some reasoning"
    )

    assert qa.overall_score == 55   

    with pytest.raises(ValidationError):
         QAResult(
            empathy_score=101,
            resolution_score=24,
            compliance_score=99,
            communication_score=75,
            professionalism_score=44.5,
            overall_score=55,
            compliance_flag=True,
            reasoning="some reasoning"
        )
    
    with pytest.raises(ValidationError):
         QAResult(
            empathy_score=-7,
            resolution_score=24,
            compliance_score=99,
            communication_score=75,
            professionalism_score=44.5,
            overall_score=55,
            compliance_flag=True,
            reasoning="some reasoning"
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
