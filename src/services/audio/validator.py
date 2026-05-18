import wave
from dataclasses import dataclass
from pathlib import Path

from mutagen import File as MutagenFile

import config

SUPPORTED_FORMATS_DISPLAY = "WAV, MP3, FLAC, M4A"


@dataclass
class ValidationResult:
    """Result of validating an audio file before transcription."""

    is_valid: bool
    error: str | None
    duration: float | None
    file_size_mb: float | None


def _detect_format_by_magic_bytes(file_path: Path) -> str | None:
    """Detect audio format from file header bytes."""
    with open(file_path, "rb") as f:
        header = f.read(12)

    if header.startswith(b"ID3") or header.startswith(b"\xFF\xFB"):
        return ".mp3"

    if header.startswith(b"RIFF"):
        return ".wav"

    if header.startswith(b"fLaC"):
        return ".flac"

    if header[4:8] == b"ftyp":
        return ".m4a"

    return None


def validate_audio(file_path: str) -> ValidationResult:
    """Validate that an audio file exists, is supported, and fits size limits."""

    path = Path(file_path)

    if not path.exists():
        return _invalid_result("File not found")

    extension = _detect_format_by_magic_bytes(path)
    if extension not in config.SUPPORTED_AUDIO_FORMATS:
        return _invalid_result(
            f"Unsupported audio format. Supported formats: {SUPPORTED_FORMATS_DISPLAY}."
        )

    size = path.stat().st_size / (1024 * 1024)
    duration = _get_audio_duration(path, extension)

    if extension == ".wav" and duration > config.MAX_AUDIO_DURATION:
        return ValidationResult(
            is_valid=False,
            error=_duration_error(),
            duration=duration,
            file_size_mb=size,
        )

    is_valid = size <= config.MAX_FILE_SIZE and duration <= config.MAX_AUDIO_DURATION
    error = None

    if size > config.MAX_FILE_SIZE:
        error = _size_error()
    elif duration > config.MAX_AUDIO_DURATION:
        error = _duration_error()

    return ValidationResult(
        is_valid=is_valid,
        error=error,
        duration=duration,
        file_size_mb=size,
    )


def _get_audio_duration(path: Path, extension: str) -> float:
    """Return audio duration, using the RIFF header first for WAV files."""
    if extension == ".wav":
        return _get_wav_duration_from_header(path)

    audio = MutagenFile(path)
    return audio.info.length


def _get_wav_duration_from_header(path: Path) -> float:
    """Read WAV duration from the RIFF header without scanning the whole file."""
    with wave.open(str(path), "rb") as wav_file:
        frame_rate = wav_file.getframerate()
        if frame_rate <= 0:
            return 0
        return wav_file.getnframes() / frame_rate


def _size_error() -> str:
    """Return a size-limit error with the configured limit."""
    return f"File exceeded maximum supported size of {config.MAX_FILE_SIZE:g} MB"


def _duration_error() -> str:
    """Return a duration-limit error with the configured limit."""
    max_minutes = config.MAX_AUDIO_DURATION / 60
    return f"File exceeded maximum supported duration of {max_minutes:g} minutes"


def _invalid_result(error: str) -> ValidationResult:
    """Build a failed validation result when metadata is unavailable."""

    return ValidationResult(
        is_valid=False,
        error=error,
        duration=None,
        file_size_mb=None,
    )
