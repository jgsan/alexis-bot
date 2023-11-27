import asyncio


async def run():
    from .bot import AlexisBot

    bot = AlexisBot.instance()
    async with bot:
        try:
            await bot.init()
        except asyncio.CancelledError:
            pass


if __name__ == '__main__':
    asyncio.run(run())
