import discord
from discord import Embed
from discord.utils import escape_markdown, utcnow

from bot import Command, categories, utils, settings
from bot.utils import deltatime_to_str
from bot.modules.usernote import UserNoteCmd


class UserInfo(Command):
    __author__ = 'makzk'
    __version__ = '1.0.0'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'user'
        self.aliases = [settings.command_prefix + 'user']
        self.help = '$[modlog-cmd-help]'
        self.category = categories.INFORMATION

    async def handle(self, cmd):
        if cmd.cmdname == self.aliases[0] and not cmd.owner:
            return

        if cmd.argc == 0:
            user = cmd.author
        else:
            user = cmd.get_member_or_author(cmd.text)
            if user is None:
                await cmd.answer('$[user-not-found]')
                return

        with_more = cmd.cmdname == self.aliases[0] and cmd.owner
        embed = self.gen_embed(user, with_more)
        await cmd.answer('$[modlog-cmd-title]', embed=embed, locales={'user_id': user.id})

    @staticmethod
    def gen_embed(member: discord.Member, more=False):
        embed = Embed()
        embed.add_field(name='$[modlog-e-name]', value=escape_markdown(str(member)))
        embed.add_field(name='$[modlog-e-nick]', value=escape_markdown(member.nick) if member.nick is not None else '$[modlog-no-nick]')
        embed.add_field(name='$[modlog-e-user-created]', value=utils.format_date(member.created_at))
        embed.add_field(name='$[modlog-e-user-join]', value=utils.format_date(member.joined_at))
        embed.add_field(name='$[modlog-e-stance]',
                        value=utils.deltatime_to_str(utcnow() - member.joined_at), inline=False)
        embed.set_thumbnail(url=str(member.display_avatar.url))

        if more and isinstance(member, discord.Member):
            n = UserNoteCmd.get_note(member)
            embed.add_field(name='$[modlog-e-notes]', value=n if n != '' else '$[modlog-no-notes]')
            embed.add_field(name='$[modlog-e-age]', value=deltatime_to_str(member.joined_at - member.created_at))

        return embed
