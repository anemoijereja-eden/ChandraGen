import threading
from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection
from time import sleep
from typing import Any
from uuid import UUID, uuid4

from loguru import logger

from chandragen import system_config
from chandragen.db.controllers.job_queue import JobQueueController


class WorkerShutdownError(Exception):
    """Raised when a worker fails to shut down cleanly."""
    def __init__(self, worker_id: UUID, reason: str = "Unknown"):
        self.worker_id = worker_id
        self.reason = reason
        super().__init__(f"Worker {worker_id} failed to shut down cleanly: {reason}")

class WorkerProcess(Process):
    def __init__(self, worker_id: UUID, conn: Connection):
        super().__init__()
        # worker level imports
        from loguru import logger

        from chandragen.db.controllers.job_queue import JobQueueController
        from chandragen.jobs.runners import RUNNER_REGISTRY
        
        self.logger = logger
        self.runners = RUNNER_REGISTRY
        self.job_queue_db = JobQueueController()
        self.id = worker_id
        self.pipe = conn
        self.running = False
        self.current_job: UUID | None = None
    
    def setup(self):
        self.running = True
        self._ipc_thread = threading.Thread(target=self.handle_ipc, daemon=True) 
        self._ipc_thread.start()
        logger.debug(f"Starting worker process {self.id}!")
        self.name = f"chandra_worker_{str(self.id)[:4]}"
    
    def run_job(self, job: tuple[UUID, str]):
        job_id, job_type = job
        self.logger.debug(f"worker {self.id} attempting to run job {job_id} of type {job_type}")
        runner_cls = self.runners.get(job_type)
        if not runner_cls:
            msg = f"No runner registered for job type {job_type} (job id: {job_id})"
            raise ValueError(msg)
        runner = runner_cls(job_id)
        runner.setup()
        try:
            runner.run()
        finally:
            runner.cleanup()
        self.logger.debug(f"Worker {self.id} completed job {job_id}")
        
    def cleanup(self):
        logger.debug(f"worker {self.id} is shutting down")
    
    def handle_ipc(self):
        while self.running:
        # IPC is handled as a seperate thread in the process that acts as a supervisor. 
            if self.pipe.poll():
                data: list[Any] | tuple[Any] = self.pipe.recv()
                self.logger.debug(f"worker {self.id} recieved ipc message {data}")
                if not isinstance(data, (list, tuple)) or len(data) == 0:  # pyright: ignore[reportUnnecessaryIsInstance] We're using isinstance to verify it at runtime, so this is actually useful.
                    self.pipe.send(["error", "Invalid message format"])
                    continue
                if data[0] == "stop":
                    self.stop()
                    self.pipe.send(["stop", True])
                
                elif data[0] == "status":
                    self.pipe.send([
                    "status",
                    True,
                    self.current_job,
                    self.running,
                    ])
                else:
                    self.pipe.send([data[0], False])
            sleep(0.1) 
    
    def run(self):
        self.setup()
        while self.running:
            job = self.job_queue_db.claim_next_pending_job(self.id)
            if job:
                job_id, _job_type = job
                self.logger.debug(f"worker {self.id} claimed job {job_id}")
                self.current_job = job_id
                self.run_job(job)
                self.current_job = None
            else:
                # queue miss means we can just go ahead and sleep for a second.
                #logger.debug(f"worker process {self.id} missed queue, resting for a sec")
                sleep(0.5)
        self.cleanup()
    
    def stop(self):
        self.running = False    
    
class ProcessPooler:
    def __init__(self):
        self.min_workers = system_config.minimum_workers_per_pool
        self.max_workers = system_config.max_workers_per_pool
        self.check_interval = system_config.tick_rate
        self.job_queue_db = JobQueueController()
        
        self.workers: dict[UUID, tuple[Process, Connection]] = {}
    
    def start(self):
        # bring up minimal process pool
        logger.debug(f"bringing up minimal worker pool of {self.min_workers} workers!! :3")
        for _ in range(self.min_workers):
            self.spawn_worker()
        
        while system_config.running:
            #logger.debug("ticking pooler")
            self.clean_up_dead_workers()
            self.balance_workers()
            sleep(self.check_interval)
        logger.info("chandragen is exiting, shutting down all workers!")
        for worker in list(self.workers.keys()):
           self.stop_worker(worker) 
        
    def spawn_worker(self):
        worker_id = uuid4()
        parent_conn, child_conn = Pipe()
        worker_process = WorkerProcess(worker_id, child_conn)
        worker_process.start()
        self.workers[worker_id] = (worker_process, parent_conn)

    def stop_worker(self, worker_id: UUID):
        # Send an IPC command asking the worker to exit cleanly
        if worker_id not in self.workers:
            return
        process, connection = self.workers[worker_id]
        connection.send(["stop"])
        if connection.poll(timeout=5):
                response = connection.recv()
                if response == ["stop", True]:
                    process.join(timeout=5)
                    self.workers.pop(worker_id, None)
                    return
        # if it didn't stop gracefully, force kill it.
        try:
                process.kill()
        except Exception:
                raise WorkerShutdownError(worker_id, reason="Could not kill process! something is very wrong!!") from None
        finally:
                del self.workers[worker_id]
    
    def clean_up_dead_workers(self):
        for worker_id, worker in list(self.workers.items()):
            worker_process, _worker_connection = worker
            if worker_process.is_alive():
                continue
            logger.warning(f"Found dead worker process {worker_id}, removing from pool.")
            del self.workers[worker_id]        
        
    def balance_workers(self):
        """ Checks worker load, adds or removes workers as needed. """
        # Fetch the queue status from the database controller
        _pending_count, in_progress_count, ratio = self.job_queue_db.get_queue_status()
        total_workers = len(self.workers)
        
        # aggressively spawn workers to ensure the minimum is met.
        if total_workers < self.min_workers:
            logger.warning(f"Worker pool below minimum! ({total_workers} < {self.min_workers})")
            for _ in range(self.min_workers - total_workers):
                self.spawn_worker()
            total_workers = self.min_workers
        # calculate this after we ensure the pool is filled properly to avoid divide-by-zero
        worker_load_ratio = in_progress_count / total_workers
        
        #if more than 25% of the jobs in the queue are pending, and 80% or more of to workers are going, spawn a worker.
        if (
            ratio > .25 
            and worker_load_ratio >= .8
            and total_workers < self.max_workers
        ):
            logger.info("worker pool overload detected, spawning worker")
            self.spawn_worker()
        
        # if there aren't many pending jobs (<1%), scale back the pooler 
        if (
            ratio < .01
            and worker_load_ratio <= .5
            and total_workers > self.min_workers
        ):
            logger.info("worker pool underloaded, terminating a worker.")
            worker_to_stop = next(iter(self.workers.keys()))
            if worker_to_stop:
                self.stop_worker(worker_to_stop)
        
    def get_worker_status(self, worker_id: UUID) -> list[str | bool | int]:
        _process, connection = self.workers[worker_id]
        connection.send(["status"])
        if connection.poll(timeout=5):
            return connection.recv()
        return ["no response", False]