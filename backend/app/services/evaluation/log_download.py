from io import BytesIO
from pathlib import Path
from time import time
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

from app.config.settings import settings


LOGS_NOT_AVAILABLE = (
    "Logs are not available. Log files are retained for "
    f"{settings.evaluation_log_retention_days} days and may have been removed."
)


def _archive_logs(paths: list[Path], root: Path) -> BytesIO:
    root_resolved = root.resolve()
    safe_paths = [
        path.resolve()
        for path in paths
        if path.resolve().is_relative_to(root_resolved) and path.is_file()
    ]
    if not safe_paths:
        raise FileNotFoundError(LOGS_NOT_AVAILABLE)

    archive_buffer = BytesIO()
    archived_count = 0
    with ZipFile(archive_buffer, mode="w", compression=ZIP_DEFLATED) as archive:
        for path in safe_paths:
            try:
                archive.write(path, arcname=str(path.relative_to(root_resolved)))
                archived_count += 1
            except OSError:
                continue

    if archived_count == 0:
        raise FileNotFoundError(LOGS_NOT_AVAILABLE)

    archive_buffer.seek(0)
    return archive_buffer


def _within_retention(paths: list[Path]) -> list[Path]:
    cutoff = time() - settings.evaluation_log_retention_days * 24 * 60 * 60
    recent_paths: list[Path] = []
    for path in paths:
        try:
            if path.stat().st_mtime >= cutoff:
                recent_paths.append(path)
        except OSError:
            continue
    return recent_paths


def _has_available_logs(paths: list[Path], root: Path) -> bool:
    root_resolved = root.resolve()
    for path in _within_retention(paths):
        try:
            resolved = path.resolve()
            if resolved.is_relative_to(root_resolved) and resolved.is_file():
                return True
        except OSError:
            continue
    return False


def evaluation_run_logs_available(run_id: UUID) -> bool:
    root = Path(settings.evaluation_log_directory)
    if not root.exists():
        return False
    return _has_available_logs(
        list(root.glob(f"worker-*/*_{run_id}.log")),
        root,
    )


def scheduler_logs_available() -> bool:
    root = Path(settings.evaluation_log_directory)
    if not root.exists():
        return False
    return _has_available_logs(list(root.glob("scheduler-*/*.log")), root)


def archive_evaluation_run_logs(run_id: UUID) -> BytesIO:
    root = Path(settings.evaluation_log_directory)
    if not root.exists():
        raise FileNotFoundError(LOGS_NOT_AVAILABLE)

    paths = sorted(
        _within_retention(list(root.glob(f"worker-*/*_{run_id}.log"))),
        key=lambda path: path.stat().st_mtime,
    )
    return _archive_logs(paths, root)


def archive_scheduler_logs() -> BytesIO:
    root = Path(settings.evaluation_log_directory)
    if not root.exists():
        raise FileNotFoundError(LOGS_NOT_AVAILABLE)

    paths = sorted(
        _within_retention(list(root.glob("scheduler-*/*.log"))),
        key=lambda path: path.stat().st_mtime,
    )
    return _archive_logs(paths, root)
