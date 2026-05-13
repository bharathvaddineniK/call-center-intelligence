import config
from pathlib import Path


def test_config_paths():
    """Test that all path configurations are properly set as absolute Path objects."""
    path_vars = [
        config.BASE_DIR,
        config.AUDIO_DIR,
        config.REPORTS_DIR,
        config.CACHE_DIR,
        config.DATABASE_PATH,
    ]
    
    for path_var in path_vars:
        assert isinstance(path_var, Path), f"{path_var} is not a Path object"
        assert path_var.is_absolute(), f"{path_var} is not an absolute path"


def test_config_api_keys():
    """Test that all required API keys are loaded."""
    api_keys = [
        config.OPENAI_API_KEY,
        config.GROQ_API_KEY,
        config.LANGSMITH_API_KEY,
    ]
    
    for api_key in api_keys:
        assert api_key is not None, "One or more API keys are not loaded"