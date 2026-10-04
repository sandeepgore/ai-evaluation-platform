from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.config.settings import settings


def cleanup_old_logs() -> int:
    """
    Delete log files older than the configured retention period.

    Returns:
        Number of log files deleted.
    """
    log_directory = Path(settings.evaluation_log_directory)

    if not log_directory.exists():
        return 0

    cutoff = datetime.now(UTC) - timedelta(
        days=settings.evaluation_log_retention_days,
    )

    deleted_count = 0

    for log_path in log_directory.rglob("*.log"):
        if not log_path.is_file():
            continue

        modified_at = datetime.fromtimestamp(
            log_path.stat().st_mtime,
            tz=UTC,
        )

        if modified_at >= cutoff:
            continue

        try:
            log_path.unlink()
            deleted_count += 1
        except OSError:
            # A currently open log file may not be deletable on some
            # platforms. Leave it for the next cleanup cycle.
            continue

    return deleted_count
