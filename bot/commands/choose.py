import random

import discord
from discord import app_commands
from .. import bot


@bot.command(description='Elige un elemento al azar')
@app_commands.describe(value='Un listado de valores separados por espacio o por "|" (pipe).')
async def choose(interaction: discord.Interaction, value: str):
    separator = '|' if '|' in value else ' '
    options = [o.strip() for o in value.split(separator) if o.strip() != '']

    # At least 2 options are required
    if len(options) < 2:
        await interaction.response.send_message(
            'Debes ingresar al menos dos elementos',
            ephemeral=True, delete_after=15
        )
        return

    # Choose an option and send it
    answer = random.choice(options).strip()
    await interaction.response.send_message(f'Resultado: {answer}')
