import discord

from bot import Command, CommandEvent
from bot.utils import replace_everywhere, get_prefix


class LangFilter(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.priority = 10
        self.autolang_cache = {}
        self.name = 'resetlangs'
        self.help = '$[config-resetlangs-help]'
        self.bot_owner_only = True

    async def handle(self, cmd):
        self.autolang_cache = {}
        await cmd.answer('$[config-resetlangs-done]')

    def pre_send_message(self, kwargs):
        dest = kwargs.get('destination')
        svid = dest.server.id if hasattr(dest, 'server') else None

        lang = self.auto_lang(kwargs)
        if 'content' in kwargs and kwargs['content']:
            kwargs['content'] = lang.format(kwargs['content'], kwargs.get('locales', None))

        if kwargs.get('embed', None) is not None:
            kwargs['embed'] = lang.format(kwargs['embed'], kwargs.get('locales', None))

        if kwargs.get('event', None):
            kwargs['content'] = kwargs['content'].replace('$AU', kwargs['event'].author_name)
            kwargs['content'] = kwargs['content'].replace('$CMD', '$PX$NM')

            if kwargs['embed'] is not None:
                replace_everywhere(kwargs['embed'], '$CMD', '$PX$NM')
                replace_everywhere(kwargs['embed'], '$AU', kwargs['event'].author_name)

            if isinstance(kwargs['event'], CommandEvent):
                kwargs['content'] = kwargs['content'].replace('$NM', kwargs['event'].cmdname)

                if kwargs['embed'] is not None:
                    replace_everywhere(kwargs['embed'], '$NM', kwargs['event'].cmdname)

        prefix = get_prefix(self.bot, svid)

        if 'content' in kwargs and kwargs['content']:
            self.log.debug(kwargs['content'])
            kwargs['content'] = kwargs['content'].replace('$PX', prefix)
            kwargs['content'] = kwargs['content'].lstrip(prefix)

        if kwargs['embed'] is not None:
            replace_everywhere(kwargs['embed'], '$PX', prefix)

    def auto_lang(self, kwargs):
        """
        Automatically determine which language will be used on a message, given a message kwargs, and determined
        if the destination is a guild, a guild member, or a user (message sent via PM). If the message is sent
        to a user via PM, then the language will be determined by the guilds in common between the bot and the user,
        and the most used language will be used.
        :param kwargs: The kwargs of the send_message method
        :return: A `bot.libs.language.SingleLanguage` instance with the determined language set.
        """

        destination = kwargs.get('destination')

        # If the destination is a discord.Channel or a discord.Member
        # (or any other destination instance that has the 'server' attribute)
        if hasattr(destination, 'server'):
            return self.get_lang(destination.server.id, destination)

        # If the destination is a user
        elif isinstance(destination, discord.channel.PrivateChannel):
            # The event could've been triggered from a guild, so use its language
            if hasattr(kwargs, 'event') and not kwargs['event'].is_pm:
                return self.get_lang(kwargs['event'].server, kwargs['event'].channel)

            user = destination.owner if destination.type == discord.ChannelType.group else destination.user
            if user.id in self.autolang_cache:
                return self.get_lang(self.autolang_cache[user.id])

            # Fetch common guilds between the user and the bot, and get the guilds languages.
            langs = [
                self.bot.sv_config.get(sv.id, 'lang', self.bot.config['default_lang'])
                for sv in self.bot.servers if sv.get_member(user.id) is not None
            ]

            # If there are no common guilds, just use the default language
            # (but it's kinda rare to talk to a bot that you don't have any guild in common, right?)
            if len(langs) == 0:
                return self.get_lang()

            # Get the mode language from the common user-bot guilds and use it.
            mode_lang = max(set(langs), key=langs.count)
            self.autolang_cache[user.id] = mode_lang
            self.log.debug('Language automatically set to %s for user "%s"', mode_lang, str(user))

            return self.get_lang(mode_lang)

        # Return the default language
        else:
            self.log.debug('Using default language')
            return self.get_lang()

