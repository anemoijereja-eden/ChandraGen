import json
from abc import ABC, abstractmethod
from uuid import UUID

from chandragen.db.controllers.job_queue import JobQueueController
from chandragen.db.models.job_queue import JobQueueEntry
from chandragen.jobs import Job


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
    def cleanup(self) -> None:
        pass   

# JobRunner has a Job type that must be provided.
class JobRunner[J: Job](BaseJobRunner):
    job_class: type[J]  # to be specified by subclasses!

    def __init__(self, job_id: UUID):
        self.job_id = job_id
        self.job_queue_db = JobQueueController()
        self.job_entry: JobQueueEntry | None = self.job_queue_db.get_job_by_id(job_id)
        config_dict = json.loads(self.job_entry.config_json)
        self.job = self.job_class.model_validate(config_dict)
     
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