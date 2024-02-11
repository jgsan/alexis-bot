import itertools
import peewee
from bot.database import BotDatabase
from bot import bot


def run():
    print('Loading models...')
    models = [
        x for x in itertools.chain.from_iterable(
            cls.db_models for cls in [
                cls for cls in bot.get_mods() if len(getattr(cls, 'db_models', [])) > 0
            ]
        ) if issubclass(x, peewee.Model)
    ]

    print('Models loaded ({}):'.format(len(models)), models)
    print('Creating tables...')
    BotDatabase().create_tables(models)
    print('Tables created!')


if __name__ == '__main__':
    run()
