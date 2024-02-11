from typing import Self
import platform
import sys
import inspect
import importlib
from datetime import datetime

import asyncio
import discord
from discord.app_commands import CommandTree

from bot import constants, settings, modules
from bot.database import BotDatabase
from .lib import GuildConfiguration, Language
from .lib.common import is_pm
from bot.logger import new_logger
from bot.utils import auto_int

log = new_logger('Core')


class AlexisBot(discord.Client):
    __author__ = 'makzk (github.com/jkcgs)'
    __license__ = 'MIT'
    __version__ = '2.0.0-dev'
    name = 'AlexisBot'

    def __init__(self, **options):
        """
        Initializes configuration, logging, an aiohttp session and class attributes.
        :param options: The discord.Client options
        """
        u_options = dict(chunk_guilds_at_startup=settings.chunk_guilds, **options)
        intents = discord.Intents.default()
        intents.members = True
        intents.guild_messages = True
        intents.dm_messages = True
        intents.message_content = True
        super().__init__(**u_options, intents=intents)

        self.db = None
        self.tasks_loop = asyncio.new_event_loop()
        self.initialized = False
        self.start_time = datetime.now()
        self.connect_delta = None

        self.lang = {}
        self.deleted_messages = []
        self.deleted_messages_nolog = []

        self.tree = CommandTree(self)

        self.cmds = {}
        self.tasks = {}
        self.swhandlers = {}
        self.cmd_instances = []
        self.mention_handlers = []

        #headers = {'User-Agent': '{}/{} (https://alexisbot.mak.wtf/)'.format(self.__class__.name, self.__class__.__version__)}
        #self.http = aiohttp.ClientSession(headers=headers, cookie_jar=aiohttp.CookieJar(unsafe=True))

        # Dinamically create and override bot event handler methods
        from bot.constants import EVENT_HANDLERS
        for method, margs in EVENT_HANDLERS.items():
            def make_handler(event_name, event_args):
                async def dispatch(*args):
                    kwargs = dict(zip(event_args, args))
                    await self.dispatch_event(event_name=event_name, **kwargs)

                return dispatch

            event = 'on_' + method
            setattr(self, event, make_handler(event, margs.copy()))

    async def setup_hook(self):
        for guild_id in [i.strip() for i in settings.command_guilds if i.strip()]:
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            log.info('Commands loaded to guild ID %s', guild_id)

    def init(self):
        """
        Loads configuration, connects to database, and then connects to Discord.
        """
        log.info('%s v%s, discord.py v%s', AlexisBot.name, AlexisBot.__version__, discord.__version__)
        log.info('Python %s in %s.', sys.version.replace('\n', ''), sys.platform)
        log.info(platform.uname())
        log.info('Bot root path: %s', constants.bot_root)
        log.info('------')

        # Load configuration
        if not settings.discord_token:
            raise RuntimeError('Discord bot token not defined in settings.')

        # Load languages
        self.load_language()

        # Load database
        log.info('Connecting to the database...')
        self.db = BotDatabase()
        GuildConfiguration.create_table(self.db)
        log.info('Successfully conected to database using %s', self.db.__class__.__name__)

        # Load command classes and instances from bots.modules
        log.info('Loading commands...')
        self.load_instances()
        self.dispatch_sync('on_loaded', force=True)

        # Connect to Discord
        try:
            self.start_time = datetime.now()
            chunking_info = ' (load guild chunks enabled!)' if settings.chunk_guilds else ''
            log.info('Connecting to Discord{}...'.format(chunking_info))
            self.run(settings.discord_token)
        except discord.errors.LoginFailure:
            log.error('Invalid Discord token!')
            raise

    async def on_ready(self):
        """ This is executed once the bot has successfully connected to Discord. """
        self.connect_delta = (datetime.now() - self.start_time).total_seconds()
        log.info('Connected as "%s" (%s)', self.user.name, self.user.id)
        log.info('It took %.3f seconds to connect.', self.connect_delta)
        log.info('------')

        self.initialized = True
        self.create_tasks()
        await self.dispatch_event('on_ready')

    def load_language(self):
        """
        Loads language content
        :return: A boolean depending on the operation's result.
        """
        try:
            log.info('Loading language stuff...')

            self.lang = Language('lang', default=settings.default_language, autoload=True)
            log.info('Loaded languages: %s, default: %s', list(self.lang.lib.keys()), settings.default_language)
            return True
        except Exception as ex:
            log.exception(ex)
            return False

    async def close(self):
        """
        Stops tasks, close connections and logout from Discord.
        :return:
        """
        log.debug('Closing stuff...')
        await super().close()

        # Stop tasks
        self.cancel_tasks()

    async def send_modlog(self, guild: discord.Guild, message=None, embed: discord.Embed = None,
                          locales=None, logtype=None):
        """
        Sends a message to the modlog channel of a guild, if modlog channel is set, and if the
        logtype is enabled.
        :param guild: The guild to send the modlog message.
        :param message: The message content.
        :param embed: An embed for the message.
        :param locales: Locale variables for language messages.
        :param logtype: The modlog type of the message. Guilds can disable individual modlog types.
        """
        config = GuildConfiguration.get_instance(guild)
        chanid = config.get('join_send_channel')
        if chanid == '':
            return

        if logtype and logtype in config.get_list('logtype_disabled'):
            return

        chan = self.get_channel(auto_int(chanid))
        if chan is None:
            return

        await self.send_message(chan, content=message, embed=embed, locales=locales)

    async def send_message(self, destination, content='', **kwargs):
        """
        Method that proxies all messages sent to Discord, to fire other calls
        like event handlers, message filters and bot logging. Allows original method's parameters.
        :param destination: Where to send the message, must be a discord.abc.Messageable compatible instance.
        :param content: The content of the message to send.
        :return: The message sent
        """

        kwargs['content'] = content
        if not isinstance(destination, discord.abc.Messageable):
            raise RuntimeError('destination must be a discord.abc.Messageable compatible instance')

        # Call pre_send_message handlers, append destination
        self.dispatch_ref('pre_send_message', kwargs)

        # Log the message
        if isinstance(destination, discord.TextChannel):
            destination_repr = '{}#{} (IDS {}#{})'.format(
                destination.guild, str(destination), destination.id, destination.guild.id)
        else:
            destination_repr = str(destination)

        msg = 'Sending message "{}" to {} '.format(kwargs['content'], destination_repr)
        if isinstance(kwargs.get('embed', None), discord.Embed):
            msg += ' (with embed: {})'.format(kwargs.get('embed').to_dict())
        log.debug(msg)

        # Send the actual message
        if 'locales' in kwargs:
            del kwargs['locales']
        if 'event' in kwargs:
            del kwargs['event']

        return await destination.send(**kwargs)

    async def delete_message(self, message, silent=False):
        """
        Deletes a message and registers the last 50 messages' IDs.
        :param message: The message to delete
        :param silent: Add the message to the no-log list
        """
        if not isinstance(message, discord.Message):
            raise RuntimeError('message must be a discord.Message instance')

        self.deleted_messages.append(message.id)
        if silent:
            self.deleted_messages_nolog.append(message.id)

        try:
            await message.delete()
        except discord.Forbidden as e:
            del self.deleted_messages[-1]
            if silent:
                del self.deleted_messages_nolog[-1]
            raise e

        if len(self.deleted_messages) > 50:
            del self.deleted_messages[0]
        if len(self.deleted_messages_nolog) > 50:
            del self.deleted_messages_nolog[0]

    def command(self, *args, coro=None, **kwargs):
        wrapper = self.command_handler(*args, **kwargs)

        if coro:
            wrapper(coro)
        else:
            return wrapper

    @property
    def uptime(self):
        return datetime.now() - self.start_time


    _instance = None
    def __new__(cls) -> Self:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


    def load_instances(self):
        """Loads instances for the command classes loaded"""
        self.cmd_instances = []
        for c in self.get_mods():
            self.cmd_instances.append(self.load_module(c))
        self.sort_instances()

        log.info('%i modules were loaded', len(self.cmd_instances))
        log.debug('Commands loaded: ' + ', '.join(self.cmds.keys()))
        log.debug('Modules loaded: ' + ', '.join([i.__class__.__name__ for i in self.cmd_instances]))

    def unload_instance(self, name):
        """
        Removes from memory a module instance, and disabling its commands and event handlers.
        :param name: Module's name.
        """
        instance = None
        for i in self.cmd_instances:
            if i.__class__.__name__ == name:
                instance = i

        if instance is None:
            return

        log.debug('Disabling %s module...', name)

        # Unload commands
        cmd_names = [n for n in [instance.name] + instance.aliases if n != '']
        for cmd_name in cmd_names:
            if cmd_name not in self.cmds:
                continue
            else:
                del self.cmds[cmd_name]

        # Unload startswith handlers
        for swname in instance.swhandler:
            if swname not in self.swhandlers:
                continue
            else:
                del self.swhandlers[swname]

        # Unload mention handlers
        for mhandler in self.mention_handlers:
            if mhandler.__class__.__name__ == name:
                self.mention_handlers.remove(mhandler)

        # Hackily unload task
        for task_name in [str(k) for k in self.tasks.keys()]:
            if task_name.startswith(name+'.'):
                log.debug('Cancelling task %s', task_name)
                self.tasks[task_name].cancel()
                del self.tasks[task_name]

        # Remove from instances list
        self.cmd_instances.remove(instance)
        log.info('"%s" module disabled', name)

    def sort_instances(self):
        self.cmd_instances = sorted(self.cmd_instances, key=lambda i: i.priority)

    def load_module(self, cls):
        """
        Loads a command module into the bot
        :param cls: The module class to load
        :return: A module class' instance
        """

        instance = cls(self)
        db_models = getattr(cls, 'db_models', [])
        if len(db_models) > 0:
            self.db.db.create_tables(db_models, safe=True)

        # Commands
        for name in [instance.name] + instance.aliases:
            if name != '':
                self.cmds[name] = instance

        # Startswith handlers
        for swtext in instance.swhandler:
            if swtext != '':
                log.debug('Registering starts-with handler "%s"', swtext)
                self.swhandlers[swtext] = instance

        # Commands activated with mentions
        if isinstance(instance.mention_handler, bool) and instance.mention_handler:
            self.mention_handlers.append(instance)

        if self.user:
            self.create_tasks(instance)

        return instance

    def create_tasks(self, instance=None):
        instances = self.cmd_instances if instance is None else [instance]

        for instance in instances:
            # Scheduled (repetitive) tasks
            if isinstance(instance.schedule, list):
                for (task, seconds) in instance.schedule:
                    self.schedule(task, seconds)
            elif isinstance(instance.schedule, tuple):
                task, seconds = instance.schedule
                self.schedule(task, seconds)

    async def run_task(self, task, time=0):
        """
        Runs a task on a given interval
        :param task: The task function
        :param time: The time in seconds to repeat the task
        """
        while 1:
            try:
                # log.debug('Running task %s', repr(task))
                await task()
            except Exception as e:
                log.exception(e)

    def schedule(self, task, time=0, force=False):
        """
        Adds a task to the loop to be run every *time* seconds.
        :param task: The task function
        :param time: The time in seconds to repeat the task
        :param force: What to do if the task was already created. If True, the task is cancelled and created again.
        """
        if time < 0:
            raise RuntimeError('Task interval time must be positive')

        task_name = '{}.{}'.format(task.__self__.__class__.__name__, task.__name__)
        if task_name in self.tasks:
            if not force:
                return
            self.tasks[task_name].cancel()

        task_ins = self.tasks_loop.create_task(self.run_task(task, time))
        self.tasks[task_name] = task_ins

        if time > 0:
            log.debug('Task "%s" created, repeating every %i seconds', task_name, time)
        else:
            log.debug('Task "%s" created, running once', task_name)

        return task_ins

    def get_handlers(self, name):
        return [getattr(c, name, None) for c in self.cmd_instances if callable(getattr(c, name, None))]

    async def dispatch_event(self, event_name, **kwargs):
        """
        Calls event methods on loaded methods.
        :param event_name: Event handler name
        :param kwargs: Event parameters
        """
        if not self.initialized:
            return

        message = kwargs.get('message', None)

        for x in self.get_handlers('pre_' + event_name):
            y = await x(**kwargs)

            if y is not None and isinstance(y, bool) and not y:
                return

        if event_name == 'on_message':
            # Log PMs
            if is_pm(message) and message.content != '':
                if message.author.id == self.user.id:
                    log.info('[PM] (-> %s): %s', message.channel.recipient, message.content)
                else:
                    log.info('[PM] (<- %s): %s', message.author, message.content)

        for z in self.get_handlers(event_name):
            await z(**kwargs)

    def dispatch_sync(self, name, force=False, **kwargs):
        """
        Synchronously (without event loop) calls "handlers" methods on loaded modules.
        :param name: Handler name
        :param force: Call handlers even if the bot is not initialized
        :param kwargs: Event parameters
        """
        if not self.initialized and not force:
            return

        for z in self.get_handlers(name):
            z(**kwargs)

    def dispatch_ref(self, name, kwargs):
        if not self.initialized:
            return

        for z in self.get_handlers(name):
            z(kwargs)

    def has_cmd(self, name):
        return name in self.cmds

    def get_cmd(self, name):
        return None if not self.has_cmd(name) else self.cmds[name]

    def get_mod(self, name):
        for i in self.cmd_instances:
            if i.__class__.__name__ == name:
                return i

        return None

    def has_mod(self, name):
        return self.get_mod(name) is not None

    def get_by_cmd(self, cmdname):
        for i in self.cmd_instances:
            if i.name == cmdname or cmdname in i.aliases:
                return i

        return None

    async def activate_mod(self, name):
        classes = self.get_mods()
        for cls in classes:
            if cls.__name__ == name:
                log.debug('Loading "%s" module...', name)
                ins = self.load_module(cls)
                if hasattr(ins, 'on_loaded'):
                    log.debug('Calling on_loaded for "%s"', name)
                    ins.on_loaded()
                if hasattr(ins, 'on_ready'):
                    log.debug('Calling on_ready for "%s"', name)
                    await ins.on_ready()

                self.cmd_instances.append(ins)
                self.sort_instances()
                log.debug('"%s" module loaded', name)
                return True

        return False

    def cancel_tasks(self):
        for task_name in list(self.tasks.keys()):
            self.tasks[task_name].cancel()
            del self.tasks[task_name]
        log.debug('All tasks cancelled.')

    def command_handler(self, *args, **kwargs):
        def wrapper(f):
            kwargs['name'] = kwargs.get('name', f.__qualname__)
            log.debug('Loading command: %s', kwargs['name'])
            async def handler(interaction: discord.Interaction):
                log.debug('Calling command %s', f)
                await f(interaction)
            return self.tree.command(*args, **kwargs)(handler)

        return wrapper

    @staticmethod
    def get_mods():
        from .command import Command
        classes = []
        bot_modules = ['bot.modules.' + x for x in modules.__all__]

        for imod in bot_modules:
            try:
                members = inspect.getmembers(importlib.import_module(imod))
                for name, clz in members:
                    if name == 'Command' or not inspect.isclass(clz) or not issubclass(clz, Command):
                        continue
                    classes.append(clz)
            except ImportError as e:
                log.error('Could not load a module')
                log.exception(e)
                continue
        return set(classes)
