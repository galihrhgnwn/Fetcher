"""
SSE Service — manages per-job subscriber queues for Server-Sent Events.
"""
from __future__ import annotations
import asyncio
import json
from typing import Optional
from backend.models import JobStatus, SSEEvent


class SSEService:
    def __init__(self):
        # job_id → list of asyncio.Queue
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    def subscribe(self, job_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.setdefault(job_id, []).append(q)
        return q

    def unsubscribe(self, job_id: str, queue: asyncio.Queue):
        subs = self._subscribers.get(job_id, [])
        if queue in subs:
            subs.remove(queue)
        if not subs:
            self._subscribers.pop(job_id, None)

    async def broadcast(self, job_id: str, event: SSEEvent):
        """Send an SSE event to all subscribers of a job."""
        payload = event.model_dump_json()
        for q in list(self._subscribers.get(job_id, [])):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass  # slow consumer — drop event

    async def close(self, job_id: str):
        """Send terminal sentinel (None) to all subscribers."""
        for q in list(self._subscribers.get(job_id, [])):
            try:
                q.put_nowait(None)
            except asyncio.QueueFull:
                pass


# Singleton
sse_service = SSEService()
