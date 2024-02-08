import asyncio

async def run():
    bot = AlexisBot.instance()
    async with bot:
        try:
            await bot.init()
        except asyncio.CancelledError:
            pass


if __name__ == '__main__':
    from .bot import AlexisBot
    from .commands import *
    asyncio.run(run())
