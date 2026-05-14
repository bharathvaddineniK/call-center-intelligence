import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import logging

import config
from faster_whisper import WhisperModel
from groq import Groq
from langsmith import traceable

from src.audio.cache import compute_hash, get_cached_transcript

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionResult:
    """Normalized transcription output shared by cache, Groq, and Whisper paths."""

    text: str
    segments: list[dict[str, Any]]
    confidence: float
    speaker_count: int
    source: str
    duration: float

@traceable
def get_transcription(file_path: str) -> TranscriptionResult:
    """Return a cached transcript, or transcribe with Groq and fall back to Whisper."""
    file_hash = compute_hash(file_path)
    cached_call = get_cached_transcript(file_hash)

    if cached_call is not None:
        return TranscriptionResult(
            text=cached_call["text"],
            segments=cached_call["segments"],
            confidence=cached_call["confidence"],
            duration=cached_call["duration"],
            speaker_count=0,
            source="cache",
        )

    try:
        return _transcribe_with_groq(file_path)
    except Exception as e:
        logger.warning("Groq transcription failed, falling back to Whisper: %s", e)
        return _transcribe_with_whisper(file_path)


def _transcribe_with_groq(file_path: str) -> TranscriptionResult:
    """Transcribe an audio file with Groq's hosted audio model."""

    client = Groq(api_key=config.GROQ_API_KEY)

    with open(file_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            file=(Path(file_path).name, audio_file.read()),
            model=config.AUDIO_MODEL,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )

    return TranscriptionResult(
        text=response.text,
        segments=response.segments,
        confidence=_calculate_confidence(
            segment["avg_logprob"] for segment in response.segments
        ),
        speaker_count=0,
        source="groq",
        duration=round(response.duration, 2),
    )


def _transcribe_with_whisper(file_path: str) -> TranscriptionResult:
    """Transcribe an audio file locally with Faster Whisper."""

    model = WhisperModel(config.FALLBACK_AUDIO_MODEL, compute_type="int8")
    segments, info = model.transcribe(
        file_path,
        beam_size=config.BEAM_SIZE,
        vad_filter=True,
    )

    segment_list = list(segments)
    transcript_segments = [
        {
            "start": segment.start,
            "end": segment.end,
            "text": segment.text,
            "avg_logprob": segment.avg_logprob,
        }
        for segment in segment_list
    ]

    return TranscriptionResult(
        text=" ".join(segment.text for segment in segment_list),
        segments=transcript_segments,
        confidence=_calculate_confidence(
            segment.avg_logprob for segment in segment_list
        ),
        speaker_count=0,
        source="whisper",
        duration=round(info.duration, 2),
    )


def _calculate_confidence(avg_logprobs: Iterable[float]) -> float:
    """Convert segment log probabilities into a rounded confidence score."""

    return round(1 + statistics.mean(avg_logprobs), 4)
