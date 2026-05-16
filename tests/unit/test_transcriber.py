from src.services.audio.transcriber import get_transcription, _calculate_confidence, TranscriptionResult

def test_transcription_groq():
    """Test that the test file transcribes through a supported source."""

    result = get_transcription('data/audio/call_114.mp3')
    assert result.source in {'groq', 'groq_turbo', 'cache'}
    assert isinstance(result, TranscriptionResult)
    assert len(result.text) > 0
    assert len(result.segments) > 0
    assert 0 <= result.confidence <= 1
    assert result.duration > 0

def test_calculate_confidence():
    """Test that confidence score is normalized properly"""
    # avg_logprob of -0.5 should normalize to 0.5
    result = _calculate_confidence([-0.5, -0.5, -0.5])
    assert result == 0.5

def test_calculate_confidence_uses_no_speech_probability():
    """Test that no_speech_prob reduces confidence when provided."""
    result = _calculate_confidence(
        avg_logprobs=[-0.2, -0.2],
        no_speech_probs=[0.4, 0.4],
    )

    assert result == 0.7
