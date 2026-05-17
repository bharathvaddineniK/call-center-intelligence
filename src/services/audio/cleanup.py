"""Delete old files from local audio-related directories."""

import logging
import re
import time
from pathlib import Path

logger = logging.getLogger(__name__)

SECONDS_PER_HOUR = 3600


def cleanup_old_files(
    directory: str,
    max_age_hours: int = 24,
    filename_pattern: str | None = None,
) -> int:
    """Delete audio files older than max_age_hours. Returns count of deleted files."""
    directory_path = Path(directory)

    if not directory_path.exists():
        return 0

    deleted_count = 0

    for file_path in directory_path.iterdir():
        if filename_pattern and not re.fullmatch(filename_pattern, file_path.name):
            continue

        if not _should_delete_file(file_path, max_age_hours):
            continue

        file_path.unlink()
        logger.info("Deleted old audio file: %s", file_path.name)
        deleted_count += 1

    return deleted_count


def _should_delete_file(file_path: Path, max_age_hours: int) -> bool:
    """Return True when a path is a file older than the configured age."""
    if not file_path.is_file():
        return False

    if not file_path.exists():
        return False

    return _get_file_age_hours(file_path) > max_age_hours


def _get_file_age_hours(file_path: Path) -> int:
    """Return file age in whole hours based on modified time."""
    file_modified_time = file_path.stat().st_mtime
    return int((time.time() - file_modified_time) / SECONDS_PER_HOUR)
