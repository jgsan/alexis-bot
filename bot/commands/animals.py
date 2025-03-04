from typing import Union
import aiohttp
import discord
from .. import bot, log


cmd_settings = {
    'cat': ['https://cataas.com/cat?json=true', 'gato', '_id'],
    'dog': ['https://dog.ceo/api/breeds/image/random', 'perro', 'message'],
    'shiba': ['https://shibe.online/api/shibes', 'shiba inu', 0],
    'fox': ['https://randomfox.ca/floof/', 'zorro', 'image'],
    'duck': ['https://random-d.uk/api/random', 'pato', 'url'],
    'bunny': ['https://api.bunnies.io/v2/loop/random/?media=gif', 'conejo', 'media.gif'],
    'owl': ['https://pics.floofybot.moe/owl', 'buho', 'image'],
}


def parse_item_result(cmd_type: str, data: Union[dict, list]) -> str:
    c_url, _, c_attr = cmd_settings[cmd_type]
    if isinstance(c_attr, int):
        data = data[c_attr]
    else:
        for prop in c_attr.split('.'):
            data = data.get(prop, '')
    if not data:
        raise RuntimeError('Result URL not found')
    if not isinstance(data, str):
        raise RuntimeError('Invalid URL result')
    if data.startswith('/'):
        proto, dom_path = c_url.split('//', 1)
        domain = dom_path.split('/', 1)[0]
        data = f'{proto}//{domain}{data}'
    return data


async def animal_interaction(cmd_type: str, interaction: discord.Interaction):
    c_url, c_name, _ = cmd_settings[cmd_type]
    async with aiohttp.ClientSession() as session:
        async with session.get(c_url) as r:
            if r.status == 200:
                data = await r.json()
                img_url = parse_item_result(cmd_type, data)
                if cmd_type == 'cat':
                    img_url = f'https://cataas.com/cat/{img_url}'
                if img_url.endswith('.gifv'):
                    img_url = img_url[:-4] + 'mp4'
                embed = discord.Embed(title=f'Aquí tienes tu {c_name}')
                embed.set_image(url=img_url)
                await interaction.response.send_message(embed=embed)
            else:
                log.error('[animals][%s] status %i heck', c_name, r.status)


for animal in cmd_settings.keys():
    def make_handler():
        z_animal = str(animal)
        async def handler(interaction: discord.Interaction):
            await animal_interaction(z_animal, interaction)
        return handler

    bot.command(name=animal, description=f'Obtener un {cmd_settings[animal][1]} al azar', coro=make_handler())
