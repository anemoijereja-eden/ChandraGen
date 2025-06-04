# TODO: Add support for cron schedule to JobConfig type
# TODO: Add an API endpoint that allows for job registration and triggering
# TODO: Allow modification of system config from api maybe?
from __future__ import annotations

from abc import abstractmethod

from pydantic import BaseModel


class Job(BaseModel):
    """Base job class, extended by job types"""

    jobname: str
    interval: str

    @property
    @abstractmethod
    def job_type(self) -> str:
        """Return the registered job type string."""


__all__ = [
    "Job",
]

