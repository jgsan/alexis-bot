from typing import Optional
from random import choice
import json
from xml.etree.ElementTree import fromstring as parsexml

import aiohttp
import discord

from .. import bot, log

search_types = {
    'e621': {
        'url': 'https://e621.net/posts.json?limit=30&tags={}',
        'name': 'e621.net'
    },
    'gelbooru': {
        'url': 'https://gelbooru.com/index.php?page=dapi&s=post&q=index&tags={}'
    },
    'rule34': {
        'url': 'https://rule34.xxx/index.php?page=dapi&s=post&q=index&tags={}'
    },
    'danbooru': {
        'url': 'https://danbooru.donmai.us/posts.json?limit=30&tags={}'
    },
    'konachan': {
        'url': 'https://konachan.net/post.json?limit=30&tags={}',
        'name': 'konachan.net (sfw)'
    },
    'konachan18': {
        'url': 'https://konachan.com/post.json?limit=30&tags={}',
        'name': 'konachan.com (nsfw)'
    },
    'hypnohub': {
        'url': 'https://hypnohub.net/post/index.json?limit=30&tags={}',
    },
    'xbooru': {
        'url': 'https://xbooru.com/index.php?page=dapi&s=post&q=index&tags={}'
    },
    'realbooru': {
        'url': 'https://realbooru.com/index.php?page=dapi&s=post&q=index&tags={}'
    },
    'furrybooru': {
        'url': 'https://furry.booru.org/index.php?page=dapi&s=post&q=index&tags={}'
    }
}


async def cmd_handler(cmd_type: str, interaction: discord.Interaction, query: str=''):
    if not interaction.channel.is_nsfw():
        await interaction.response.send_message(
            'Este comando solo puede ser utilizado en un canal NSFW', ephemeral=True
        )
        return

    conf = search_types[cmd_type]
    c_url = conf['url'].format(query)
    await interaction.channel.typing()

    async with aiohttp.ClientSession() as session:
        async with session.get(c_url) as r:
            if r.status != 200:
                log.error('[booru][%s] status %i heck', cmd_type, r.status)
                return

            result = await r.text()
            if result.startswith('<'):
                posts = parsexml(result).findall('post')
            else:
                posts = json.loads(result)
                if cmd_type == 'e621':
                    posts = filter(lambda x: x['file']['ext'] != 'webm', posts['posts'])

            if len(posts) == 0:
                await interaction.response.send_message('Sin resultados', ephemeral=True)
                return

            post = choice(posts)
            image_url = post['file']['url'] if cmd_type == 'e621' else post.get('file_url')

            if image_url.startswith('//'):
                image_url = f'https:{image_url}'

            site_name = conf.get('name', cmd_type)
            embed = discord.Embed(title=f'Resultado de la búsqueda en {site_name}')
            embed.set_image(url=image_url)
            await interaction.response.send_message(embed=embed)


for search_type, conf in search_types.items():
    def booru_handler():
        z_type = str(search_type)
        async def handler(interaction: discord.Interaction, query: Optional[str]=''):
            await cmd_handler(z_type, interaction, query)
        return handler

    description = 'Buscar contenido en ' + conf.get('name', search_type)
    bot.command(name=search_type, description=description, coro=booru_handler())
