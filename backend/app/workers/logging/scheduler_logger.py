import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from app.config.settings import settings


class SchedulerLogger:
    def __init__(
        self,
        scheduler_id: str,
    ):
        self.scheduler_id = scheduler_id

        timestamp = datetime.now(timezone.utc)
        timestamp_text = timestamp.strftime("%Y%m%dT%H%M%SZ")

        log_directory = Path(settings.evaluation_log_directory) / f"scheduler-{scheduler_id}"

        log_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.log_path = log_directory / (f"scheduler_{timestamp_text}.log")

        logger_name = f"evaluation-scheduler.{scheduler_id}"

        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

        self.handler = logging.FileHandler(
            self.log_path,
            encoding="utf-8",
        )

        formatter = logging.Formatter(
            f"%(asctime)sZ | %(levelname)s | scheduler-{scheduler_id} | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )

        formatter.converter = time.gmtime

        self.handler.setFormatter(formatter)
        self.logger.addHandler(self.handler)

        self.logger.info(f"scheduler log created at {timestamp.isoformat()}")

    def info(self, message: str, *args: object) -> None:
        self.logger.info(message, *args)

    def warning(self, message: str, *args: object) -> None:
        self.logger.warning(message, *args)

    def error(self, message: str, *args: object) -> None:
        self.logger.error(message, *args)

    def exception(self, message: str, *args: object) -> None:
        self.logger.exception(message, *args)

    def close(self) -> None:
        self.handler.flush()
        self.handler.close()
        self.logger.removeHandler(self.handler)
