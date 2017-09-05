from modules.base.command import Command
import urllib.parse as urlparse


class AltoEn(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'altoen'
        self.help = 'Muestra una imagen basada en el logo "ALTO EN"'

    async def handle(self, message, cmd):
        if len(cmd.args) < 1:
            await cmd.answer('Formato: !altoen <str>')
            return

        altotext = ' '.join(cmd.args)
        if len(altotext) > 25:
            await cmd.answer('mucho texto, máximo 25 carácteres plix ty')
            return

        altourl = "https://desu.cl/alto.php?size=1000&text=" + urlparse.quote(altotext)
        await self.bot.send_message(message.channel, embed=Command.img_embed(altourl))
