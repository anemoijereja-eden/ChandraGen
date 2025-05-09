from abc import ABC, abstractmethod
from threading import Event, Thread
from time import sleep
from typing import TypeVar

from loguru import logger

from chandragen import system_config
import chandragen
from chandragen.db.controllers.job_queue import JobQueueController
from chandragen.db.models.job_queue import JobQueueEntry
from chandragen.jobs import Job
from chandragen.jobs.pooler import ProcessPooler

J = TypeVar("J", bound=Job)

def run_scheduler(jobs: list[J]):
    if system_config.scheduler_mode == "oneshot":
        scheduler = OneShotScheduler(jobs)
    elif system_config.scheduler_mode == "cron":
        scheduler = CronScheduler()
    else:
        logger.error(f"Err: valid scheduler not specified; {system_config.scheduler_mode} is invalid")
        return
    logger.info(f"Invoking scheduler {scheduler}")
    scheduler.start()   
    while system_config.running:
        scheduler.tick()
        sleep(10)
    logger.info(f"scheduler {scheduler} exiting")
    scheduler.stop()


class JobScheduler(ABC):
    def __init__(self):
        self.job_queue_db = JobQueueController()
        self.pooler = ProcessPooler()

        self._pooler_thread = Thread(target=self.pooler.start, daemon=True)
        self._pooler_thread.start()
       
    def add_job_to_queue(self, job_config: J): #pyright:ignore InvalidTypeVarUse  we do actually want this for genericization.
        """Serialize and enqueue a job for processing"""
        job_config_json = job_config.model_dump_json()
        job_type = job_config.job_type
        job_name = job_config.jobname
        job_entry = JobQueueEntry(
            job_type=job_type,
            name = job_name,
            config_json=job_config_json
        )
        self.job_queue_db.add_job(job_entry)
        
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
    def __init__(self, jobs: list[J]):
        super().__init__()
        self.jobs = jobs
        self.shutdown_event = Event()

    def start(self):
        # Queue all jobs uwu
        for job in self.jobs:
            self.add_job_to_queue(job)
        logger.info(f"✨ Queued {len(self.jobs)} jobs, nya~")
        self.shutdown_event.clear()

    def tick(self):
        # Check if all jobs are finished
        pending, in_progress, _ratio = self.job_queue_db.get_queue_status()
        jobs_in_flight = pending + in_progress
        
        if not jobs_in_flight:
            logger.info("💫 All jobs complete~ Time for a catnap :3")
            updated_config = system_config
            updated_config.running = False
            chandragen.update_system_config(updated_config)
            self.shutdown_event.set()

    def stop(self):
        logger.info("🛑 Scheduler stopped~")
        self.shutdown_event.set()


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