from collections.abc import Sequence
from datetime import UTC, datetime

from sqlmodel import Session, asc, desc, select

from chandragen.db import get_session
from chandragen.db.models.job_queue import JobQueueEntry


class JobState:
    PENDING = 0
    IN_PROGRESS = 1
    COMPLETED = 2
    FAILED = 3
 
class JobQueueController:
    def __init__(self, session: Session | None = None):
        self.session = session or get_session()

    def add_job(self, job: JobQueueEntry):
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def get_pending_jobs(self, limit: int = 10) -> Sequence[JobQueueEntry]:
        stmt = select(JobQueueEntry).where(JobQueueEntry.state == 0).order_by(
            desc(JobQueueEntry.priority), asc(JobQueueEntry.created_at)
        ).limit(limit)
        return self.session.exec(stmt).all()

    def mark_job_in_progress(self, job_id: int):
        job = self.session.get(JobQueueEntry, job_id)
        if job:
            job.state = 1
            job.started_at = datetime.now(UTC)
            self.session.commit()
        return job

    def mark_job_complete(self, job_id: int):
        job = self.session.get(JobQueueEntry, job_id)
        if job:
            job.state = 2
            self.session.commit()
        return job

    def mark_job_failed(self, job_id: int):
        job = self.session.get(JobQueueEntry, job_id)
        if job:
            job.state = 3
            self.session.commit()
        return job

    def delete_completed_jobs(self):
        stmt = select(JobQueueEntry).where(JobQueueEntry.state == 2)
        completed_jobs = self.session.exec(stmt).all()
        for job in completed_jobs:
            self.session.delete(job)
        self.session.commit()
