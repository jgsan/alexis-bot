from os import getenv
import pathlib
from dotenv import load_dotenv

load_dotenv()

def s2l(val):  # string2list
    return [y for x in str('' if val is None else val).split(',') if (y := x.strip())]

def tryint(val, default=None):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


base_dir = pathlib.Path(__file__).parent.parent
debug = getenv('DEBUG', '') == '1'
database_url = getenv('DATABASE_URL', 'sqlite:///database.db')
discord_token = getenv('DISCORD_TOKEN')
chunk_guilds = getenv('CHUNK_GUILDS', '') == '1'

command_prefix = getenv('COMMAND_PREFIX', '!')
owner_role = getenv('OWNER_ROLE', 'AlexisMaster')
bot_owners = s2l(getenv('BOT_OWNERS', '130324995984326656'))

default_language = getenv('DEFAULT_LANGUAGE', 'es_CL')

log_to_file = getenv('LOG_TO_FILE', '') == '1'
log_path = getenv('LOG_PATH', 'alexisbot.log')
log_format = getenv('LOG_FORMAT', '%(asctime)s | %(levelname)-8s | %(name)s || %(message)s')
log_level = getenv('LOG_LEVEL', 'DEBUG' if debug else 'INFO')

allowlist_enabled = getenv('ALLOWLIST_ENABLED', '0') == '1'
allowlist_servers = s2l(getenv('ALLOWLIST_SERVERS'))
allowlist_autoleave = getenv('ALLOWLIST_AUTOLEAVE', '1') == '1'
allowlist_contact = getenv('ALLOWLIST_CONTACT', bot_owners[0])
blocklist_servers = s2l(getenv('BLOCKLIST_SERVERS'))

command_guilds = s2l(getenv('COMMAND_GUILDS'))

# Modules values
weatherapi_key = getenv('WEATHERAPI_KEY')
twitter_api_key = getenv('TWITTER_API_KEY')
twitter_api_secret = getenv('TWITTER_API_SECRET')
bitly_api_key = getenv('BITLY_API_KEY')
bitly_domain = getenv('BITLY_DOMAIN', 'bit.ly')
bitly_min_length = tryint(getenv('BITLY_MIN_LENGTH'), 25)
greeting_max_messages = tryint(getenv('GREETING_MAX_MESSAGES'), 10)
greeting_max_length = tryint(getenv('GREETING_MAX_LENGTH'), 1000)
iam_roles_limit = tryint(getenv('IAM_ROLES_LIMIT'), 0)
polls_max_options = tryint(getenv('POLLS_MAX_OPTIONS'), 6)
remindme_text_limit = tryint(getenv('REMINDME_TEXT_LIMIT'), 150)
currency_api_key = getenv('CURRENCY_API_KEY')
sbif_api_key = getenv('SBIF_API_KEY')

try:
    from local_settings import *  # pyright: ignore[reportMissingImports]
except ImportError:
    pass
