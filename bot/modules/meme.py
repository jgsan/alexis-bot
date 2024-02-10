from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
from discord import File

from bot import Command, categories
from bot.regex import pat_usertag
from bot.utils import download

furl = 'https://github.com/sophilabs/macgifer/raw/master/static/font/impact.ttf'


class Meme(Command):
    __author__ = 'makzk'
    __version__ = '1.0.3'

    def __init__(self, bot):
        super().__init__(bot)
        self.name = 'meme'
        self.help = '$[memes-help]'
        self.category = categories.IMAGES
        self.format = '$[format]:```$[memes-format-1]\n$[memes-format-2]\n$[memes-format-3]\n' \
                      '$[memes-format-4]\n$[memes-format-5]```'
        self.isize = 512
        self.mpath = None
        self.font = None
        self.font_smaller = None

    async def on_ready(self):
        self.mpath = await download('impact.ttf', furl)
        if self.mpath is None:
            self.log.warn('Could not retrieve the font')
            return

        try:
            self.font = ImageFont.truetype(self.mpath, size=int(self.isize/8))
            self.font_smaller = ImageFont.truetype(self.mpath, size=int(self.isize/14))
        except OSError as e:
            if str(e) == 'unknown file format':
                self.log.warn('The cached or downloaded font is invalid. '
                              'Try deleting "cache/impact.ttf" and running the bot again.')

    async def handle(self, cmd):
        if cmd.argc == 0:
            await cmd.answer(self.format)
            return

        if self.font is None:
            await cmd.answer('$[memes-disabled]')
            return

        user = cmd.author
        if cmd.argc > 1 and pat_usertag.match(cmd.args[0]):
            user = cmd.get_member_or_author(cmd.args.pop(0))
            cmd.text = ' '.join(cmd.args)
            cmd.argc -= 1

        args = [x.strip() for x in cmd.no_tags().split('|')]
        upper = '' if len(args) == 1 else args[0]
        lower = args[0] if len(args) == 1 else args[1]

        await cmd.typing()
        self.log.debug('Downloading user avatar: %s', str(user.display_avatar.url))
        avatar_data = await user.display_avatar.read()

        avatar_data = Image.open(BytesIO(avatar_data)).resize((self.isize, self.isize), Image.LANCZOS)
        im = Image.new('RGBA', (self.isize, self.isize))
        im.paste(avatar_data, (0, 0))

        self.meme_draw(im, lower, upper=False)
        if upper:
            self.meme_draw(im, upper)

        temp = BytesIO()
        im.save(temp, format='PNG')
        temp = BytesIO(temp.getvalue())  # eliminar bytes nulos

        self.log.debug('Meme generated!')
        await cmd.channel.send(cmd.author_name, file=File(temp, filename='meme.png'))

    def meme_draw(self, im, text, upper=True):
        draw = ImageDraw.Draw(im)
        sep = int(self.isize / 23)

        use_smaller = len(self.text_splitter(draw, text, self.isize - sep)) > 2
        draw.font = self.font_smaller if use_smaller else self.font

        # Determine text position
        text = '\n'.join(self.text_splitter(draw, text, self.isize - sep))
        height = draw.multiline_textbbox((0,0), text)[3]
        width = draw.textlength(text)

        xy = (int(self.isize/2)) - int(width/2), (15 if upper else self.isize - sep - height)

        # Draw shadow
        i = 2
        x, y = xy
        draw.multiline_text((x+i, y+i), text, align='center', fill='black')
        draw.multiline_text((x+i, y-i), text, align='center', fill='black')
        draw.multiline_text((x-i, y-i), text, align='center', fill='black')
        draw.multiline_text((x-i, y+i), text, align='center', fill='black')

        # Draw text itself
        draw.multiline_text(xy, text, align='center')

    def text_splitter(self, draw: ImageDraw, text: str, max_width: int, font=None):
        lines = []
        words = [f.strip() for f in text.split(' ')]

        line = []
        for word in words:
            width = draw.multiline_textbbox((0, 0), ' '.join(line) + word)[2]
            if width > max_width and len(line) > 0:
                lines.append(' '.join(line))
                line = [word]
            else:
                line.append(word)

        if len(line) > 0:
            lines.append(' '.join(line))

        return lines
