"""Clean transcription artifacts from raw speech-to-text output."""

import re


BRACKETED_ARTIFACTS = {
    "applause",
    "background noise",
    "beep",
    "blank audio",
    "blank_audio",
    "crosstalk",
    "inaudible",
    "laugh",
    "laughing",
    "laughter",
    "chuckle",
    "chuckles",
    "music",
    "noise",
    "pause",
    "ringing",
    "silence",
    "sound",
    "static",
}

YOUTUBE_FOOTER_PATTERNS = (
    r"\bsubscribe\s+to\s+(our|my|the)\s+channel\b[.!?]*",
    r"\blike\s+and\s+share\b[.!?]*",
    r"\blike,\s*share,?\s+and\s+subscribe\b[.!?]*",
    r"\bdon'?t\s+forget\s+to\s+subscribe\b[.!?]*",
    r"\bplease\s+like\s+and\s+subscribe\b[.!?]*",
    r"\bhit\s+the\s+bell\s+icon\b[.!?]*",
)

MAX_REPEATED_PHRASE_WORDS = 6


def clean_transcript(text: str) -> str:
    """Remove common transcription artifacts from transcript text."""
    if text is None:
        return None

    cleaned_text = _remove_bracketed_artifacts(text)
    cleaned_text = _remove_youtube_footers(cleaned_text)
    cleaned_text = _remove_repeated_phrases(cleaned_text)

    return _normalize_whitespace(cleaned_text)


def _remove_bracketed_artifacts(text: str) -> str:
    """Remove bracketed non-speech labels such as [MUSIC] or [BLANK_AUDIO]."""
    return re.sub(r"\[([^\]]+)\]", _replace_bracketed_artifact, text)


def _replace_bracketed_artifact(match: re.Match) -> str:
    """Return an empty string for known bracketed audio artifacts."""
    label = _normalize_artifact_label(match.group(1))

    if label in BRACKETED_ARTIFACTS:
        return " "

    return match.group(0)


def _normalize_artifact_label(label: str) -> str:
    """Normalize a bracket label for artifact matching."""
    return re.sub(r"[\s_-]+", " ", label.strip().lower())


def _remove_youtube_footers(text: str) -> str:
    """Remove common YouTube call-to-action footer phrases."""
    cleaned_text = text

    for pattern in YOUTUBE_FOOTER_PATTERNS:
        cleaned_text = re.sub(pattern, " ", cleaned_text, flags=re.IGNORECASE)

    return cleaned_text


def _remove_repeated_phrases(text: str) -> str:
    """Collapse consecutive repeated words or short phrases."""
    words = text.split()
    collapsed_words = []
    index = 0

    while index < len(words):
        phrase_length = _find_repeated_phrase_length(words, index)
        phrase = words[index : index + phrase_length]

        collapsed_words.extend(phrase)
        index = _skip_repeated_phrases(words, index, phrase_length)

    return " ".join(collapsed_words)


def _find_repeated_phrase_length(words: list[str], start_index: int) -> int:
    """Find the longest repeated phrase starting at the given word index."""
    max_phrase_length = min(MAX_REPEATED_PHRASE_WORDS, (len(words) - start_index) // 2)

    for phrase_length in range(max_phrase_length, 0, -1):
        first_phrase = words[start_index : start_index + phrase_length]
        next_phrase = words[start_index + phrase_length : start_index + phrase_length * 2]

        if _phrases_match(first_phrase, next_phrase):
            return phrase_length

    return 1


def _skip_repeated_phrases(words: list[str], start_index: int, phrase_length: int) -> int:
    """Move past all repeats of the phrase that starts at start_index."""
    phrase = words[start_index : start_index + phrase_length]
    next_index = start_index + phrase_length

    while _phrases_match(phrase, words[next_index : next_index + phrase_length]):
        next_index += phrase_length

    return next_index


def _phrases_match(first_phrase: list[str], second_phrase: list[str]) -> bool:
    """Compare two phrases while ignoring case and surrounding punctuation."""
    if len(first_phrase) != len(second_phrase):
        return False

    return [
        _normalize_repeated_word(word) for word in first_phrase
    ] == [
        _normalize_repeated_word(word) for word in second_phrase
    ]


def _normalize_repeated_word(word: str) -> str:
    """Normalize a word before checking for repeated phrase artifacts."""
    return word.strip(".,!?;:\"'()[]{}").lower()


def _normalize_whitespace(text: str) -> str:
    """Collapse extra whitespace introduced during transcript cleaning."""
    return re.sub(r"\s+", " ", text).strip()
