from typing import Optional
import discord

from bot.utils import img_embed
from .. import bot


@bot.command(description='Muestra un avatar')
async def avatar(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    if member is None:
        member = interaction.user

    ext_url = str(member.display_avatar.with_static_format('png'))
    text = 'Avatar' if bool(member.display_avatar.url) else 'Avatar predeterminado'
    embed = img_embed(str(member.display_avatar.url), text, '[Link externo]({})'.format(ext_url))
    await interaction.response.send_message(embed)
