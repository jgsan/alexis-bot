from logging import Logger
from datetime import datetime

start_time = datetime.now()


def new_logger(name: str) -> Logger:
    from bot import settings
    from bot.lib.logger import create_logger
    log_path = None if not settings.log_to_file else settings.log_path
    newlog = create_logger(name, settings.log_format, log_path, start_time)
    return newlog
