from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from loguru import logger
from sqlalchemy.exc import OperationalError, StatementError
from sqlmodel import Session, asc, desc, func, select, text

from chandragen.db import EntryNotFoundError, get_session
from chandragen.db.models.job_queue import JobQueueEntry, JobState


class JobQueueController:
    def __init__(self, session: Session | None = None):
        self.session = session or get_session()

    # wraps any db controller call, adds error handling!
    def _safe_run(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except (OperationalError, StatementError) as e:
            logger.error(f"database controller call {fn} failed, resetting session and retrying;\n{e}")
            self.session.rollback()
            self.session.close()
            self.session = get_session()
            # you can try once more after reset
            return fn(*args, **kwargs)

    def get_job_by_id(self, job_id: UUID) -> JobQueueEntry:
        entry = self.session.exec(select(JobQueueEntry).where(JobQueueEntry.id == job_id)).first()
        if entry is not None:
            return entry
        raise EntryNotFoundError(job_id)

    def increment_retries(self, job_id: UUID) -> int | None:
        job = self.session.exec(select(JobQueueEntry).where(JobQueueEntry.id == job_id)).first()
        if job:
            job.retries += 1
            self.session.add(job)
            self.session.commit()
            self.session.refresh(job)
            return job.retries
        return None

    def get_jobs_by_name_and_state(self, jobname: str, state: JobState) -> list[UUID]:
        query = (
            select(JobQueueEntry)
            .where(JobQueueEntry.name == jobname)
            .where(JobQueueEntry.state == state)
            .order_by(desc(JobQueueEntry.priority), asc(JobQueueEntry.created_at))
            .limit(10)
        )
        jobs = self.session.exec(query).all()
        return [job.id for job in jobs]

    def claim_next_pending_job(self, worker_id: UUID) -> tuple[UUID, str] | None:  # returns job UUID
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

    def get_queue_status(
        self,
    ) -> tuple[int, int, float]:  # pending jobs, in-progress jobs, percentage of incomplete jobs that are pending
        pending_count = self.session.exec(select(func.count()).where(JobQueueEntry.state == JobState.PENDING)).one()
        in_progress_count = self.session.exec(
            select(func.count()).where(JobQueueEntry.state == JobState.IN_PROGRESS)
        ).one()

        total = pending_count + in_progress_count
        ratio: float = (pending_count / total) if total > 0 else 0.0

        return pending_count, in_progress_count, ratio

    def add_job(self, job: JobQueueEntry):
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def add_job_list(self, joblist: list[JobQueueEntry]):
        self.session.add_all(joblist)
        self.session.commit()
        return joblist

    def get_pending_jobs(self, limit: int = 10) -> Sequence[JobQueueEntry]:
        def run():
            return self.session.exec(
                select(JobQueueEntry)
                .where(JobQueueEntry.state == JobState.PENDING)
                .order_by(
                    desc(JobQueueEntry.priority),
                    asc(JobQueueEntry.created_at),
                )
                .limit(limit)
            ).all()

        return self._safe_run(run)

    def get_job_claimed_by(self, worker_id: UUID) -> JobQueueEntry | None:
        return self.session.exec(select(JobQueueEntry).where(JobQueueEntry.claimed_by == worker_id)).first()

    def mark_job_pending(self, job_id: UUID):
        job = self.session.get(JobQueueEntry, job_id)
        if job:
            job.state = JobState.PENDING
            job.claimed_by = None
            self.session.add(job)
            self.session.commit()
            self.session.refresh(job)
        return job

    def mark_job_complete(self, job_id: UUID):
        job = self.session.get(JobQueueEntry, job_id)
        if job:
            job.state = JobState.COMPLETED
            self.session.add(job)
            self.session.commit()
            self.session.refresh(job)
        return job

    def mark_job_failed(self, job_id: UUID):
        job = self.session.get(JobQueueEntry, job_id)
        if job:
            job.state = JobState.FAILED
            self.session.add(job)
            self.session.commit()
            self.session.refresh(job)
        return job

    def delete_completed_jobs(self):
        completed_jobs = self.session.exec(select(JobQueueEntry).where(JobQueueEntry.state == JobState.COMPLETED)).all()
        for job in completed_jobs:
            self.session.delete(job)
        self.session.commit()

    def tune_autovacuum(self):
        sql = text("""
            ALTER TABLE job_queue SET (
                autovacuum_vacuum_scale_factor = 0.01,
                autovacuum_vacuum_threshold = 50,
                autovacuum_analyze_scale_factor = 0.05,
                autovacuum_analyze_threshold = 100
            );
        """)
        self.session.exec(sql)  # pyright: ignore
        self.session.commit()
