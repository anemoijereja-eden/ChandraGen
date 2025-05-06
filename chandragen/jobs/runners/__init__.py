from abc import ABC, abstractmethod


class JobRunner(ABC):
    def __init__(self, job_name: str, config: dict[str, str]):
        self.job_name = job_name
        self.config = config
        
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