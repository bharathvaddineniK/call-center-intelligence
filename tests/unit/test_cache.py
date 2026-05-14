from src.audio.cache import compute_hash, get_cached_transcript

def test_compute_hash():
    """Computes hash twice for a same file and asserts both are same"""
    hash1 = compute_hash('data/audio/call_114.mp3')
    hash2 = compute_hash('data/audio/call_114.mp3')

    assert hash1 == hash2

def test_cache_miss():
    """Test that for a hash that's not in DB we get None"""
    call = get_cached_transcript("5218e7c7172d516a6501dae095701a135e36a2b928ee9586b8f2105e54a07925")
    assert call is None