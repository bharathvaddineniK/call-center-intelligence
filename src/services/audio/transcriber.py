import logging
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import torch

import config
from faster_whisper import WhisperModel
from groq import Groq
from langsmith import traceable

from src.services.audio.cache import compute_hash, get_cached_transcript, save_to_cache
from src.services.audio.cleaner import clean_transcript

logger = logging.getLogger(__name__)

_whisper_model = None


def _get_device() -> tuple[str, str]:
    """Auto-detect best available device and compute type."""
    if torch.cuda.is_available():
        return "cuda", "float16"
    return "cpu", "int8"


def _get_whisper_model() -> WhisperModel:
    """Load the Whisper model once and reuse it."""
    global _whisper_model

    if _whisper_model is None:
        device, compute_type = _get_device()
        _whisper_model = WhisperModel(
            config.FALLBACK_AUDIO_MODEL,
            device=device,
            compute_type=compute_type,
        )
    return _whisper_model


@dataclass
class TranscriptionResult:
    """Normalized transcription output shared by cache, Groq, and Whisper paths."""

    text: str
    segments: list[dict[str, Any]]
    confidence: float
    speaker_count: int
    source: str
    duration: float
    file_hash: str = ""


@traceable
def get_transcription(file_path: str) -> TranscriptionResult:
    """Return a cached transcript, or transcribe with Groq and fall back to Whisper.
    And save the result to cache"""
    file_hash = compute_hash(file_path)
    cached_call = get_cached_transcript(file_hash)

    if cached_call is not None:
        result = _build_cached_result(cached_call)
        result.file_hash = file_hash
        return result

    try:
        result = _transcribe(file_path)
    except Exception as e:
        raise RuntimeError(f"Transcription failed for {file_path}") from e

    result.file_hash = file_hash
    save_to_cache(
        file_hash=file_hash,
        text=result.text, 
        segments=result.segments, 
        confidence=result.confidence, 
        duration=result.duration
    )  
    return result
    

def _transcribe(file_path: str) -> TranscriptionResult:
    """Try Groq primary, then Groq turbo, then local Whisper."""
    try:
        return _transcribe_with_groq(file_path)
    except Exception as e:
        logger.warning(
            "Groq transcription failed, falling back to groq smaller model: %s",
            e,
        )
        try:
            return _transcribe_with_groq_fallback(file_path)
        except Exception as e:
            logger.warning("Groq turbo failed, falling back to Whisper: %s", e)
            return _transcribe_with_whisper(file_path)

def _build_cached_result(cached_call: dict) -> TranscriptionResult:
    """Build a transcription result from a cached database row."""
    return TranscriptionResult(
        text=cached_call["text"],
        segments=cached_call["segments"],
        confidence=cached_call["confidence"],
        duration=cached_call["duration"],
        speaker_count=0,
        source="cache",
    )


def _transcribe_with_groq(file_path: str) -> TranscriptionResult:
    """Transcribe an audio file with Groq's hosted audio model."""
    return _transcribe_with_groq_model(
        file_path=file_path,
        model=config.AUDIO_MODEL,
        source="groq",
    )


def _transcribe_with_groq_fallback(file_path: str) -> TranscriptionResult:
    """Transcribe using the faster Groq fallback model."""
    return _transcribe_with_groq_model(
        file_path=file_path,
        model=config.AUDIO_MODEL_FALLBACK,
        source="groq_turbo",
    )


def _transcribe_with_groq_model(
    file_path: str,
    model: str,
    source: str,
) -> TranscriptionResult:
    """Transcribe an audio file with a specific Groq audio model."""
    response = _create_groq_transcription(file_path, model)
    return TranscriptionResult(
        text=clean_transcript(response.text),
        segments=response.segments,
        confidence=_calculate_confidence(
            (segment["avg_logprob"] for segment in response.segments),
            (segment.get("no_speech_prob", 0) for segment in response.segments),
        ),
        speaker_count=0,
        source=source,
        duration=round(response.duration, 2),
    )


def _create_groq_transcription(file_path: str, model: str):
    """Call Groq's transcription API for one audio file and model."""
    client = Groq(api_key=config.GROQ_API_KEY)

    with open(file_path, "rb") as audio_file:
        return client.audio.transcriptions.create(
            file=(Path(file_path).name, audio_file.read()),
            model=model,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )


def _transcribe_with_whisper(file_path: str) -> TranscriptionResult:
    """Transcribe an audio file locally with Faster Whisper."""

    segments, info = _get_whisper_model().transcribe(
        file_path,
        beam_size=config.BEAM_SIZE,
        vad_filter=True,
        condition_on_previous_text=False,
        word_timestamps=True,
    )

    segment_list = list(segments)
    transcript_segments = [
        {
            "start": segment.start,
            "end": segment.end,
            "text": clean_transcript(segment.text),
            "avg_logprob": segment.avg_logprob,
            "no_speech_prob": segment.no_speech_prob,
        }
        for segment in segment_list
    ]

    return TranscriptionResult(
        text=" ".join(seg["text"] for seg in transcript_segments),
        segments=transcript_segments,
        confidence=_calculate_confidence(
            (segment.avg_logprob for segment in segment_list),
            (segment.no_speech_prob for segment in segment_list),
        ),
        speaker_count=0,
        source="whisper",
        duration=round(info.duration, 2),
    )


def _calculate_confidence(
    avg_logprobs: Iterable[float],
    no_speech_probs: Iterable[float] | None = None,
) -> float:
    """Convert log probability and no-speech probability into a confidence score."""
    logprob_confidence = 1 + statistics.mean(avg_logprobs)

    if no_speech_probs is None:
        return round(logprob_confidence, 4)

    speech_confidence = 1 - statistics.mean(no_speech_probs)
    return round((logprob_confidence + speech_confidence) / 2, 4)
