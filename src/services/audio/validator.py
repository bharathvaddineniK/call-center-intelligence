from dataclasses import dataclass
from pathlib import Path

from mutagen import File as MutagenFile

import config


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
        return _invalid_result("Unsupported audio format")

    size = path.stat().st_size / (1024 * 1024)
    audio = MutagenFile(path)
    duration = audio.info.length

    is_valid = size <= config.MAX_FILE_SIZE and duration <= config.MAX_AUDIO_DURATION
    error = None

    if size > config.MAX_FILE_SIZE:
        error = "File exceeded maximum supported size"
    elif duration > config.MAX_AUDIO_DURATION:
        error = "File exceeded maximum supported duration"

    return ValidationResult(
        is_valid=is_valid,
        error=error,
        duration=duration,
        file_size_mb=size,
    )


def _invalid_result(error: str) -> ValidationResult:
    """Build a failed validation result when metadata is unavailable."""

    return ValidationResult(
        is_valid=False,
        error=error,
        duration=None,
        file_size_mb=None,
    )
