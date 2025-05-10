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

class WorkerProcess:
    def __init__(self, worker_id: UUID, conn: Connection):
        # worker level imports
        from loguru import logger

        from chandragen.db.controllers.job_queue import JobQueueController
        from chandragen.jobs.runners import RUNNER_REGISTRY
        
        logger.debug(f"Starting worker process {worker_id}!")
        self.logger = logger
        self.runners = RUNNER_REGISTRY
        self.job_queue_db = JobQueueController()
        self.id = worker_id
        self.pipe = conn
        self.running = False
        self.current_job: UUID | None = None
        self._ipc_thread = threading.Thread(target=self.handle_ipc, daemon=True)
         
    def setup(self):
        pass
    
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
        self.running = True
        self.setup()
        self._ipc_thread.start()
        while self.running:
            job = self.job_queue_db.claim_next_pending_job(self.id)
            if job:
                job_id, _job_type = job
                self.logger.debug(f"worker {self.id} claimed job {job_id}")
                self.current_job = job_id
                self.run_job(job)
                self.current_job = None
            else:
                sleep(0.001)
        self.cleanup()
    
    def stop(self):
        self.running = False    
    
class ProcessPooler:
    def __init__(self, min_workers: int = 3, max_workers: int = 16, check_interval: float = 0.01):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.check_interval = check_interval
        self.job_queue_db = JobQueueController()
        
        self.workers: dict[UUID, tuple[Process, Connection]] = {}
    
    def start(self):
        # bring up minimal process pool
        logger.debug(f"bringing up minimal worker pool of {self.min_workers} workers!! :3")
        for _ in range(self.min_workers):
            self.spawn_worker()
        
        while system_config.running:
            self.balance_workers()
            sleep(self.check_interval)
        logger.info("chandragen is exiting, shutting down all workers!")
        for worker in list(self.workers.keys()):
           self.stop_worker(worker) 
        
    def worker_loop(self, worker_id: UUID, conn: Connection):
        """ Prepares the worker process loop for worker spawning """
        worker = WorkerProcess(worker_id, conn)
        worker.run()
        
    def spawn_worker(self):
        worker_id = uuid4()
        parent_conn, child_conn = Pipe()
        worker_process = Process(target=self.worker_loop, args=(worker_id, child_conn))
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

    def balance_workers(self):
        """ Checks worker load, adds or removes workers as needed. """
        # Fetch the queue status from the database controller
        _pending_count, in_progress_count, ratio = self.job_queue_db.get_queue_status()
        total_workers = len(self.workers)
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