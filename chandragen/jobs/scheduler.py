from abc import ABC, abstractmethod
from threading import Thread
from time import sleep

from chandragen import system_config
from chandragen.db.controllers.job_queue import JobQueueController
from chandragen.jobs.pooler import ProcessPooler
from chandragen.jobs.types import ConverterJob


def run_scheduler(jobs: list[ConverterJob]):
    if system_config.scheduler_mode == "oneshot":
        scheduler = OneShotScheduler()
    if system_config.scheduler_mode == "cron":
        scheduler = CronScheduler()
    else:
        print("Err: valid scheduler not specified")
        return
    scheduler.start()   
    while system_config.running:
        scheduler.tick()
        sleep(10)
    scheduler.stop()


class JobScheduler(ABC):
    def __init__(self):
        self.job_queue_db = JobQueueController
        self.pooler = ProcessPooler()

        self._pooler_thread = Thread(target=self.pooler.start, daemon=True)
        self._pooler_thread.start()
        
    @abstractmethod
    def start(self):
        pass
    
    @abstractmethod
    def tick(self):
        pass
    
    @abstractmethod
    def stop(self):
        pass
   

class OneShotScheduler(JobScheduler):
    def start(self):
        pass
    def tick(self):
        pass
    def stop(self):
        pass

class CronScheduler(JobScheduler):
    def start(self):
        pass
    def tick(self):
        pass
    def stop(self):
        pass


#TODO:
# main loop
# spawn pooler on thread before starting main loop
#- main loop needs to look at the queue and hand off jobs to worker processes via process pooler