from src.logger import Logger
from sqlite3 import connect
from os.path import exists

log = Logger('SQLog', file=__file__)

def create_db(db_path:str='db.sqlite3') -> None:
    """Setup db first time."""
    if not exists(db_path):
        try: 
            with open(db_path, 'w') as f: 
                f.close()
            log.info(f'database created successful: {db_path}')
        except Exception as e:
            log.error(e.__str__())
    else:
        log.warning(f'database already exists there: {db_path}')

