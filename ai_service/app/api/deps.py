"""
API Dependencies
Common dependencies for API routes (DB sessions, auth, etc.)
"""
from typing import Generator
from app.db.session import SessionLocal


def get_db() -> Generator:
    """
    Dependency for getting database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
