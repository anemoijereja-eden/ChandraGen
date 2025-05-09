from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlmodel import Session, asc, desc, func, select

from chandragen.db import EntryNotFoundError, get_session
from chandragen.db.models.job_queue import JobQueueEntry, JobState


#TODO: add logic to set up runner from database using job uuid
class JobQueueController:
    def __init__(self, session: Session | None = None):
        self.session = session or get_session()
    
    def get_job_by_id(self, job_id: UUID) -> JobQueueEntry:
        entry = self.session.exec(
            select(JobQueueEntry)
            .where(JobQueueEntry.id == job_id)
        ).first()
        if entry is not None:
            return entry
        raise EntryNotFoundError(job_id)
    
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
    
    def claim_next_pending_job(self, worker_id: UUID) -> tuple[UUID, str] | None: # returns job UUID
        job = self.session.exec(
            select(JobQueueEntry)
            .where(JobQueueEntry.state == JobState.PENDING)
            .order_by(
                desc(JobQueueEntry.priority),
                asc(JobQueueEntry.created_at),
            )
            .with_for_update(skip_locked=True)
            ).first()
        if job:
            job.state = JobState.IN_PROGRESS
            job.claimed_by = worker_id
            job.started_at = datetime.now(UTC)
            self.session.add(job)
            self.session.commit()
            self.session.refresh(job)
            return job.id, job.job_type
        return None
         
    def get_queue_status(self) -> tuple[int, int, float]: # pending jobs, in-progress jobs, percentage of incomplete jobs that are pending
        pending_count = self.session.exec(
            select(func.count())
            .where(JobQueueEntry.state == JobState.PENDING)
        ).one()
        in_progress_count = self.session.exec(
            select(func.count())
            .where(JobQueueEntry.state == JobState.IN_PROGRESS)
        ).one()
        
        total = pending_count + in_progress_count
        ratio: float = (pending_count / total) if total > 0 else 0.0
        
        return pending_count, in_progress_count, ratio
        
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

    def mark_job_complete(self, job_id: UUID):
        job = self.session.get(JobQueueEntry, job_id)
        if job:
            job.state = JobState.COMPLETED
            self.session.commit()
        return job

    def mark_job_failed(self, job_id: UUID):
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