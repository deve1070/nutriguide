from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    # For SQLite (local testing without Postgres):
    # connect_args={"check_same_thread": False},
    pool_pre_ping=True,  # reconnect after idle timeouts
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """All ORM models inherit from this"""

    pass


def get_db():
    """FastAPI dependency — yields a DB session and always closes it"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
