from threading import Thread

from chandragen.db.controllers.job_queue import JobQueueController
from chandragen.jobs.pooler import ProcessPooler


class OneShotScheduler:
    def __init__(self):
        self.job_quue_db = JobQueueController
        self.pooler = ProcessPooler()

        self._pooler_thread = Thread(target=self.pooler.start, daemon=True)
        self._pooler_thread.start()
#TODO:
# main loop
# spawn pooler on thread before starting main loop
#- main loop needs to look at the queue and hand off jobs to worker processes via process pooler