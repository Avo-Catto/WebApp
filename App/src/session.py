from src.logger import Logger
from src.sql import DB
from src.exception import IntegrityError, JSONDecodeError, NoSessionError
from time import sleep
from datetime import datetime

log = Logger('SessionLog')

try:
    with open('./config.json', 'r') as f:
        CONFIG:dict = __import__('json').load(f)
except JSONDecodeError:
    log.critical('failed to load config file')
    exit(1)

# update loglist
log.remove_loglist(*CONFIG.get('log')['remove'])

DB_PATH = CONFIG.get('db')['path']
TABLES = CONFIG.get('db')['tables']


def add_session(unique_id:str, session_id:str, expires:datetime, username:str, email:str, realname:str) -> None:
    """Add session cookie to db for validation."""
    db = DB(DB_PATH)
    data = {
        'unique_id': unique_id,
        'session_id': session_id,
        'expiration': expires,
        'username': username,
        'email': email,
        'realname': realname,
    }
    try: db.insert(TABLES['session'], data)
    except IntegrityError:
        log.debug(f'update session: {session_id}')
        db.delete(TABLES['session'], f'WHERE unique_id = "{unique_id}"')
        db.insert(TABLES['session'], data)
    db.close()


def get_session_data(session_id:str, data:str|tuple|list) -> tuple:
    """Return requested data of session or raise NoSessionError if session doesn't exist."""
    db = DB(DB_PATH)
    data = (data, ) if type(data) == str else data # handle string type
    try: return db.select(TABLES['session'], data, f'WHERE session_id = "{session_id}"')[0]
    except TypeError: raise NoSessionError


def session_cleanup(sleep_time: int) -> None:
    """Clean session table by expired cookies."""
    while True:
        try: sleep(sleep_time)
        except Exception as e: 
            log.warning(f'session cleanup process stopped due exception: {e}')
            break
        db = DB(CONFIG.get('db')['path'])
        db.delete(CONFIG.get('db')['tables']['session'], f'WHERE expiration < ?', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), )) # delete expired sessions
        db.close()
        log.debug('cleared expired sessions')
