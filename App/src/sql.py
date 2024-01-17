from sqlite3 import connect
from os.path import exists
from src.logger import Logger
from src.exception import TableExistError, DBConnectionFailedError, JSONDecodeError

log = Logger('SQLog')

try:
    with open('./config.json', 'r') as f:
        CONFIG:dict = __import__('json').load(f)
except (JSONDecodeError, FileNotFoundError):
    log.warning('failed to load config file')

# update loglist
try: log.remove_loglist(*CONFIG.get('log')['remove'])
except NameError: log.warning('couldn\'t update the loglist')


class DB:
    def __init__(self, path:str) -> None:
        self.path = path

        try:
            self.conn = connect(path)
            self.curser = self.conn.cursor()
        except Exception as e:
            log.critical(f'Failed to connect to DB: {e.__str__()}')
            raise DBConnectionFailedError
        

    def create_db(db_path:str, ask:bool = False, question:str|None = None) -> bool:
        """Create new db file. Returns True if new DB was created and only returns False if creation was aborted by the user."""
        if ask:
            if question is None: question = 'Do you want to create a new database?'
            inp = input(f'{question} [y/n] ').lower()

            if inp == 'y':
                with open(db_path, 'w') as f: 
                    f.close()
                log.info(f'created new db: {db_path}')
                return True
            else: 
                return False
        else:
            with open(db_path, 'w') as f: 
                f.close()
            log.info(f'created new db: {db_path}')
            return True
    

    def execute(self, sql:str, params:tuple=()) -> tuple|None:
        """Execute sql code."""
        try: 
            log.debug(f'execute in db: {self.path}: {sql}')
            out = tuple(self.curser.execute(sql, params))
            if len(out) > 0: return out
            else: return None

        except Exception as e:
            log.error(f'error while executing sql on db: {self.path}: {e.__str__()}')
            raise e
    

    def create_table(self, name:str, columns:tuple|list) -> None:
        """
        Create new table in db.\n
        example: columns=["id integer PRIMARY KEY", ...]
        """
        try:
            if name not in tuple(self.list_tables()):
                code = f'CREATE TABLE IF NOT EXISTS {name} ({", ".join(columns)});'
                self.execute(code)
                self.commit()
            else:
                log.error(f'table already exist in db: {self.path}')
                raise TableExistError(name)
        except Exception as e:
            log.error(f'error while creating new table: {name} on db: {self.path}: {e.__str__()}')
            raise e


    def list_tables(self) -> tuple:
        """Returns a generator object of tables from db."""
        ex = self.execute('SELECT name FROM sqlite_master WHERE type="table";')
        return ex if ex is not None else ('',)


    def commit(self) -> None:
        """Commit executed code to db."""
        self.conn.commit()


    def close(self) -> None:
        """Close connection to DB."""
        try:
            self.commit() # just for safety
            self.conn.close()
        except Exception as e:
            log.error(f'error while closing connection to db: {self.path}: {e.__str__()}')
            raise e
    

    def insert(self, table:str, data:dict) -> None:
        """Insert data into table."""
        try:
            q = ', '.join(f"{'? '*len(data)}".split()) # get values of data
            code = f"INSERT INTO {table} ({', '.join([key for key in data])}) VALUES ({q});" # insert values safely
            self.execute(code, tuple(val for _, val in data.items()))
            self.commit()
        except Exception as e:
            log.error(f'error while inserting data into table: {table} in db: {self.path}: {e.__str__()}')
            raise e
    

    def select(self, table:str, columns:str|tuple|list, where:str='', params:tuple=()) -> tuple|None:
        """
        Retrieve data from db.
        example: where='WHERE uid = ...'
        """
        try:
            code = f'SELECT {", ".join(columns) if type(columns) != str else columns} FROM {table} {where};'
            return self.execute(code, params)
        except Exception as e:
            log.error(f'error while retrieving data from table: {table} from db: {self.path}: {e.__str__()}')
            raise e
    

    def delete(self, table:str, where:str, params:tuple=()) -> None:
        """
        Delete row in table where $where matches.
        example: where='WHERE uid = ...'
        """
        try:
            self.execute(f'DELETE FROM {table} {where};', params)
            self.commit()
        except Exception as e:
            log.error(f'error while deleting row in table: {table} in db: {self.path}: {e.__str__()}')
            raise e
    
    
    def update(self, table:str, data:dict, where:str, params:tuple=()) -> None:
        """
        Update columns in table where $where matches.
        example: where='WHERE uid = ...' 
        """
        try:
            data = ', '.join((f'{key} = "{value}"' for key, value in data.items()))
            self.execute(f'UPDATE {table} SET {data} {where};', params)
            self.commit()
        except Exception as e:
            log.error(f'error while updating row in table: {table} in db: {self.path}: {e.__str__()}')
            raise e
