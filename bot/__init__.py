#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .bot import AlexisBot
from .events import CommandEvent, MessageEvent, BotMentionEvent
from .database import BaseModel
from .lib.language import Language, SingleLanguage
from .command import Command

bot = AlexisBot.instance()
