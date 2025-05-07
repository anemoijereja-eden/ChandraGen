from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlmodel import Session, asc, desc, select

from chandragen.db import EntryNotFoundError, get_session
from chandragen.db.models.job_queue import JobQueueEntry, JobState


class JobQueueController:
    def __init__(self, session: Session | None = None):
        self.session = session or get_session()
    
    def get_jobs_by_name_and_state(self, jobname: str, state: JobState) -> list[UUID]:
        query = (
            select(JobQueueEntry)
            .where(JobQueueEntry.name == jobname)
            .where(JobQueueEntry.state == state)
            .order_by(desc(JobQueueEntry.priority), asc(JobQueueEntry.created_at))
            .limit(10)
        )
        jobs = self.session.exec(query).all()
        return [ job.id for job in jobs ]
        
    def claim_job(self, job_id: UUID, worker_id: UUID):
        entry = self.session.exec(
            select(JobQueueEntry)
            .where(JobQueueEntry.id == job_id)
        ).first()
        
        if entry is None:
            raise EntryNotFoundError(job_id)
        
        # Adds the worker UUID to the entry, and updates it in the db.
        entry.assigned_to = worker_id
        if entry.state == JobState.PENDING:
            entry.state = JobState.IN_PROGRESS
            entry.started_at = datetime.now(UTC)
        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
    
    def add_job(self, job: JobQueueEntry):
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def get_pending_jobs(self, limit: int = 10) -> Sequence[JobQueueEntry]:
        return self.session.exec( 
                select(JobQueueEntry)
                .where(JobQueueEntry.state == JobState.PENDING)
                .order_by(
                    desc(JobQueueEntry.priority),
                    asc(JobQueueEntry.created_at),
        ).limit(limit)).all()

    def mark_job_complete(self, job_id: int):
        job = self.session.get(JobQueueEntry, job_id)
        if job:
            job.state = JobState.COMPLETED
            self.session.commit()
        return job

    def mark_job_failed(self, job_id: int):
        job = self.session.get(JobQueueEntry, job_id)
        if job:
            job.state = JobState.FAILED
            self.session.commit()
        return job

    def delete_completed_jobs(self):
        completed_jobs = self.session.exec(
            select(JobQueueEntry)
            .where(JobQueueEntry.state == JobState.COMPLETED)
            ).all()
        for job in completed_jobs:
            self.session.delete(job)
        self.session.commit()
