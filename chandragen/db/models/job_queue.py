from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class JobQueueEntry(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, description="Human-readable job name or label")
    job_type: str = Field(description="The registered job runner type to execute this entry")
    config_json: str = Field(description="Serialized job config (JSON string)")
    
    created_at: datetime = Field(default=datetime.now(UTC), description="Time the job was started at")
    started_at: datetime | None = Field(default=None, description="When the job actually began execution")
    
    state: int = Field(default=0, description="Integer representing the current job state, where 0 is not started, 1 is in-progress, 2 is completed, and 3 is failed.")

    priority: int = Field(default=0, description="Optional priority system for the queue (higher = sooner)")
