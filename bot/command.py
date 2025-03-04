from __future__ import annotations
from logging import Logger
import aiohttp

import discord

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bot.bot import AlexisBot

from bot import GuildConfiguration, CommandEvent, SingleLanguage, categories, settings
from .utils import lazy_property
from .logger import new_logger


class Command:
    __author__ = 'makzk'
    __version__ = '0.0.0'
    db_models = []

    def __init__(self, bot: AlexisBot):
        self.bot = bot
        self.name = ''  # Command name
        self.aliases = []  # Command aliases
        self.schedule = []
        self.swhandler = []
        self.swhandler_break = False
        self.mention_handler = False
        self.category = categories.OTHER
        self.allow_pm = True
        self.nsfw_only = False
        self.bot_owner_only = False
        self.owner_only = False
        self.default_enabled = True
        self.default_config = None
        self.priority = 100
        self.user_delay = 0
        self.users_delay = {}

        # Default messages and error messages
        self.help = '$[help-not-available]'
        self.pm_error = '$[disallowed-via-pm]'
        self.owner_error = '$[command-not-authorized]'
        self.format = '$[help-format-not-available]'
        self.user_delay_error = '$[command-delayed]'
        self.nsfw_only_error = '$[nsfw-only]'

    def handle(self, cmd: CommandEvent):
        raise AssertionError('handle method not implemented')

    def get_lang(self, guild=None, channel=None):
        """
        Creates a SingleLanguage instance for a specific server or server channel or default language.
        :param guild: The discord.Guild instance to get the language. If it's None, the default language is used.
        :param channel: The channel instance to get channel-specific language. If not set, the server language is used.
        :return: The SingleLanguage instance with the determined language.
        """
        lang_code = settings.default_language

        if isinstance(guild, discord.Guild):
            guildcfg = GuildConfiguration.get_instance(guild)
            lang_code = guildcfg.get('lang', settings.default_language)

            # Use channel language if the argument has been passed
            if isinstance(channel, discord.TextChannel):
                chanid = channel if not isinstance(channel, discord.TextChannel) else str(channel.id)
                lang_code = guildcfg.get('lang#' + chanid, lang_code)

        return SingleLanguage(self.bot.lang, lang_code)

    @classmethod
    def user_optout(cls, user):
        from .modules.userlog_optout import UserLogOptOut
        return UserLogOptOut.user_opted_out(user.id)

    @lazy_property
    def http(self):
        """
        Creates a http session instance with its own cookie storage and user-agent.
        :return: The http session instance.
        """
        headers = {'User-Agent': '{}/{} {}/{} (https://alexisbot.mak.wtf/)'.format(
            self.__class__.__name__, self.__class__.__version__,
            self.bot.__class__.name, self.bot.__class__.__version__)}

        return aiohttp.ClientSession(
            headers=headers, cookie_jar=aiohttp.CookieJar(unsafe=True)
        )

    @lazy_property
    def log(self) -> Logger:
        return new_logger(self.__class__.__name__)
