from src.services.audio.diarization import (
    SPEAKER_00,
    SPEAKER_01,
    _detect_speaker_change,
    assign_speakers,
)


def _segment(start: float, end: float, text: str) -> dict:
    """Build a transcript segment for diarization tests."""

    return {"start": start, "end": end, "text": text}


def test_assign_speakers_empty():
    """Return an empty segment list unchanged."""

    result = assign_speakers([])

    assert result == []


def test_first_speaker_is_agent():
    """Assign the first segment to SPEAKER_00."""

    segments = [
        _segment(0.0, 3.0, "Hello 911 what is your emergency"),
        _segment(3.5, 6.0, "I need help"),
    ]

    result = assign_speakers(segments)

    assert result[0]["speaker"] == SPEAKER_00


def test_speaker_changes_on_gap():
    """Switch speakers when adjacent segments have a long pause."""

    segments = [
        _segment(0.0, 3.0, "Hello 911 what is your emergency"),
        _segment(3.6, 6.0, "I need help"),
    ]

    result = assign_speakers(segments)

    assert result[1]["speaker"] == SPEAKER_01


def test_speaker_changes_after_question():
    """Switch speakers when the previous segment ends with a question."""

    previous = _segment(0.0, 3.0, "What is your emergency?")
    current = _segment(3.1, 6.0, "I need help")

    assert _detect_speaker_change(previous, current) is True


def test_speaker_does_not_change_for_short_pause_and_statement():
    """Keep the same speaker when there is no change cue."""

    previous = _segment(0.0, 3.0, "I can help with that")
    current = _segment(3.2, 6.0, "Please continue")

    assert _detect_speaker_change(previous, current) is False
