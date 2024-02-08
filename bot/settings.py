from os import getenv
import pathlib
from dotenv import load_dotenv

load_dotenv()

base_dir = pathlib.Path(__file__).parent.parent
debug = getenv('DEBUG', '') == '1'
database_url = getenv('DATABASE_URL', 'sqlite:///database.db')
discord_token = getenv('DISCORD_TOKEN')
chunk_guilds = getenv('CHUNK_GUILDS', '') == '1'

command_prefix = getenv('COMMAND_PREFIX', '!')
owner_role = getenv('OWNER_ROLE', 'AlexisMaster')
bot_owners = getenv('BOT_OWNERS', '130324995984326656').split(',')

default_language = getenv('DEFAULT_LANGUAGE', 'es_CL')

log_to_file = getenv('LOG_TO_FILE', '') == '1'
log_path = getenv('LOG_PATH', 'alexisbot.log')
log_format = getenv('LOG_FORMAT', '%(asctime)s | %(levelname)-8s | %(name)s || %(message)s')
log_level = getenv('LOG_LEVEL', 'DEBUG' if debug else 'INFO')

allowlist_servers = getenv('ALLOWLIST_SERVERS', '').split(',')
allowlist_autoleave = getenv('ALLOWLIST_AUTOLEAVE', '1') == '1'
allowlist_contact = getenv('ALLOWLIST_CONTACT', bot_owners[0])
blocklist_servers = getenv('BLOCKLIST_SERVERS', '').split(',')

command_guilds = getenv('COMMAND_GUILDS', '').split(',')

weatherapi_key = ''

try:
    from local_settings import *  # pyright: ignore[reportMissingImports]
except ImportError:
    pass
