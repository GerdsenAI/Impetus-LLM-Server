"""
Unit tests for download manager service.
"""

from collections import namedtuple
from unittest.mock import patch

import pytest
from src.services.download_manager import DownloadManager, DownloadStatus, DownloadTask


class TestDownloadManager:
    """Tests for DownloadManager task lifecycle, disk space checks, and size estimation."""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a DownloadManager backed by a temporary directory."""
        with patch("src.services.download_manager.settings") as mock_settings:
            mock_settings.model.models_dir = tmp_path / "models"
            mgr = DownloadManager(models_dir=tmp_path / "models")
        return mgr

    # ── task creation ──────────────────────────────────────────────────

    def test_create_download_task(self, manager):
        """create_download_task returns a UUID string and the task starts in PENDING status."""
        task_id = manager.create_download_task("mlx-community/test-model-7B-4bit")
        assert isinstance(task_id, str)
        assert len(task_id) == 36  # UUID4 string length
        task = manager.tasks[task_id]
        assert task.status == DownloadStatus.PENDING
        assert task.model_id == "mlx-community/test-model-7B-4bit"

    # ── task status retrieval ──────────────────────────────────────────

    def test_get_task_status_exists(self, manager):
        """get_task_status returns a DownloadTask for a known task id."""
        task_id = manager.create_download_task("test/model")
        task = manager.get_task_status(task_id)
        assert isinstance(task, DownloadTask)
        assert task.task_id == task_id

    def test_get_task_status_not_found(self, manager):
        """get_task_status returns None for an unknown task id."""
        task = manager.get_task_status("nonexistent-id")
        assert task is None

    # ── list all tasks ─────────────────────────────────────────────────

    def test_get_all_tasks(self, manager):
        """get_all_tasks returns a copy of the internal dict, not the original."""
        tid1 = manager.create_download_task("model/a")
        tid2 = manager.create_download_task("model/b")
        all_tasks = manager.get_all_tasks()
        assert len(all_tasks) == 2
        assert tid1 in all_tasks
        assert tid2 in all_tasks
        # Must be a copy, not the same dict object
        assert all_tasks is not manager.tasks

    # ── cancellation ───────────────────────────────────────────────────

    def test_cancel_pending_task(self, manager):
        """Cancelling a PENDING task changes its status to CANCELLED and returns True."""
        task_id = manager.create_download_task("model/cancel-me")
        result = manager.cancel_download(task_id)
        assert result is True
        assert manager.tasks[task_id].status == DownloadStatus.CANCELLED

    def test_cancel_completed_task(self, manager):
        """Cancelling a COMPLETED task returns False — only PENDING/DOWNLOADING tasks are cancellable."""
        task_id = manager.create_download_task("model/done")
        manager.tasks[task_id].status = DownloadStatus.COMPLETED
        result = manager.cancel_download(task_id)
        assert result is False
        assert manager.tasks[task_id].status == DownloadStatus.COMPLETED

    def test_cancel_nonexistent_task(self, manager):
        """Cancelling a task id that does not exist returns False."""
        result = manager.cancel_download("no-such-task")
        assert result is False

    def test_cancel_failed_task(self, manager):
        """Cancelling a FAILED task returns False."""
        task_id = manager.create_download_task("model/failed")
        manager.tasks[task_id].status = DownloadStatus.FAILED
        result = manager.cancel_download(task_id)
        assert result is False

    # ── disk space ─────────────────────────────────────────────────────

    def test_check_disk_space_sufficient(self, manager):
        """check_disk_space returns (True, available_gb) when free space exceeds 1.2x the required amount."""
        DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
        free_bytes = 20 * 1024**3  # 20 GB free
        with patch("shutil.disk_usage", return_value=DiskUsage(total=0, used=0, free=free_bytes)):
            has_space, available_gb = manager.check_disk_space(required_gb=10.0)
        assert has_space is True
        assert available_gb == pytest.approx(20.0, abs=0.1)

    def test_check_disk_space_insufficient(self, manager):
        """check_disk_space returns (False, available_gb) when free space is below 1.2x the required amount."""
        DiskUsage = namedtuple("DiskUsage", ["total", "used", "free"])
        free_bytes = 5 * 1024**3  # 5 GB free
        with patch("shutil.disk_usage", return_value=DiskUsage(total=0, used=0, free=free_bytes)):
            has_space, available_gb = manager.check_disk_space(required_gb=10.0)
        assert has_space is False
        assert available_gb == pytest.approx(5.0, abs=0.1)

    # ── download size estimation ───────────────────────────────────────

    def test_get_download_size_7b(self, manager):
        """A model id containing '7B' and '4bit' estimates 4.0 GB."""
        size = manager.get_download_size("mlx-community/model-7B-4bit")
        assert size == 4.0

    def test_get_download_size_3b(self, manager):
        """A model id containing '3b' and '4bit' estimates 2.0 GB."""
        size = manager.get_download_size("mlx-community/model-3b-4bit")
        assert size == 2.0

    def test_get_download_size_8b(self, manager):
        """A model id containing '8B' and '4bit' estimates 4.5 GB."""
        size = manager.get_download_size("mlx-community/Llama-3.2-8B-Instruct-4bit")
        assert size == 4.5

    def test_get_download_size_unknown(self, manager):
        """A model id without a recognized size pattern defaults to 5.0 GB."""
        size = manager.get_download_size("mlx-community/some-custom-model")
        assert size == 5.0


    # ── download size estimation (additional variants) ─────────────────

    def test_get_download_size_9b(self, manager):
        """A model id containing '9B' estimates 5.2 GB for 4bit."""
        size = manager.get_download_size("mlx-community/model-9B-4bit")
        assert size == 5.2

    def test_get_download_size_9b_full(self, manager):
        """A model id containing '9B' without 4bit estimates 10.5 GB."""
        size = manager.get_download_size("mlx-community/model-9B")
        assert size == 10.5

    def test_get_download_size_3b_full(self, manager):
        """A model id containing '3B' without 4bit estimates 4.0 GB."""
        size = manager.get_download_size("mlx-community/model-3B")
        assert size == 4.0

    def test_get_download_size_7b_full(self, manager):
        """A model id containing '7B' without 4bit estimates 8.0 GB."""
        size = manager.get_download_size("mlx-community/model-7B")
        assert size == 8.0

    def test_get_download_size_8b_full(self, manager):
        """A model id containing '8B' without 4bit estimates 9.0 GB."""
        size = manager.get_download_size("mlx-community/model-8B")
        assert size == 9.0

    # ── progress callback registration ─────────────────────────────────

    def test_register_progress_callback(self, manager):
        """register_progress_callback stores the callback."""
        task_id = manager.create_download_task("model/test")
        cb = lambda p: None  # noqa: E731
        manager.register_progress_callback(task_id, cb)
        assert manager.progress_callbacks[task_id] is cb

    # ── cleanup_failed_downloads ───────────────────────────────────────

    def test_cleanup_removes_incomplete(self, manager, tmp_path):
        """cleanup_failed_downloads removes dirs without config.json."""
        incomplete = manager.downloads_dir / "incomplete-model"
        incomplete.mkdir(parents=True)
        (incomplete / "partial.bin").write_bytes(b"\x00" * 10)

        manager.cleanup_failed_downloads()
        assert not incomplete.exists()

    def test_cleanup_keeps_complete(self, manager, tmp_path):
        """cleanup_failed_downloads keeps dirs with config.json."""
        complete = manager.downloads_dir / "complete-model"
        complete.mkdir(parents=True)
        (complete / "config.json").write_text("{}")

        manager.cleanup_failed_downloads()
        assert complete.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
