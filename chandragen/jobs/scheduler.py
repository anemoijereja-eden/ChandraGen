# TODO: re-do most of this file. current state does NOT align with the current vision of chandragen.
from abc import ABC, abstractmethod
from threading import Event, Thread
from time import sleep
from typing import TypeVar
from uuid import uuid1

from loguru import logger

import chandragen
from chandragen import system_config
from chandragen.db.controllers.job_queue import JobQueueController
from chandragen.db.models.job_queue import JobQueueEntry
from chandragen.jobs import Job


class GarbageCollector(Thread):
    """Garbage collector thread that periodically cleans completed jobs from the queue"""

    def __init__(self):
        self.id = uuid1()
        super().__init__(name="garbage_collector", daemon=True)
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
    """
    Class dedicated to managing the lifecycle of scheduler instances.

    Attributes:
        tick_rate (float): Defines the rate at which the scheduler operates, as set in the system configuration.
        garbage_collector (GarbageCollector): an instance of the garbage collector thread that handles keeping the queue clean.

    Methods:
        __init__():
            Initializes the SchedulerRunner with a tick rate and starts the garbage collector to manage system resources efficiently.

        run(jobs: list[J]):
            Initiates and manages the execution of a scheduler based on the system's configuration settings.
            Parameters:
                jobs (list[J]): A list of job instances to be scheduled. The mode of scheduling (oneshot or cron) is determined by the system configuration.
            Executes the appropriate scheduler and controls its operation through periodic ticks until the scheduler is commanded to stop.

    The SchedulerRunner acts as a bridge to start, handle execution, and terminate schedulers based on predefined operational modes, ensuring a seamless integration with overall system behavior.
    """

    def __init__(self):
        self.tick_rate = system_config.tick_rate
        # start a pooler up!
        self.garbage_collector = GarbageCollector()
        self.garbage_collector.start()

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


class JobScheduler(ABC, SchedulerRunner):
    """
    Abstract base class for a job scheduler, designed to be subclassed for specific scheduler modules.

    Attributes:
        job_queue_db (JobQueueController): Handles interactions with the job queue database, including inserting jobs and tuning auto-vacuum settings.

    Methods:
        __init__():
            Sets up the JobScheduler with a job queue controller and adjusts database settings.

        add_job_to_queue(job_config: J):
            Takes a job configuration object, serializes it, and adds it to the job queue.
            Parameters:
                job_config (J): Comprises the job's configuration details like type and name, preparing it for scheduling.

        start():
            Abstract method requiring implementation in subclasses. Initiates the scheduler, sets up recurring job intervals, or performs initial setup tasks.

        tick():
            Abstract method requiring implementation in subclasses. Represents a scheduler cycle or "tick," supporting periodic operations for scheduling maintenance.

        stop():
            Abstract method requiring implementation in subclasses. Manages operations to stop the scheduler gracefully, including necessary cleanup tasks.

    This class standardizes the interface and behavior for various scheduler implementations, focusing on job submission and lifecycle management.
    """

    def __init__(self):
        self.job_queue_db = JobQueueController()
        self.job_queue_db.tune_autovacuum()

    def add_job_to_queue(self, job_config: J):  # pyright:ignore InvalidTypeVarUse  we do actually want this for genericization.
        """Serialize and enqueue a job for processing"""
        job_config_json = job_config.model_dump_json()
        job_type = job_config.job_type
        job_name = job_config.jobname
        job_entry = JobQueueEntry(job_type=job_type, name=job_name, config_json=job_config_json)
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
    """register a single list of jobs to the queue, and then exit when all jobs are completed"""

    def __init__(self, jobs: list[J]):
        super().__init__()
        self.jobs = jobs
        self.shutdown_event = Event()

    def start(self):
        # Queue all jobs uwu
        for job in self.jobs:
            self.add_job_to_queue(job)
        logger.info(f"Queued {len(self.jobs)} jobs")
        self.shutdown_event.clear()

    def tick(self):
        # Check if all jobs are finished
        pending, in_progress, _ratio = self.job_queue_db.get_queue_status()
        jobs_in_flight = pending + in_progress

        if not jobs_in_flight:
            logger.info("All jobs complete, shutting down.")
            updated_config = system_config
            updated_config.running = False
            chandragen.update_system_config(updated_config)
            self.shutdown_event.set()

    def stop(self):
        logger.info("🛑 Scheduler stopped")
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
