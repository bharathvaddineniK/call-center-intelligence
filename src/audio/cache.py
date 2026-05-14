import hashlib
from src.database.models import Call
from src.database.session import session_scope
from typing import Optional

def compute_hash(file_path: str) -> str:
    """Computes hash for the input file and returns the hash"""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def get_cached_transcript(file_hash: str) -> Optional[dict]:
    """Checks the db if the given file hash is present and returns the corresponding transcription"""
    with session_scope() as session:
        call = session.query(Call).filter(Call.file_hash == file_hash).first()
        if call is not None:
            return {
                "text": call.transcription,
                "segments": call.segments or [],
                "confidence": call.confidence or 1.0,
                "duration": call.duration
            }
        return None
