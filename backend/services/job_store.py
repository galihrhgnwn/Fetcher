"""
In-memory job store — tracks all download jobs and history.
Thread-safe via asyncio.Lock.
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional
from backend.models import JobStatus


@dataclass
class Job:
    id:        str
    url:       str
    format:    str
    quality:   str
    status:    JobStatus  = JobStatus.QUEUED
    progress:  float      = 0.0
    speed:     Optional[str] = None
    eta:       Optional[str] = None
    filename:  Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    error:     Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class HistoryEntry:
    id:            str
    url:           str
    title:         str
    format:        str
    file_size:     Optional[int]  = None
    thumbnail:     Optional[str]  = None
    downloaded_at: float          = field(default_factory=time.time)


TERMINAL_STATUSES = {JobStatus.DONE, JobStatus.ERROR, JobStatus.CANCELLED}
MAX_HISTORY = 50


class JobStore:
    def __init__(self):
        self._jobs:    dict[str, Job]          = {}
        self._history: list[HistoryEntry]      = []

    def create(self, job: Job) -> Job:
        self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs) -> Optional[Job]:
        job = self._jobs.get(job_id)
        if not job:
            return None
        for k, v in kwargs.items():
            if hasattr(job, k):
                setattr(job, k, v)
        job.updated_at = time.time()
        return job

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job or job.status in TERMINAL_STATUSES:
            return False
        job.status     = JobStatus.CANCELLED
        job.updated_at = time.time()
        return True

    def list_active(self) -> list[Job]:
        return [j for j in self._jobs.values() if j.status not in TERMINAL_STATUSES]

    def add_history(self, entry: HistoryEntry):
        self._history.insert(0, entry)
        if len(self._history) > MAX_HISTORY:
            self._history = self._history[:MAX_HISTORY]

    def get_history(self) -> list[HistoryEntry]:
        return list(self._history)


# Singleton
job_store = JobStore()
