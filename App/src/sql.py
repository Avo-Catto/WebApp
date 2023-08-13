# sql db management stuff
# https://www.sqlitetutorial.net

from sqlite3 import connect
from os.path import exists
from src.logger import Logger
from src.exception import TableExistError, NoDBError, JSONDecodeError

log = Logger('SQLog')
# log.remove_loglist('info')

try:
    with open('./config.json', 'r') as f:
        CONFIG:dict = __import__('json').load(f)
except JSONDecodeError:
    log.critical('config file couldn\'t be loaded: some functions will raise errors')


class DB:
    def __init__(self, path:str) -> None:
        self.path = path

        if self._create_db(path, True):
            self.conn = connect(path)
            self.curser = self.conn.cursor()
            log.info(f'connected to db: {path}')
        else: 
            log.critical('no db given')
            raise NoDBError

    def _create_db(self, db_path:str, ask:bool = False, question:str|None = None) -> bool:
        """Create new db file if not already there and return True if a db exists to connect to."""
        if not exists(db_path):
            if ask:
                if question is None: question = f'The requested DB doesn\' exist, do you want to create a new one? [y/n] '
                inp = input(question).lower()

                if inp == 'y':
                    with open(db_path, 'w') as f: 
                        f.close()
                    log.info(f'created new db: {db_path}')
                    return True
                else: 
                    return False
        else: 
            return True
    
    def _execute(self, sql:str, params:tuple=()) -> tuple|None:
        """Execute sql code."""
        try: 
            log.debug(f'execute on db: {self.path}: {sql}')
            out = tuple(self.curser.execute(sql, params))
            if len(out) > 0: return out
            else: return None
            
        except Exception as e:
            log.error(f'error while executing sql on db: {self.path}: {e.__str__()}')
            raise e
    
    def _create_table(self, name:str, columns:tuple|list) -> None:
        """
        Create new table in db.\n
        example: columns=["id integer PRIMARY KEY", ...]
        """
        try:
            if name not in tuple(self._list_tables()):
                code = f'CREATE TABLE IF NOT EXISTS {name} ({", ".join(columns)});'
                self._execute(code)
                self._commit()
                log.info(f'created new table: {name} in db: {self.path}')
            else:
                log.critical(f'table already exist in db: {self.path}')
                raise TableExistError(name)
        except Exception as e:
            log.error(f'error while creating new table: {name} on db: {self.path}: {e.__str__()}')
            raise e

    def _list_tables(self) -> tuple:
        """Returns a generator object of tables from db."""
        ex = self._execute('SELECT name FROM sqlite_master WHERE type="table";')
        return ex if ex is not None else ('')

    def _commit(self) -> None:
        """Commit executed code to db."""
        self.conn.commit()

    def close(self) -> None:
        """Close connection to DB."""
        try:
            self._commit() # just for safety
            self.conn.close()
            log.info(f'connection to db: {self.path} closed')
        except Exception as e:
            log.error(f'error while closing connection to db: {self.path}: {e.__str__()}')
            raise e
    
    def insert(self, table:str, data:dict) -> None:
        """Insert data into table."""
        try:
            log.debug(f'insert data into db: {self.path}: table: {table}')
            q = ', '.join(f"{'? '*len(data)}".split())
            code = f"INSERT INTO {table} ({', '.join([key for key in data])}) VALUES ({q});"
            self._execute(code, tuple(val for _, val in data.items()))
            self._commit()
        except Exception as e:
            log.error(f'error while inserting data into table: {table} in db: {self.path}: {e.__str__()}')
            raise e
    
    def select(self, table:str, columns:str|tuple|list, where:str='', params:tuple=()) -> tuple|None:
        """
        Retrieve data from db.
        example: where='WHERE username = ...'
        """
        try:
            log.debug(f'get {columns} from db: {self.path}: table: {table}')
            code = f'SELECT {", ".join(columns) if type(columns) != str else columns} FROM {table} {where};'
            return self._execute(code, params)
        except Exception as e:
            log.error(f'error while retrieving data from table: {table} from db: {self.path}: {e.__str__()}')
            raise e
    
    def delete(self, table:str, where:str, params:tuple=()) -> None:
        """
        Delete row in table where $where matches.
        example: where='WHERE username = ...'
        """
        try:
            log.debug(f'delete row in table: {table} where: {where}')
            self._execute(f'DELETE FROM {table} {where};', params)
            self._commit()
        except Exception as e:
            log.error(f'error while deleting row in table: {table} in db: {self.path}: {e.__str__()}')
            raise e


# TODO: add interactive mode
