import logging
from pathlib import Path
from uuid import UUID

from loguru import logger
from sqlmodel import Session, SQLModel, create_engine

from chandragen import system_config

# This import is purely to run class decorators
from chandragen.db import models  #noqa: F401 #pyright:ignore


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        # Try to map logging level to loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_globals["__name__"] == __name__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

if system_config.log_all_sql:
    # Redirect SQLAlchemy logs
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

class EntryNotFoundError(Exception):
    """Raised when a database entry cannot be found"""
    def __init__(self, entry_id: UUID):
        self.entry_id = entry_id
        super().__init__(f"Entry {self.entry_id} does not exist in the database!")

DATABASE_URL = system_config.db_url

# Create the engine at import time (persistent)
engine = create_engine(DATABASE_URL, echo=system_config.log_all_sql, pool_pre_ping=True)

def init_db():
    """Create all defined tables if they don't exist yet~"""
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)

# Initialize database tables on first import if file doesn't exist yet!
if not Path("chandragen.db").exists():
    init_db()
