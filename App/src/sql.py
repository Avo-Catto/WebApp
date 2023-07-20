# sql db management stuff
# https://www.sqlitetutorial.net

from src.logger import Logger
from sqlite3 import connect
from os.path import exists

log = Logger('SQLog', file=__file__)


def create_db(db_path:str) -> None:
    """Create new db file."""
    if not exists(db_path):
        try: 
            with open(db_path, 'w') as f: 
                f.close()
            log.info(f'database created successfully: {db_path}')
        except Exception as e:
            log.critical(f'creating db: {db_path} failed')
            log.error(e.__str__())
    else:
        log.warning(f'database already exists there: {db_path}')


class DB:
    def __init__(self, path:str) -> None:
        self.path = path
        try:
            log.info(f'connecting to DB: {path}') 
            self.conn = connect(path)
            self.curser = self.conn.cursor()
            log.info(f'connection to DB: {path} established')
        except Exception as e:
            log.critical(f'connecting to DB: {path} failed')
            log.error(e.__str__())
    
    def execute(self, sql:str, params:tuple=()) -> bool:
        """Execute sql code and return True if succeed."""
        try: 
            log.debug(f'execute on db:\n{sql}')
            self.curser.execute(sql, params)
            self.conn.commit()
            log.info(f'execution succeed on db: {self.path}')
            return True
        except Exception as e:
            log.warning(f'an error occured while executing sql')
            log.error(e.__str__())
            return False
    
    def close(self) -> None:
        """Close connection to DB."""
        try:
            self.conn.close()
            log.info(f'connection to DB: {self.path} closed successful')
        except Exception as e:
            log.warning(f'an error occured while closing the connection to the DB: {self.path}')
            log.error(e.__str__())
    
    def insert(self, table:str, data:dict) -> bool:
        """Insert data into table."""
        q = ', '.join(f"{'? '*len(data)}".split())
        code = f"INSERT INTO {table} ({', '.join([key for key in data])}) VALUES ({q});"
        log.debug(f'Insert command would be executed:\n{code}')
        log.debug(f'Parameters: {tuple(val for key, val in data.items())}')
        self.execute(sql=code, params=tuple(val for key, val in data.items()))

# TODO: work on DB class (+add interactive feature) 
