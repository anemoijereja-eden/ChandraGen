# CLI tools can use pront, T201 is only for logging.
#ruff: noqa: T201
import code
import threading
from typing import Any


class InteractiveShellThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True, name="ChandraShell")
        from chandragen.db.controllers.job_queue import JobQueueController
        self.job_queue = JobQueueController()
        
        # You can prep handy commands here~
        self.helpers: dict[str, Any] = {
            "register_job": self.register_job,
            "list_jobs": self.list_jobs,
        }

    def run(self):
        local_ctx = {
            "job_queue": self.job_queue,
            "help": self.print_help,
            **self.helpers,
        }
        print("✨ ChandraGen interactive shell started! Type `help()` for commands~")
        code.interact(local=local_ctx, banner="🐚 chandra> Interactive shell ready~")

    def print_help(self):
        print("This interactive shell is intended for debugging purposes")
        print("✨ Available helper commands:")
        for name in self.helpers:
            print(f" - {name}()")

    def register_job(self, job_data: str):
        # example implementation uwu~
        print("Not yet implemented, but here's where you'd enqueue a job with custom args~")

    def list_jobs(self):
        return self.job_queue.get_pending_jobs()

