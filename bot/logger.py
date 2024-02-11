from typing import Optional
from datetime import datetime
import logging
from pathlib import Path

from bot.defaults import default_log_format, datetime_format, filename_format

start_time = datetime.now()


def create_logger(
        name: str,
        log_format: str = None,
        log_path: Optional[str | Path] = None,
        logtime: Optional[datetime] = None
    ) -> logging.Logger:

    log = logging.getLogger(name)
    if len(log.handlers) > 1:
        return log

    if log_format is None:
        log_format = default_log_format

    if not isinstance(log_path, Path):
        log_path = Path(log_path)

    formatter = logging.Formatter(log_format, datetime_format)

    if log_format is not None:
        log.setLevel(logging.DEBUG)
        stdout_logger = logging.StreamHandler()
        stdout_logger.setLevel(logging.DEBUG)
        stdout_logger.setFormatter(formatter)
        log.addHandler(stdout_logger)

    if log_path is not None:
        if log_path.is_file():
            raise ValueError('Invalid logging file path: is a file, not a directory.')

        if not log_path.exists():
            log_path.mkdir(parents=True)

        dt = datetime.now() if logtime is None else logtime
        filename = dt.strftime(filename_format) + '.log'
        file_logger = logging.FileHandler(log_path / filename, encoding='utf-8')
        file_logger.setLevel(logging.DEBUG)
        file_logger.setFormatter(formatter)
        log.addHandler(file_logger)

    return log


def new_logger(name: str) -> logging.Logger:
    from bot import settings
    log_path = None if not settings.log_to_file else settings.log_path
    newlog = create_logger(name, settings.log_format, log_path, start_time)
    return newlog
