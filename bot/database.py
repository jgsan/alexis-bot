import logging

from playhouse.db_url import connect

from bot import settings
from bot.logger import new_logger

peewee_log = new_logger('peewee')
peewee_log.setLevel(logging.INFO)


class BotDatabase:
    _ins = None

    def __new__(cls):
        if cls._ins is None:
            cls._ins = super().__new__(cls)
        return cls._ins

    def __init__(self):
        dburl = settings.database_url
        if dburl.startswith('mysql:'):
            dburl += '&amp;' if '?' in dburl else '?'
            dburl += 'charset=utf8mb4;'

        self.db = connect(dburl, autorollback=True)
