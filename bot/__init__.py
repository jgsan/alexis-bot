#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .logger import new_logger
from .guild_configuration import GuildConfiguration
from .language import Language, SingleLanguage
from .events import MessageEvent, CommandEvent, BotMentionEvent
from .database import BotDatabase
from .command import Command
from .bot import AlexisBot

bot = AlexisBot()
log = new_logger('Sys')
