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


def test_agent_opening_pattern_sets_first_speaker():
    """Recognize support-style greetings as agent openings."""

    segments = [
        _segment(
            0.0,
            3.0,
            "Thank you for calling Technical Support. This is Alex, how may I help?",
        ),
        _segment(3.4, 6.0, "I am having trouble with my account."),
    ]

    result = assign_speakers(segments)

    assert result[0]["speaker"] == SPEAKER_00
    assert result[1]["speaker"] == SPEAKER_01


def test_customer_opening_still_sets_first_speaker():
    """Keep caller-style first turns labeled as customer."""

    segments = [
        _segment(0.0, 2.0, "I am calling because I need help with my account."),
        _segment(2.4, 4.0, "How may I help you?"),
    ]

    result = assign_speakers(segments)

    assert result[0]["speaker"] == SPEAKER_01
    assert result[1]["speaker"] == SPEAKER_00


def test_customer_intent_beats_weak_agent_question_cue():
    """Avoid labeling a customer request as agent just because it says can you."""

    segments = [
        _segment(0.0, 2.0, "911, what are you reporting?"),
        _segment(2.2, 5.0, "I need help, can you send someone right away?"),
    ]

    result = assign_speakers(segments)

    assert result[1]["speaker"] == SPEAKER_01


def test_weak_single_cue_does_not_override_current_speaker():
    """Require stronger evidence before overriding the current speaker."""

    segments = [
        _segment(0.0, 2.0, "I am calling because my account is locked."),
        _segment(2.1, 4.0, "Can you see the error message on the screen"),
    ]

    result = assign_speakers(segments)

    assert result[0]["speaker"] == SPEAKER_01
    assert result[1]["speaker"] == SPEAKER_01


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


def test_agent_cue_overrides_alternation():
    """Keep agent labels for adjacent operator-style questions."""

    segments = [
        _segment(0.0, 2.0, "911, what are you reporting?"),
        _segment(2.1, 4.0, "That's right, how may I help you?"),
    ]

    result = assign_speakers(segments)

    assert result[1]["speaker"] == SPEAKER_00


def test_customer_cue_overrides_first_speaker_default():
    """Label caller-style statements as customer even after agent questions."""

    segments = [
        _segment(0.0, 2.0, "911, what are you reporting?"),
        _segment(2.1, 4.0, "I would like for a police officer to give me a call."),
    ]

    result = assign_speakers(segments)

    assert result[1]["speaker"] == SPEAKER_01
