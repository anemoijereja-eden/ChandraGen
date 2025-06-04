import code
import threading
from typing import Any

from loguru import logger


class InteractiveShellThread(threading.Thread):
    """Thread to execute arbitrary code in a running chandragen instance.

    This supervisory thread allows developers to debug, monitor, and manipulate
    program state at runtime. Currently, it's a skeleton with low priority
    for expansion.
    """

    def __init__(self):
        super().__init__(daemon=True, name="ChandraShell")
        from chandragen.db.controllers.job_queue import JobQueueController

        self.job_queue = JobQueueController()
        self.logger = logger

        self.logger.level("SHELL", no=255, color="<cyan>")
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
        self.logger.log("SHELL", "✨ ChandraGen interactive shell started! Type `help()` for commands")
        code.interact(local=local_ctx, banner="🐚 chandra> Interactive shell ready")

    def print_help(self):
        self.logger.log("SHELL", "This interactive shell is intended for debugging purposes")
        self.logger.log("SHELL", "✨ Available helper commands:")
        for name in self.helpers:
            self.logger.log("SHELL", f" - {name}()")

    def register_job(self, job_data: str):
        # example implementation
        self.logger.log("SHELL", "Not yet implemented, but here's where you'd enqueue a job with custom args")

    def list_jobs(self):
        return self.job_queue.get_pending_jobs()
