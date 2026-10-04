from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.workers.logging.log_cleanup import cleanup_old_logs


def test_cleanup_old_logs_deletes_files_older_than_retention(
    tmp_path: Path,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.workers.logging.log_cleanup.settings.evaluation_log_directory",
        str(tmp_path),
    )

    monkeypatch.setattr(
        "app.workers.logging.log_cleanup.settings.evaluation_log_retention_days",
        3,
    )

    old_log = tmp_path / "worker-old" / "execution_old.log"
    old_log.parent.mkdir(parents=True)
    old_log.write_text("old")

    recent_log = tmp_path / "scheduler-recent" / "scheduler_recent.log"
    recent_log.parent.mkdir(parents=True)
    recent_log.write_text("recent")

    old_timestamp = (datetime.now(UTC) - timedelta(days=4)).timestamp()

    old_log.touch()
    old_log.stat()

    import os

    os.utime(
        old_log,
        (old_timestamp, old_timestamp),
    )

    deleted_count = cleanup_old_logs()

    assert deleted_count == 1
    assert not old_log.exists()
    assert recent_log.exists()


def test_cleanup_old_logs_returns_zero_when_directory_does_not_exist(
    tmp_path: Path,
    monkeypatch,
):
    missing_directory = tmp_path / "missing"

    monkeypatch.setattr(
        "app.workers.logging.log_cleanup.settings.evaluation_log_directory",
        str(missing_directory),
    )

    assert cleanup_old_logs() == 0
