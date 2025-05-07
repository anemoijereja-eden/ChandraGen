from abc import ABC, abstractmethod
from uuid import UUID


class JobRunner(ABC):
    def __init__(self, job_id: UUID):
       self.job_id = job_id
     
    @abstractmethod
    def setup(self) -> None:
        pass
    
    @abstractmethod
    def run(self) -> None:
        pass       
    
    @abstractmethod
    def cleanup(self) -> None:
        pass
    
RUNNER_REGISTRY: dict[str, type[JobRunner]] = {}

def jobrunner(name: str):
    def wrapper(cls: type[JobRunner]):
        RUNNER_REGISTRY[name] = cls
        return cls
    return wrapper