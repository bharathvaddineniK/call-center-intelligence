SPEAKER_00 = "SPEAKER_00"
SPEAKER_01 = "SPEAKER_01"
SPEAKER_CHANGE_PAUSE_SECONDS = 0.5


def assign_speakers(segments: list[dict]) -> list[dict]:
    """Assign alternating speaker labels to transcript segments using simple cues."""

    if not segments:
        return segments

    current_speaker = SPEAKER_00
    segments[0]["speaker"] = current_speaker

    for i, segment in enumerate(segments[1:], start=1):
        if _detect_speaker_change(segments[i - 1], segment):
            current_speaker = _next_speaker(current_speaker)

        segments[i]["speaker"] = current_speaker

    return segments


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
