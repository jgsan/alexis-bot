from modules.base.command import Command


class Ping(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ping'
        self.help = 'Responde al comando *ping*'
        self.user_delay = 5

    async def handle(self, message, cmd):
        await cmd.answer('Pong!')
