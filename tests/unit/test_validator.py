import os
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
    assert result.error == "Unsupported audio format"


def test_non_existent_file():
    """Test that non existent file returns is valid false"""
    result = validate_audio("fake/path.wav")
    assert result.is_valid is False
    assert result.error == "File not found"


def test_large_file():
    """Test that large file returns is valide false"""
    original = config.MAX_FILE_SIZE
    config.MAX_FILE_SIZE = 0.001
    result = validate_audio("data/audio/call_114.mp3")
    config.MAX_FILE_SIZE = original
    assert result.is_valid is False
    assert result.error == "File exceeded maximum supported size"
