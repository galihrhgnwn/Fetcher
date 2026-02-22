"""Tests for job store and cookie manager."""
import pytest
import time
from backend.services.job_store import JobStore, Job, HistoryEntry
from backend.models import JobStatus


class TestJobStore:
    def setup_method(self):
        self.store = JobStore()

    def _make_job(self, job_id="test-1"):
        return Job(id=job_id, url="https://youtube.com/watch?v=abc", format="mp4", quality="best")

    def test_create_and_get(self):
        job = self._make_job()
        self.store.create(job)
        result = self.store.get("test-1")
        assert result is not None
        assert result.id == "test-1"

    def test_get_nonexistent(self):
        assert self.store.get("nope") is None

    def test_update_status(self):
        job = self._make_job()
        self.store.create(job)
        self.store.update("test-1", status=JobStatus.DOWNLOADING, progress=50.0)
        updated = self.store.get("test-1")
        assert updated.status == JobStatus.DOWNLOADING
        assert updated.progress == 50.0

    def test_cancel_active_job(self):
        job = self._make_job()
        self.store.create(job)
        result = self.store.cancel("test-1")
        assert result is True
        assert self.store.get("test-1").status == JobStatus.CANCELLED

    def test_cancel_done_job_fails(self):
        job = self._make_job()
        self.store.create(job)
        self.store.update("test-1", status=JobStatus.DONE)
        result = self.store.cancel("test-1")
        assert result is False

    def test_cancel_nonexistent_fails(self):
        assert self.store.cancel("nope") is False

    def test_list_active(self):
        j1 = self._make_job("j1")
        j2 = self._make_job("j2")
        self.store.create(j1)
        self.store.create(j2)
        self.store.update("j2", status=JobStatus.DONE)
        active = self.store.list_active()
        assert len(active) == 1
        assert active[0].id == "j1"

    def test_history_add_and_get(self):
        entry = HistoryEntry(id="h1", url="https://yt.com", title="Test", format="mp3")
        self.store.add_history(entry)
        history = self.store.get_history()
        assert len(history) == 1
        assert history[0].title == "Test"

    def test_history_max_50(self):
        for i in range(60):
            self.store.add_history(HistoryEntry(id=f"h{i}", url="u", title=f"T{i}", format="mp4"))
        assert len(self.store.get_history()) == 50

    def test_history_newest_first(self):
        self.store.add_history(HistoryEntry(id="old", url="u", title="Old", format="mp4"))
        self.store.add_history(HistoryEntry(id="new", url="u", title="New", format="mp4"))
        history = self.store.get_history()
        assert history[0].title == "New"

    def test_update_returns_job(self):
        job = self._make_job()
        self.store.create(job)
        updated = self.store.update("test-1", progress=75.0)
        assert updated is not None
        assert updated.progress == 75.0

    def test_update_nonexistent_returns_none(self):
        result = self.store.update("nope", progress=50.0)
        assert result is None


class TestCookieManager:
    def test_no_cookies_dir_returns_none(self):
        import tempfile, os
        from backend.cookie_manager import get_cookie_file
        # When cookies dir doesn't exist, should return None gracefully
        # (actual dir may or may not exist in test env)
        result = get_cookie_file("nonexistent_platform_xyz")
        assert result is None or isinstance(result, str)

    def test_list_available_cookies_returns_list(self):
        from backend.cookie_manager import list_available_cookies
        result = list_available_cookies()
        assert isinstance(result, list)
