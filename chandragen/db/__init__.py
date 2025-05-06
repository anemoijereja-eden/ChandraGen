from pathlib import Path
from uuid import UUID

from sqlmodel import Session, SQLModel, create_engine

# This import is purely to run class decorators, it's not unused even if your IDE says it is.
from chandragen.db import models  # noqa: F401


class EntryNotFoundError(Exception):
    """Raised when a database entry cannot be found"""
    def __init__(self, entry_id: UUID):
        self.entry_id = entry_id
        super().__init__(f"Entry {self.entry_id} does not exist in the database!")

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
