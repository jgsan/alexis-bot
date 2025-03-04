import re

from ruamel.yaml import YAML
from discord import Embed

from bot import settings
from bot.logger import new_logger

pat_lang_placeholder = re.compile(r'\$\[([a-zA-Z0-9_\-]+)\]')
log = new_logger('Language')


class Language:
    def __init__(self, default='en', autoload=False):
        self.lib = {}
        self.path = settings.base_dir / 'lang'
        self.default = default

        if autoload:
            self.load()

    def load(self):
        self.lib = {}
        lang_files = self.path.glob('**/*.yml')

        for lang_file in lang_files:
            if not lang_file.is_file() or not lang_file.name.endswith('.yml'):
                continue

            with lang_file.open(encoding='utf8') as f:
                yml = YAML(typ='safe')
                data = dict(yml.load(f))
                lang = lang_file.name[:-4]

                for k, v in data.items():
                    if not isinstance(v, str) and not isinstance(v, int) and not isinstance(v, float):
                        continue

                    if lang not in self.lib:
                        self.lib[lang] = {}

                    self.lib[lang][k] = str(v)

    def get(self, name, __lang=None, **kwargs):
        if __lang is None:
            __lang = self.default

        if __lang not in self.lib:
            text = __lang + '_' + name
        elif name not in self.lib[__lang] or self.lib[__lang][name].strip() == '':
            if __lang == self.default:
                text = '[{}:{}]'.format(__lang, name)
            else:
                text = self.get(name, self.default, **kwargs)
        else:
            text = self.lib[__lang][name]

            try:
                text = text.format(**kwargs)
            except KeyError:
                pass

        return text

    def get_list(self, name, separator='|', __lang=None, **kwargs):
        val = self.get(name, __lang, **kwargs)
        return [f.strip() for f in val.split(separator) if f.strip() != '']

    def has(self, lang):
        return lang in self.lib


class SingleLanguage:
    def __init__(self, instance, lang):
        self.instance = instance
        self.lang = lang

    def get(self, name, **kwargs):
        return self.instance.get(name, self.lang, **kwargs)

    def get_list(self, name, separator='|', **kwargs):
        return self.instance.get_list(name, separator, self.lang, **kwargs)

    def format(self, message, locales=None):
        if isinstance(message, str):
            locales = locales or {}
            for m in pat_lang_placeholder.finditer(message):
                message = message.replace(m.group(0), self.get(m.group(1), **locales))

            return self.format(message) if pat_lang_placeholder.search(message) else message
        elif isinstance(message, Embed):
            if message.title is not None:
                message.title = self.format(message.title, locales)
            if message.description is not None:
                message.description = self.format(message.description, locales)
            if message.footer.text is not None:
                message.set_footer(text=self.format(message.footer.text, locales), icon_url=message.footer.icon_url)

            for idx, field in enumerate(message.fields):
                message.set_field_at(idx,
                                     name=self.format(field.name, locales),
                                     value=self.format(field.value, locales),
                                     inline=field.inline)
            return message
        elif message is None:
            return None
        else:
            return self.format(str(message), locales)
