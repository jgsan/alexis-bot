import asyncio
import json
from datetime import datetime
from json import JSONDecodeError

from discord import Embed

from bot import Command, categories
from bot.guild_configuration import GuildConfiguration

cached_data = None
cached_ts = datetime.now().timestamp()
last_date = None


def nf(val):
    return '.'.join([str(val)[::-1][i:i + 3] for i in range(0, len(str(val)), 3)])[::-1].replace('-.', '-')


def data_diff(data):
    diff = {}
    fields = ['activos', 'conectados', 'confirmados', 'criticos', 'fallecidos',
              'recuperados', 'ventiladores_disp']
    for field in fields:
        diff[field] = nf(data[field])
        if data['ayer']:
            val = data[field] - data['ayer'][field]
            diff[field] += ' ({})'.format(['', '+'][int(val > 0)] + nf(val))
    return diff


def description(data):
    diff = data_diff(data)
    return f'Información del día **{data["fecha"]}** (hasta las 21:00 del día anterior)\n\n' \
        f'**Total confirmados:** {diff["confirmados"]}\n' \
        f'*({nf(data["sintomaticos"])} sintomáticos, {nf(data["asintomaticos"])} asintomáticos, ' \
        f'{nf(data["sin_notificar"])} sin notificar)*\n' \
        f'**Total activos:** {diff["activos"]}\n' \
        f'**Recuperados:** {diff["recuperados"]}\n' \
        f'**Fallecidos:** {diff["fallecidos"]}\n\n' \
        f'**Exámenes realizados:** {nf(data["total_examenes"])} (+{nf(data["examenes"])})\n' \
        f'**Pacientes conectados:** {diff["conectados"]}, críticos: {diff["criticos"]}\n' \
        f'**Ventiladores disponibles:** {diff["ventiladores_disp"]}\n\n' \
        f'**Residencias sanitarias**: {data["rs_residencias"]} ' \
        f'con {nf(data["rs_habitaciones"])} habitaciones'


def embed(data):
    desc = description(data)
    the_embed = Embed(title='Estado del Coronavirus COVID-19 en Chile', description=desc)
    the_embed.set_footer(text='Información actualizada al: {}'.format(data['ts_capturado']))
    return the_embed


class Covid19CL(Command):
    __author__ = 'makzk'
    __version__ = '1.0.1'
    url = 'https://api.mak.wtf/covid'
    _last_day = None

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'covid19cl'
        self.aliases = ['covid', 'coronavirus']
        self.category = categories.INFORMATION
        self.config = GuildConfiguration.get_instance()

        self.schedule = (self.task, 60)

        self.default_config = {
            'covid19cl_telegram_key': '',
            'covid19cl_telegram_channel': ''
        }

    async def handle(self, cmd):
        try:
            data = json.loads(self.config.get('covid19cl_data', '{}', create=False))
            if not data:
                await cmd.answer('La información aún no está disponible.')
                return

            the_embed = embed(data)
            await cmd.answer(embed=the_embed)
            return
        except Exception as e:
            self.log.error(e)
            await cmd.answer('No se pudo cargar la información: {}'.format(str(e)))

    async def publish(self, data):
        tg_key = self.bot.config.get('covid19cl_telegram_key')
        tg_api = 'https://api.telegram.org/bot{apikey}/sendMessage'.format(apikey=tg_key)
        tg_chanid = self.bot.config.get('covid19cl_telegram_channel')

        message = description(data)
        the_embed = embed(data)

        self.log.debug('Publishing Covid19 data to Discord...')
        chan = self.bot.get_channel(int(self.bot.config.get('covid19cl_discord_channel')))
        await self.bot.send_message(chan, embed=the_embed)

        self.log.debug('Publishing Covid19 data to Telegram...')
        tg_message = message.replace('**', '#').replace('*', '_').replace('#', '*') + '\n\nSent by AlexisBot™'
        tg_data = {'chat_id': tg_chanid, 'text': tg_message, 'parse_mode': 'Markdown'}
        await self.http.post(tg_api, json=tg_data)

    async def task(self):
        now = datetime.now()
        curr_data = json.loads(self.config.get('covid19cl_data', '{}', create=False))

        if not curr_data or (self._last_day != now.day and now.hour >= 10):
            try:
                self.log.debug('Loading Covid19 data...')
                async with self.http.get(self.url) as r:
                    if r.status != 200:
                        raise RuntimeError('status ' + str(r.status))
                    data = await r.json()
                    if 'ts_capturado' not in data:
                        raise RuntimeError('invalid data')

                    if curr_data.get('fecha', '') != data['fecha'] and data['listo']:
                        self.config.set('covid19cl_data', json.dumps(data))
                        _last_day = now.day
                        if curr_data:
                            self.log.debug('Publishing Covid19 data...')
                            await self.publish(data)
            except (JSONDecodeError, RuntimeError) as e:
                self.log.warning('No se pudo obtener la información ({}).'.format(e))
