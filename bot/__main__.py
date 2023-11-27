import asyncio

from bot import AlexisBot


def run():
    ale = None

    try:
        ale = AlexisBot()
        with ale:
            ale.init()
    except asyncio.CancelledError:
        pass
    except Exception:
        ale.manager.close_http()
        raise


if __name__ == '__main__':
    run()
