import re

SPEAKER_00 = "Agent"
SPEAKER_01 = "Customer"
SPEAKER_CHANGE_PAUSE_SECONDS = 0.5
STRONG_ROLE_SCORE = 3
ROLE_SCORE_MARGIN = 2
AGENT_OPENING_PATTERNS = (
    r"\bthank\s+you\s+for\s+calling\b",
    r"\bthanks\s+for\s+calling\b",
    r"\b(?:good\s+morning|good\s+afternoon|good\s+evening),?\s+.*\bhow\s+may\s+i\s+help\b",
    r"\b(?:this\s+is|you(?:'re| are)\s+speaking\s+with)\s+[a-z]+",
    r"\b(?:technical\s+support|customer\s+support|support\s+desk|help\s+desk)\b",
    r"\b911\b.*\b(?:what|where|do|are|can|is)\b",
)
CUSTOMER_OPENING_PATTERNS = (
    r"\bi\s+(?:am\s+)?calling\s+(?:because|about|to)\b",
    r"\bi\s+(?:need|want|would\s+like)\b",
    r"\bmy\s+(?:account|order|service|phone|internet|bill)\b",
    r"\bwe\s+(?:need|have|are|were)\b",
)
AGENT_CUES = (
    ("911,", STRONG_ROLE_SCORE),
    ("what are you reporting", STRONG_ROLE_SCORE),
    ("what is your emergency", STRONG_ROLE_SCORE),
    ("how may i help", STRONG_ROLE_SCORE),
    ("how can i help", STRONG_ROLE_SCORE),
    ("where are you", STRONG_ROLE_SCORE),
    ("what is the address", STRONG_ROLE_SCORE),
    ("stay on the line", STRONG_ROLE_SCORE),
    ("i can help", 2),
    ("i'm going to", 2),
    ("can you", 1),
    ("do you", 1),
    ("are you", 1),
)
CUSTOMER_CUES = (
    ("i called", STRONG_ROLE_SCORE),
    ("i need", STRONG_ROLE_SCORE),
    ("i would like", STRONG_ROLE_SCORE),
    ("i just", 2),
    ("i have", 2),
    ("i'm calling", STRONG_ROLE_SCORE),
    ("my ", 1),
    ("me ", 1),
    ("we ", 1),
    ("our ", 1),
)


def assign_speakers(segments: list[dict]) -> list[dict]:
    """Assign likely speaker labels to transcript segments using text and timing cues."""

    if not segments:
        return segments

    current_speaker = _infer_initial_speaker(segments[0].get("text", "")) or SPEAKER_00
    segments[0]["speaker"] = current_speaker

    for i, segment in enumerate(segments[1:], start=1):
        inferred_speaker = _infer_speaker_from_text(segment.get("text", ""))
        if inferred_speaker is not None:
            current_speaker = inferred_speaker
        elif _detect_speaker_change(segments[i - 1], segment):
            current_speaker = _next_speaker(current_speaker)

        segments[i]["speaker"] = current_speaker

    return segments


def _infer_initial_speaker(text: str) -> str | None:
    """Infer the first speaker from common call-center opening phrases."""
    normalized = text.lower().strip()
    if any(re.search(pattern, normalized) for pattern in AGENT_OPENING_PATTERNS):
        return SPEAKER_00
    if any(re.search(pattern, normalized) for pattern in CUSTOMER_OPENING_PATTERNS):
        return SPEAKER_01
    return _infer_speaker_from_text(text)


def _infer_speaker_from_text(text: str) -> str | None:
    """Infer speaker role from call-center and emergency-call phrasing."""
    normalized = f" {text.lower().strip()} "
    agent_score = _score_cues(normalized, AGENT_CUES)
    customer_score = _score_cues(normalized, CUSTOMER_CUES)

    if agent_score >= STRONG_ROLE_SCORE and agent_score >= customer_score + ROLE_SCORE_MARGIN:
        return SPEAKER_00
    if (
        customer_score >= STRONG_ROLE_SCORE
        and customer_score >= agent_score + ROLE_SCORE_MARGIN
    ):
        return SPEAKER_01
    return None


def _score_cues(text: str, cues: tuple[tuple[str, int], ...]) -> int:
    """Return a weighted score for role-specific text cues."""
    return sum(weight for cue, weight in cues if cue in text)


def _detect_speaker_change(prev: dict, curr: dict) -> bool:
    """Detect a likely speaker change between two adjacent segments."""

    if curr["start"] - prev["end"] > SPEAKER_CHANGE_PAUSE_SECONDS:
        return True

    if prev["text"].strip().endswith("?"):
        return True

    return False


def _next_speaker(current_speaker: str) -> str:
    """Return the alternate speaker label for two-speaker diarization."""

    return SPEAKER_00 if current_speaker == SPEAKER_01 else SPEAKER_01
