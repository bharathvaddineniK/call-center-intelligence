import os
import struct
import tempfile

import config
from src.services.audio.validator import validate_audio


def test_valid_file():
    """Test that a valid file returns valid result"""
    result = validate_audio("data/audio/call_114.mp3")
    assert result.is_valid is True
    assert result.error is None
    assert result.duration > 0
    assert result.file_size_mb > 0


def test_unsupported_format():
    """Test that unsupported file format returns is valid false"""
    with tempfile.NamedTemporaryFile(suffix=".abc", delete=False) as f:
        f.write(b"fake audio")
        temp_path = f.name

    result = validate_audio(temp_path)
    os.unlink(temp_path)
    assert result.is_valid is False
    assert result.error == "Unsupported audio format. Supported formats: WAV, MP3, FLAC, M4A."


def test_non_existent_file():
    """Test that non existent file returns is valid false"""
    result = validate_audio("fake/path.wav")
    assert result.is_valid is False
    assert result.error == "File not found"


def test_large_file():
    """Test that large file returns is valide false"""
    original = config.MAX_FILE_SIZE
    try:
        config.MAX_FILE_SIZE = 0.001
        result = validate_audio("data/audio/call_114.mp3")
    finally:
        config.MAX_FILE_SIZE = original
    assert result.is_valid is False
    assert result.error == "File exceeded maximum supported size of 0.001 MB"


def test_wav_duration_is_checked_before_size():
    """Return duration errors before size errors for oversized WAV headers."""
    temp_path = _write_wav_header(duration_seconds=61)
    original_duration = config.MAX_AUDIO_DURATION
    original_size = config.MAX_FILE_SIZE

    try:
        config.MAX_AUDIO_DURATION = 60
        config.MAX_FILE_SIZE = 0.000001
        result = validate_audio(temp_path)
    finally:
        config.MAX_AUDIO_DURATION = original_duration
        config.MAX_FILE_SIZE = original_size
        os.unlink(temp_path)

    assert result.is_valid is False
    assert result.duration == 61
    assert result.error == "File exceeded maximum supported duration of 1 minutes"


def _write_wav_header(duration_seconds: int) -> str:
    """Create a tiny WAV file whose header declares a long duration."""
    sample_rate = 8000
    channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    data_size = duration_seconds * byte_rate
    riff_size = 36 + data_size

    header = (
        b"RIFF"
        + struct.pack("<I", riff_size)
        + b"WAVE"
        + b"fmt "
        + struct.pack(
            "<IHHIIHH",
            16,
            1,
            channels,
            sample_rate,
            byte_rate,
            block_align,
            bits_per_sample,
        )
        + b"data"
        + struct.pack("<I", data_size)
    )

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(header)
        return f.name
