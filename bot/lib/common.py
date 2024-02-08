import discord
from ruamel.yaml import YAML

from bot import settings
from bot.lib.guild_configuration import GuildConfiguration


def is_owner(bot, member: discord.Member):
    """
    Check if a guild member is an "owner" for the bot
    :param bot: A bot instance
    :param member: The discord.Guild member.
    :return: A boolean value depending if the member is an owner or not.
    """
    if not isinstance(member, discord.Member):
        return False

    # The server owner or a user with the Administrator permission is an owner to the bot.
    if member.guild.owner == member or member.guild_permissions.administrator:
        return True

    # Check if the user has the owner role
    cfg = GuildConfiguration.get_instance(member.guild)
    owner_roles = cfg.get_list('owner_roles', [settings.owner_role])
    for role in member.roles:
        if str(role.id) in owner_roles \
                or role.name in owner_roles \
                or str(member.id) in owner_roles:
            return True

    return False


def is_pm(message):
    return isinstance(message, discord.DMChannel)


def is_bot_owner(member, bot):
    return member.id in settings.bot_owners


def yaml_config(name, defaults=None, raise_exception=False):
    file = settings.base_dir / 'config' / f'{name}.yml'
    yaml = YAML(typ='safe')
    try:
        with file.open() as f:
            yaml.load(f)
    except Exception:
        if raise_exception:
            raise
        return defaults
    return yaml
