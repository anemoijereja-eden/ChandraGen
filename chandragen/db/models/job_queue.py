from datetime import UTC, datetime
from enum import IntEnum
from uuid import UUID, uuid4

from sqlalchemy import DDL, event
from sqlmodel import Field, Index, SQLModel

"""
ChandraGen Job Queue Models 🚀✨

This module defines the `JobQueueEntry` table, which represents the active task 
queue for ChandraGen's job execution system.

Each entry in the queue contains:
- A unique ID and human-readable name
- The type of job to run (for dynamic runner dispatch)
- A serialized job configuration (JSON string)
- Timestamps for creation and execution lifecycle
- A worker claim field for coordination across processes
- A `JobState` enum indicating current job progress

Queue entries are prioritized using an integer-based system where higher values 
get scheduled sooner.

Speed Boost: This table is UNLOGGED, meaning Postgres skips writing it 
to the WAL for max performance. Perfect for ephemeral workloads that don't need 
persistence after a crash
"""


class JobState(IntEnum):
    PENDING = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    FAILED = 3


class JobQueueEntry(SQLModel, table=True):
    __tablename__ = "job_queue"  # pyright:ignore
    __table_args__ = (
        Index("ix_job_state", "state"),
        Index("ix_job_created_at", "created_at"),
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True, description="Human-readable job name or label")
    job_type: str = Field(description="The registered job runner type to execute this entry")
    config_json: str = Field(description="Serialized job config (JSON string)")

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Time the job was started at")
    started_at: datetime | None = Field(default=None, description="When the job actually began execution")

    claimed_by: UUID | None = Field(default=None, description="What worker process has ownership of a queued job")
    state: JobState = Field(
        default=0,
        description="Integer representing the current job state, where 0 is not started, 1 is in-progress, 2 is completed, and 3 is failed.",
    )
    retries: int = Field(default=0, description="How many times the job has been retried")

    priority: int = Field(default=0, description="Optional priority system for the queue (higher = sooner)")


# Use an SQLAlchemy listener to ensure the table is *unlogged* after creation!
# This tells postgres that we don't care about persistence with this table, so it won't bother writing it to disk.
# keeps it going extra fast!!
event.listen(
    JobQueueEntry.__table__,  # pyright: ignore
    "after_create",
    DDL("ALTER TABLE %(table)s SET UNLOGGED"),
)

