import logging

from socket import setdefaulttimeout
from faulthandler import enable as faulthandler_enable
from telegram.ext import Updater as tgUpdater, Defaults
from os import remove as osremove, path as ospath, environ
from subprocess import Popen, run as srun, PIPE
from time import sleep, time
from threading import Lock
from dotenv import load_dotenv
from asyncio import get_event_loop
from bot.log_config import configure_logger

configure_logger()
LOGGER = logging.getLogger(__name__)

main_loop = get_event_loop()

faulthandler_enable()

setdefaulttimeout(600)

botStartTime = time()

Interval = []
DRIVES_NAMES = []
DRIVES_IDS = []
INDEX_URLS = []
GLOBAL_EXTENSION_FILTER = ['.html', '.php']
user_data = {}

download_dict_lock = Lock()
status_reply_dict_lock = Lock()
# Key: update.effective_chat.id
# Value: telegram.Message
status_reply_dict = {}
# Key: update.message.message_id
# Value: An object of Status
download_dict = {}

if ospath.exists('log.txt'):
    with open('log.txt', 'r+') as f:
        f.truncate(0)
        
load_dotenv('config.env', override=True)

BOT_TOKEN = environ.get('BOT_TOKEN', '')
if len(BOT_TOKEN) == 0:
    LOGGER.error("BOT_TOKEN variable is missing! Exiting now")
    exit(1)

OWNER_ID = environ.get('OWNER_ID', '')
if len(OWNER_ID) == 0:
    LOGGER.error("OWNER_ID variable is missing! Exiting now")
    exit(1)
else:
    OWNER_ID = int(OWNER_ID)

TELEGRAM_API = environ.get('TELEGRAM_API', '')
if len(TELEGRAM_API) == 0:
    LOGGER.error("TELEGRAM_API variable is missing! Exiting now")
    exit(1)
else:
    TELEGRAM_API = int(TELEGRAM_API)

TELEGRAM_HASH = environ.get('TELEGRAM_HASH', '')
if len(TELEGRAM_HASH) == 0:
    LOGGER.error("TELEGRAM_HASH variable is missing! Exiting now")
    exit(1)

GDRIVE_ID = environ.get('GDRIVE_ID', '')
if len(GDRIVE_ID) == 0:
    GDRIVE_ID = ''

DOWNLOAD_DIR = environ.get('DOWNLOAD_DIR', '')
if len(DOWNLOAD_DIR) == 0:
    DOWNLOAD_DIR = '/project/downloads/'
elif not DOWNLOAD_DIR.endswith("/"):
    DOWNLOAD_DIR = f'{DOWNLOAD_DIR}/'

AUTHORIZED_CHATS = environ.get('AUTHORIZED_CHATS', '')
if len(AUTHORIZED_CHATS) != 0:
    aid = AUTHORIZED_CHATS.split()
    for id_ in aid:
        user_data[int(id_.strip())] = {'is_auth': True}

INDEX_URL = environ.get('INDEX_URL', '').rstrip("/")
if len(INDEX_URL) == 0:
    INDEX_URL = ''

STATUS_UPDATE_INTERVAL = environ.get('STATUS_UPDATE_INTERVAL', '')
if len(STATUS_UPDATE_INTERVAL) == 0:
    STATUS_UPDATE_INTERVAL = 10
else:
    STATUS_UPDATE_INTERVAL = int(STATUS_UPDATE_INTERVAL)

AUTO_DELETE_MESSAGE_DURATION = environ.get('AUTO_DELETE_MESSAGE_DURATION', '')
if len(AUTO_DELETE_MESSAGE_DURATION) == 0:
    AUTO_DELETE_MESSAGE_DURATION = 30
else:
    AUTO_DELETE_MESSAGE_DURATION = int(AUTO_DELETE_MESSAGE_DURATION)

STATUS_LIMIT = environ.get('STATUS_LIMIT', '')
STATUS_LIMIT = '' if len(STATUS_LIMIT) == 0 else int(STATUS_LIMIT)

CMD_SUFFIX = environ.get('CMD_SUFFIX', '')

SERVER_PORT = environ.get('SERVER_PORT', '') or environ.get('PORT', '')
if len(SERVER_PORT) == 0:
    SERVER_PORT = 80
else:
    SERVER_PORT = int(SERVER_PORT)

STOP_DUPLICATE = environ.get('STOP_DUPLICATE', '')
STOP_DUPLICATE = STOP_DUPLICATE.lower() == 'true'

VIEW_LINK = environ.get('VIEW_LINK', '')
VIEW_LINK = VIEW_LINK.lower() == 'true'

IS_TEAM_DRIVE = environ.get('IS_TEAM_DRIVE', '')
IS_TEAM_DRIVE = IS_TEAM_DRIVE.lower() == 'true'

USE_SERVICE_ACCOUNTS = environ.get('USE_SERVICE_ACCOUNTS', '')
USE_SERVICE_ACCOUNTS = USE_SERVICE_ACCOUNTS.lower() == 'true'

config_dict = {'AUTHORIZED_CHATS': AUTHORIZED_CHATS,
               'AUTO_DELETE_MESSAGE_DURATION': AUTO_DELETE_MESSAGE_DURATION,
               'BOT_TOKEN': BOT_TOKEN,
               'CMD_SUFFIX': CMD_SUFFIX,
               'DOWNLOAD_DIR': DOWNLOAD_DIR,
               'GDRIVE_ID': GDRIVE_ID,
               'INDEX_URL': INDEX_URL,
               'IS_TEAM_DRIVE': IS_TEAM_DRIVE,
               'OWNER_ID': OWNER_ID,
               'SERVER_PORT': SERVER_PORT,
               'STATUS_LIMIT': STATUS_LIMIT,
               'STATUS_UPDATE_INTERVAL': STATUS_UPDATE_INTERVAL,
               'STOP_DUPLICATE': STOP_DUPLICATE,
               'TELEGRAM_API': TELEGRAM_API,
               'TELEGRAM_HASH': TELEGRAM_HASH,
               'USE_SERVICE_ACCOUNTS': USE_SERVICE_ACCOUNTS,
               'VIEW_LINK': VIEW_LINK}
if GDRIVE_ID:
    DRIVES_NAMES.append("Main")
    DRIVES_IDS.append(GDRIVE_ID)
    INDEX_URLS.append(INDEX_URL)

if ospath.exists('drives.txt'):
    with open('drives.txt', 'r+') as f:
        lines = f.readlines()
        for line in lines:
            temp = line.strip().split()
            DRIVES_IDS.append(temp[1])
            DRIVES_NAMES.append(temp[0].replace("_", " "))
            if len(temp) > 2:
                INDEX_URLS.append(temp[2])
            else:
                INDEX_URLS.append('')
                
if ospath.exists('accounts.zip'):
    if ospath.exists('accounts'):
        srun(["rm", "-rf", "accounts"])
    srun(["unzip", "-q", "-o", "accounts.zip", "-x", "accounts/emails.txt"])
    srun(["chmod", "-R", "777", "accounts"])
    osremove('accounts.zip')
if not ospath.exists('accounts'):
    config_dict['USE_SERVICE_ACCOUNTS'] = False
sleep(0.5)

Popen(["gunicorn", "web.server:app", f"--bind=0.0.0.0:{SERVER_PORT}", "--logger-class=web.log_config.StubbedGunicornLogger"])

tgDefaults = Defaults(parse_mode='HTML', disable_web_page_preview=True, allow_sending_without_reply=True, run_async=True)
updater = tgUpdater(token=BOT_TOKEN, defaults=tgDefaults, request_kwargs={'read_timeout': 20, 'connect_timeout': 15})
bot = updater.bot
dispatcher = updater.dispatcher
job_queue = updater.job_queue
