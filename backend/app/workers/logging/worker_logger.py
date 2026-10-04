import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from app.config.settings import settings


class WorkerRunLogger:
    def __init__(
        self,
        worker_id: str,
        evaluation_run_id: UUID | str,
        message_id: str,
        log_type: str,
    ):
        if log_type not in {"execution", "retry"}:
            raise ValueError("log_type must be 'execution' or 'retry'.")

        self.worker_id = worker_id
        self.evaluation_run_id = str(evaluation_run_id)
        self.message_id = message_id
        self.log_type = log_type

        timestamp = datetime.now(timezone.utc)
        timestamp_text = timestamp.strftime("%Y%m%dT%H%M%SZ")

        log_directory = Path(settings.evaluation_log_directory) / f"worker-{worker_id}"
        log_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.log_path = log_directory / (
            f"{log_type}_{timestamp_text}_{message_id}_{self.evaluation_run_id}.log"
        )

        logger_name = (
            f"evaluation-worker.{worker_id}.{self.evaluation_run_id}.{message_id}.{log_type}"
        )

        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        self.handler = logging.FileHandler(
            self.log_path,
            encoding="utf-8",
        )

        formatter = logging.Formatter(
            "%(asctime)sZ | %(levelname)s | "
            f"worker-{worker_id} | "
            f"run={self.evaluation_run_id} | "
            f"message={message_id} | "
            f"{log_type} | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )

        formatter.converter = time.gmtime

        self.handler.setFormatter(formatter)
        self.logger.addHandler(self.handler)

        self.logger.info(f"{log_type} log created at {timestamp.isoformat()}")

    def info(self, message: str) -> None:
        self.logger.info(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

    def exception(self, message: str) -> None:
        self.logger.exception(message)

    def close(self) -> None:
        self.handler.flush()
        self.handler.close()
        self.logger.removeHandler(self.handler)
