import hashlib

from src.database.models import TranscriptionCache
from src.database.session import session_scope


def compute_hash(file_path: str) -> str:
    """Computes hash for the input file and returns the hash"""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_cached_transcript(file_hash: str) -> dict | None:
    """Return cached transcription data for the given file hash."""
    with session_scope() as session:
        call = (
            session.query(TranscriptionCache)
            .filter(TranscriptionCache.file_hash == file_hash)
            .first()
        )
        if call is not None:
            return {
                "text": call.text,
                "segments": call.segments or [],
                "confidence": call.confidence or 1.0,
                "duration": call.duration,
            }
        return None


def save_to_cache(
    file_hash: str,
    text: str,
    segments: list,
    confidence: float,
    duration: float,
) -> None:
    """Save a transcription result to the cache for future lookups."""
    with session_scope() as session:
        session.add(
            TranscriptionCache(
                file_hash=file_hash,
                text=text,
                segments=segments,
                confidence=confidence,
                duration=duration,
            )
        )
