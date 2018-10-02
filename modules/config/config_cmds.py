import sys

from discord import Game

from bot import Command, StaticConfig, categories
from bot.utils import is_float, is_int, split_list


class ConfigCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'config'
        self.help = '$[config-admin]'
        self.bot_owner_only = True
        self.category = categories.SETTINGS

    async def handle(self, cmd):
        if cmd.argc < 2 or (cmd.args[0] != 'get' and cmd.argc < 3):
            await cmd.answer('$[config-format]')
            return

        if cmd.subcmd == '':
            cfg = self.bot.config
        else:
            if not StaticConfig.exists(cmd.subcmd):
                await cmd.answer('$[config-not-exists]')
                return
            cfg = StaticConfig.get_config(cmd.subcmd)

        arg = cmd.args[0]
        name = cmd.args[1]

        if name not in cfg:
            await cmd.answer('$[config-value-not-exists]')
            return

        val = cfg[name]

        if arg == 'get':
            if name not in cfg:
                await cmd.answer('$[config-not-exists]')
                return

            if isinstance(val, list):
                if len(val) == 0:
                    await cmd.answer('$[config-empty-list]', locales={'list_name': name})
                else:
                    await cmd.answer('$[config-list-values]:', locales={'list_name': name})
                    items = ['- ' + str(f) for f in val]
                    for chunk in split_list(items, 1800):
                        cont = '\n'.join(chunk)
                        await cmd.answer('```{}```'.format(cont))
            else:
                await cmd.answer('$[config-value]', locales={'config_name': name, 'config_value': str(val)})
        elif arg == 'set':
            if isinstance(val, list):
                await cmd.answer('$[config-err-list]', locales={'list_name': name})
                return

            argvalue = ' '.join(cmd.args[2:])
            if isinstance(val, bool):
                if argvalue.lower() in ['0', 'false', 'no', 'disabled', 'off']:
                    argvalue = False
                elif argvalue.lower() in ['1', 'true', 'yes', 'enabled', 'on']:
                    argvalue = True
                else:
                    await cmd.answer('$[config-err-bool]', locales={'config_name': name})
                    return
            elif isinstance(val, float):
                if not is_float(argvalue):
                    await cmd.answer('$[config-err-float]', locales={'config_name': name})
                    return
                else:
                    argvalue = float(argvalue)
            elif isinstance(val, int):
                if not is_int(argvalue):
                    await cmd.answer('$[config-err-int]', locales={'config_name': name})
                    return
                else:
                    argvalue = int(argvalue)

            self.bot.config[name] = argvalue
            await cmd.answer('$[config-value-changed]', locales={'config_name': name})
        elif arg == 'add' or arg == 'remove':
            if not isinstance(val, list):
                await cmd.answer('$[config-err-not-list]', locales={'config_name': name})
                return

            argvalue = ' '.join(cmd.args[2:])
            if arg == 'add':
                if argvalue in val:
                    await cmd.answer('$[config-err-list-already]')
                    return

                val.append(argvalue)
                self.bot.config[name] = val
                await cmd.answer('$[config-list-added]')
                return
            elif arg == 'remove':
                if argvalue not in val:
                    await cmd.answer('$[config-list-not-in]')
                    return

                val.remove(argvalue)
                self.bot.config[name] = val
                await cmd.answer('$[config-list-removed]')
                return
        else:
            await cmd.answer('$[config-err-sub]')


class ReloadCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'reload'
        self.help = '$[config-reload-help]'
        self.bot_owner_only = True
        self.category = categories.SETTINGS

    async def handle(self, cmd):
        if not self.bot.load_config():
            await cmd.answer('$[config-reload-err]')
            return

        nmods = len([i.load_config() for i in self.bot.manager.cmd_instances if callable(getattr(i, 'load_config', None))])
        await cmd.answer('$[config-reloaded]', locales={'rel_mods': nmods})


class ShutdownCmd(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'shutdown'
        self.help = '$[config-shutdown-help]'
        self.bot_owner_only = True
        self.category = categories.SETTINGS

    async def handle(self, cmd):
        self.bot.config['shutdown_channel'] = cmd.message.channel.id
        await cmd.answer('$[config-goodbye]')
        await self.bot.logout()
        sys.exit(0)

    async def on_ready(self):
        if self.bot.config.get('shutdown_channel', '') != '':
            chan = self.bot.get_channel(self.bot.config['shutdown_channel'])
            if chan is None:
                return

            await self.bot.send_message(chan, '$[config-back]')
            self.bot.config['shutdown_channel'] = ''


class SetStatus(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'status'
        self.help = '$[config-status-help]'
        self.bot_owner_only = True
        self.category = categories.SETTINGS

    async def handle(self, cmd):
        status = '' if len(cmd.args) < 1 else cmd.text
        await self.bot.change_presence(game=Game(name=status))
        await cmd.answer('$[config-status-ok]')
