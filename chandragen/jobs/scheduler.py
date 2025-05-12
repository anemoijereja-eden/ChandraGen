from abc import ABC, abstractmethod
from threading import Event, Thread
from time import sleep
from typing import TypeVar

from loguru import logger

import chandragen
from chandragen import system_config
from chandragen.db.controllers.job_queue import JobQueueController
from chandragen.db.models.job_queue import JobQueueEntry
from chandragen.jobs import Job


class GarbageCollector:
    def __init__(self):
        self.job_queue_db = JobQueueController()
         
    def run(self):
        logger.debug("garbage collector thread initializing")
        while system_config.running:
            self.tick()
            sleep(120)

    def tick(self):
        logger.debug("Purging completed jobs from job queue")
        self.job_queue_db.delete_completed_jobs()        

J = TypeVar("J", bound=Job)
class SchedulerRunner:
    def __init__(self):
        self.tick_rate = system_config.tick_rate
        # start a pooler up!
        self.garbage_collector = GarbageCollector()
        
        self._garbage_collector_thread = Thread(target=self.garbage_collector.run, daemon=True)

        self._garbage_collector_thread.start()
        
    def run(self, jobs: list[J]):
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
            sleep(self.tick_rate)
        logger.info(f"scheduler {scheduler} exiting")
        scheduler.stop()

# base job scheduler abstract class should inherit from the scheduler runner
# this way we can keep the scope of the schedulers limited to just inserting jobs,
# but they can still access the invoked pooler
class JobScheduler(ABC, SchedulerRunner):
    def __init__(self):
        self.job_queue_db = JobQueueController()
        self.job_queue_db.tune_autovacuum()

      
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
        logger.debug("Invoking garbage collector to purge complete jobs")
        self.job_queue_db.delete_completed_jobs() 
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