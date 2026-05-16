from src.services.audio.cleaner import clean_transcript


def test_removes_blank_audio_tag():
    """Remove blank audio tags from transcripts."""
    text = "Hello [BLANK_AUDIO] I can hear you now."

    assert clean_transcript(text) == "Hello I can hear you now."


def test_removes_bracketed_non_speech_labels():
    """Remove common bracketed non-speech labels."""
    text = "[MUSIC] Hello [NOISE] thanks for calling [LAUGHTER]"

    assert clean_transcript(text) == "Hello thanks for calling"


def test_collapses_repeated_consecutive_words():
    """Collapse repeated consecutive words into one occurrence."""
    text = "Hello hello hello, how can I help?"

    assert clean_transcript(text) == "Hello how can I help?"


def test_collapses_repeated_consecutive_phrases():
    """Collapse repeated consecutive short phrases into one occurrence."""
    text = "I can help I can help with that today."

    assert clean_transcript(text) == "I can help with that today."


def test_removes_youtube_style_footers():
    """Remove common YouTube footer phrases from transcripts."""
    text = "That resolves your issue. Subscribe to our channel. Like and share."

    assert clean_transcript(text) == "That resolves your issue."


def test_clean_transcript_preserves_normal_text():
    """Leave normal transcript text unchanged."""
    text = "Agent: Thank you for calling. Caller: I need help with billing."

    assert clean_transcript(text) == text
