from datetime import UTC, datetime
from enum import IntEnum
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

"""
ChandraGen Configuration Database Models ✨

This module defines the SQLModel data structures used to represent and persist 
ChandraGen's scheduler job configurations.

Each `ConfigEntry` represents a unit of scheduled work, handled by a specific 
scheduler type (e.g., ONESHOT, CRONJOB, or API-triggered).

Config entries are grouped into `ConfigGroup`s, which:
- Serve as logical containers for related jobs (e.g., from the same TOML section)
- Provide default values (via `defaults_json`) to be applied to group members
- Help users organize, export, and manage their configurations cleanly

These models power the config import/export logic, scheduling queue, and 
long-term persistence of job state across runs~ 🛠️💖
"""

class SchedulerType(IntEnum):
    ONESHOT = 0
    CRONJOB = 1
    API     = 2

class ConfigGroup(SQLModel, table=True):
    __tablename__ = "config_groups" #pyright:ignore

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str = Field(index=True, unique=True, description="Name for this group (e.g. for TOML section export)")
    description: str = Field(default=None, description="Human-readable description of what a config group is for")
    defaults_json: str = Field(description="Serialized JSON object of default values for this group")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    entries: list["ConfigEntry"] = Relationship(back_populates="group")

class ConfigEntry(SQLModel, table=True):
    __tablename__ = "config" #pyright:ignore
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # group IDs will be used as part of the import/export process for toml configs, as well as to allow end users to organize the config db.
    group_id: UUID = Field(foreign_key="config_groups.id", index=True, description="ID used to associate config entries with each other")
    group: ConfigGroup | None = Relationship(back_populates="entries")
    name: str = Field(index=True, description="Human-readable name or label")
    
    scheduler: SchedulerType = Field(index=True, description="Which scheduler should handle this entry")
    interval: str = Field(index=True, description="Interval field—interpretation depends on the scheduler")
    json_job_payload: str = Field(description="Serialized job Queue entry (JSON string)")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True, description="Time the config entry was first created")
    last_run_at: datetime | None = Field(default=None, description="Last time this config was executed")
    
    priority: int = Field(default=0, description="Optional priority system (higher = sooner)")
    
