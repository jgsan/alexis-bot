import discord
from .. import bot


@bot.command(description='Responde al comando')
async def ping(interaction: discord.Interaction):
    msg_text = f'Hola, {interaction.user.mention}'
    await interaction.response.send_message(msg_text)
