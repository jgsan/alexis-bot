from io import BytesIO
from os import path
from PIL import Image
from alexis import Command


class ShipperUwU(Command):
    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'ship'
        self.help = 'Forma parejas entre dos usuarios'
        self.allow_pm = False

    async def handle(self, cmd):
        if cmd.argc != 2:
            await cmd.answer('formato: $CMD @usuario1 @usuario2')
            return

        # obtener menciones en el mismo orden en el que se escribieron
        user1 = await cmd.get_user(cmd.args[0])
        user2 = await cmd.get_user(cmd.args[1])

        # verificar que los usuarios no son iguales po jaja
        if user1.id == user2.id:
            await cmd.answer('sabías que para formar una pareja necesitas a dos personas? :3')
            return

        await cmd.typing()
        self.log.debug('Generando imagen...')

        # Descargar avatares
        avatar1_url = user1.avatar_url[:-4] + '.png'
        avatar2_url = user2.avatar_url[:-4] + '.png'
        async with self.http.get(avatar1_url) as resp:
            self.log.debug('Descargando avatar usuario 1 - %s', avatar1_url)
            user1_avatar = await resp.read()
        async with self.http.get(avatar2_url) as resp:
            self.log.debug('Descargando avatar usuario 2 - %s', avatar2_url)
            user2_avatar = await resp.read()

        # Abrir avatares y cambiar su tamaño
        user1_img = Image.open(BytesIO(user1_avatar)).resize((512, 512), Image.ANTIALIAS)
        user2_img = Image.open(BytesIO(user2_avatar)).resize((512, 512), Image.ANTIALIAS)

        # Abrir el corazón <3
        heart_img = Image.open(path.join(path.dirname(path.realpath(__file__)), 'heart.png'))

        # Crear imagen resultante
        result = Image.new('RGBA', (1536, 512))
        result.paste(user1_img, (0, 0))
        result.paste(heart_img, (512, 0))
        result.paste(user2_img, (1024, 0))

        # Guardar imagen en un array
        temp = BytesIO()
        result.save(temp, format='PNG')
        temp = BytesIO(temp.getvalue())  # eliminar bytes nulos
        self.log.debug('Imagen lista!')

        # Generar nombre del ship y enviar con la imagen
        u1name = user1.display_name
        u2name = user2.display_name
        ship_name = u1name[0:int(len(u1name) / 2)] + u2name[int(len(u2name) / 2):]
        await self.bot.send_file(cmd.message.channel, temp, filename='ship.png',
                                 content='Formando la pareja: **{}**'.format(ship_name))
