import json
import random
import threading
from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection
from queue import Queue
from time import sleep
from uuid import UUID, uuid4

from chandragen.jobs.runners import RUNNER_REGISTRY


class WorkerShutdownError(Exception):
    """Raised when a worker fails to shut down cleanly."""
    def __init__(self, worker_id: UUID, reason: str = "Unknown"):
        self.worker_id = worker_id
        self.reason = reason
        super().__init__(f"Worker {worker_id} failed to shut down cleanly: {reason}")

class WorkerProcess:
    def __init__(self, worker_id: UUID, conn: Connection):
        from chandragen.db.controllers.job_queue import JobQueueController
        self.job_queue_db = JobQueueController()
        self.id = worker_id
        self.pipe = conn
        self.running = False
        self.thread_pool: list[threading.Thread] = []
        self.max_queue_size = 5
        self.job_queue: Queue[tuple[str, str, str]] = Queue() # jobname, runner, config json
    
    def register_job(self, job: tuple[str, str, str]):
        self.job_queue.put(job)
        
    
    def setup(self):
        pass
    
    def run_job(self, job: tuple[str, str, str]):
        runner_cls = RUNNER_REGISTRY.get(job[1])
        if not runner_cls:
            msg = f"No runner registered for job type {job[2]}"
            raise ValueError(msg)
        config = json.loads(job[2])
        runner = runner_cls(job[0], config)
        runner.setup()
        try:
            runner.run()
        finally:
            runner.cleanup()
        
    def cleanup(self):
        # ensure all threads are done running before exiting the process 
        for thread in self.thread_pool:
            thread.join()
        
    def run(self):
        self.running = True
        self.setup()
        while self.running or not self.job_queue.empty():
            # handle IPC loop
            if self.pipe.poll():
                data = self.pipe.recv()
                if data[0] == "add_job":
                    self.register_job((data[1], data[2], data[3]))
                    self.pipe.send(["add_job", True])
                
                elif data[0] == "stop":
                    self.stop()
                    self.pipe.send(["stop", True])
                
                elif data[0] == "status":
                    self.pipe.send([
                        "status",
                        True,
                        self.job_queue.qsize(),
                        self.max_queue_size,
                        self.running,
                    ])
                else:
                    self.pipe.send([data[0], False])
                
            job = self.job_queue.get(timeout=5)
            if job:
                job_thread = threading.Thread(target=self.run_job, args=(job,))
                job_thread.start()
                self.thread_pool.append(job_thread)
            else:
                sleep(10)
        self.cleanup()
    
    def stop(self):
        self.running = False    
    
class ProcessPooler:
    def __init__(self, min_workers: int = 3, max_workers: int = 16, check_interval: int = 10):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.check_interval = check_interval
        
        self.workers: dict[UUID, tuple[Process, Connection]] = {}
    
    def start(self):
        # bring up minimal process pool
        for _ in range(self.min_workers):
            self.spawn_worker()
        
        while True:
            self.balance_workers()
            sleep(self.check_interval)
    
    def worker_loop(self, worker_id: UUID, conn: Connection):
        worker = WorkerProcess(worker_id, conn)
        worker.run()
        
    def spawn_worker(self):
        worker_id = uuid4()
        parent_conn, child_conn = Pipe()
        worker_process = Process(target=self.worker_loop, args=(worker_id, child_conn))
        worker_process.start()
        self.workers[worker_id] = (worker_process, parent_conn)

    def _stop_worker(self, worker_id: UUID):
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
        total_capacity: int     = 0
        total_queued: int       = 0
        idle_workers: list[UUID] = [] # worker ID
        
        for worker_id, (_process, connection) in self.workers.items():
            try:
                connection.send(["status"])
                if connection.poll(timeout = 1):
                    response = connection.recv()
                    if response[0] == "status" and response[1] is True:
                        queue_size = response[2]
                        max_queue = response[3]
                        running = response[4]
                        
                        total_capacity += max_queue
                        total_queued += queue_size
                        if queue_size == 0 and running:
                            idle_workers.append(worker_id)     
            except Exception:
                self._stop_worker(worker_id)
        
        # Check if we're overloaded or near capacity, add more workers if we are.
        if total_queued >= total_capacity * .8 and len(self.workers) < self.max_workers :
            self.spawn_worker()
        
        # Check if we're underloaded and above minimum. scale back if we are.
        if total_queued < total_capacity // 2 and len(self.workers) > self.min_workers:
            for worker_id in idle_workers:
                self._stop_worker(worker_id)
    
    def get_worker_status(self, worker_id: UUID) -> list[str | bool | int]:
        _process, connection = self.workers[worker_id]
        connection.send(["status"])
        if connection.poll(timeout=5):
            return connection.recv()
        return ["no response", False]
    
    def assign_job_to_worker(self, job_id: UUID):
        lowest_load: int = 65535
        chosen_worker: UUID = random.choice(list(self.workers.items()))[0] # Grab the ID of a random entry from the dict to provide a sane default
        
        for worker_id in self.workers:
            status = self.get_worker_status(worker_id)
            if status[0] == "status" and status[1] is True:
                queue_size = status[2]
                _max_queue_size = status[3]
                running = status [4]
                if running is True and type(queue_size) is int and queue_size < lowest_load:
                    lowest_load = queue_size
                    chosen_worker = worker_id
                
        _process, connection = self.workers[chosen_worker]
        assigned = False
        # Try to assign to the chosen worker. if that fails, throw the job to a random worker.
        while not assigned:
            connection.send(["assign", str(job_id)])
            if connection.poll(timeout=5) and connection.recv == ["assign", True]:
                return
            chosen_worker = random.choice(list(self.workers.items()))[0]
            
