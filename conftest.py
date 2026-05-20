import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.database.session as db_session
from src.database.models import Base

sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(autouse=True)
def use_test_db(tmp_path):
    """Use a temporary SQLite database for all tests."""
    test_db = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{test_db}")
    Base.metadata.create_all(engine)

    original_engine = db_session.engine
    original_session = db_session.SessionLocal

    db_session.engine = engine
    db_session.SessionLocal = sessionmaker(bind=engine)

    yield

    db_session.engine = original_engine
    db_session.SessionLocal = original_session
