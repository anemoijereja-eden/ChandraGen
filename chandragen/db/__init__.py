from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from chandragen.db import models  # noqa: F401

DATABASE_URL = "sqlite:///./chandragen.db"

# Create the engine at import time (persistent)
engine = create_engine(DATABASE_URL, echo=False)

def init_db():
    """Create all defined tables if they don't exist yet~"""
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)

# Initialize database tables on first import if file doesn't exist yet!
if not Path("chandragen.db").exists():
    init_db()
