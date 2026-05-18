SPEAKER_00 = "Agent"
SPEAKER_01 = "Customer"
SPEAKER_CHANGE_PAUSE_SECONDS = 0.5
AGENT_CUES = (
    "911,",
    "what are you reporting",
    "what is your emergency",
    "how may i help",
    "how can i help",
    "where are you",
    "what is the address",
    "can you",
    "do you",
    "are you",
    "stay on the line",
    "i can help",
    "i'm going to",
)
CUSTOMER_CUES = (
    "i called",
    "i need",
    "i would like",
    "i just",
    "i have",
    "my ",
    "me ",
    "we ",
    "our ",
    "i'm calling",
)


def assign_speakers(segments: list[dict]) -> list[dict]:
    """Assign likely speaker labels to transcript segments using text and timing cues."""

    if not segments:
        return segments

    current_speaker = _infer_speaker_from_text(segments[0].get("text", "")) or SPEAKER_00
    segments[0]["speaker"] = current_speaker

    for i, segment in enumerate(segments[1:], start=1):
        inferred_speaker = _infer_speaker_from_text(segment.get("text", ""))
        if inferred_speaker is not None:
            current_speaker = inferred_speaker
        elif _detect_speaker_change(segments[i - 1], segment):
            current_speaker = _next_speaker(current_speaker)

        segments[i]["speaker"] = current_speaker

    return segments


def _infer_speaker_from_text(text: str) -> str | None:
    """Infer speaker role from call-center and emergency-call phrasing."""
    normalized = f" {text.lower().strip()} "
    if any(cue in normalized for cue in AGENT_CUES):
        return SPEAKER_00
    if any(cue in normalized for cue in CUSTOMER_CUES):
        return SPEAKER_01
    return None


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
