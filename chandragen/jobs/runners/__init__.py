import json
from abc import ABC, abstractmethod
from uuid import UUID

from chandragen.db.controllers.job_queue import JobQueueController
from chandragen.db.models.job_queue import JobQueueEntry
from chandragen.jobs import Job


# Generic base class skeleton used for typing shenanigans
class BaseJobRunner(ABC):
    @abstractmethod
    def __init__(self, job_id: UUID):
        pass

    @abstractmethod
    def setup(self) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        pass

    @abstractmethod
    def retry(self) -> None:
        pass

    @abstractmethod
    def cleanup(self) -> None:
        pass


# JobRunner has a Job type that must be provided.
class JobRunner[J: Job](BaseJobRunner):
    job_class: type[J]  # to be specified by subclasses!
    SHOULD_RERUN = True
    MAX_RETRIES = 3

    def __init__(self, job_id: UUID):
        self.job_id = job_id
        self.job_queue_db = JobQueueController()
        self.job_entry: JobQueueEntry | None = self.job_queue_db.get_job_by_id(job_id)
        config_dict = json.loads(self.job_entry.config_json)
        self.job = self.job_class.model_validate(config_dict)

    # Job Retryer
    # This is the main system for handling of failed Jobs.
    # in the event that a job fails or a worker dies, this method is used to handle the stale or failed job.
    def retry(self):
        self.cleanup()
        if self.job_entry is None:
            return

        # fail the job and quit if we're not set to re-run it.
        if not self.SHOULD_RERUN:
            self.job_queue_db.mark_job_failed(self.job_id)
            return

        # Check if we still have retries left. if not, fail the job.
        if self.job_entry.retries <= self.MAX_RETRIES:
            self.job_queue_db.increment_retries(self.job_id)
            # mark the job pending, so a worker process can grab it.
            self.job_queue_db.mark_job_pending(self.job_id)
        else:
            self.job_queue_db.mark_job_failed(self.job_id)

    @abstractmethod
    def setup(self) -> None:
        pass

    @abstractmethod
    def run(self) -> None:
        pass

    @abstractmethod
    def cleanup(self) -> None:
        pass


RUNNER_REGISTRY: dict[str, type[BaseJobRunner]] = {}


# decorator that loads jobtypes into the registry
def jobrunner(name: str):
    def wrapper(cls: type[BaseJobRunner]):
        RUNNER_REGISTRY[name] = cls
        return cls

    return wrapper
