from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import config
from mutagen import File as MutagenFile


@dataclass
class ValidationResult:
    """Result of validating an audio file before transcription."""

    is_valid: bool
    error: Optional[str]
    duration: Optional[float]
    file_size_mb: Optional[float]


def validate_audio(file_path: str) -> ValidationResult:
    """Validate that an audio file exists, is supported, and fits size limits."""

    path = Path(file_path)

    if not path.exists():
        return _invalid_result("File not found")

    extension = path.suffix.lower()
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
