from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from src.database.models import Base
import config


engine = create_engine(f"sqlite:///{config.DATABASE_PATH}")
SessionLocal = sessionmaker(bind=engine)

@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    Base.metadata.create_all(engine)