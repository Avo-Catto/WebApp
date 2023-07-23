# sql db management stuff
# https://www.sqlitetutorial.net

from src.logger import Logger
from sqlite3 import connect
from os.path import exists

log = Logger('SQLog')
log.remove_loglist('info')


class DB:
    def __init__(self, path:str) -> None:
        self.path = path

        if self._create_db(path, True):
            self.conn = connect(path)
            self.curser = self.conn.cursor()
            log.info(f'connected to db: {path}')
        else: 
            log.critical('no db given')

    def _create_db(self, db_path:str, ask:bool = False, question:str|None = None) -> bool:
        """Create new db file if not already there and return True if a db exists to connect to."""
        if not exists(db_path):
            if ask:
                if question is None: question = f'The requested DB doesn\' exist, do you want to create a new one? [y/n]'
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
            log.debug(f'execute on db: {self.path}:\n{sql}')
            out = tuple(self.curser.execute(sql, params))
            if len(out) > 0: return out[0]
            else: return None
            
        except Exception as e:
            log.error(f'error while executing sql on db: {self.path}: {e.__str__()}')
            raise e
    
    def close(self) -> None:
        """Close connection to DB."""
        try:
            self.conn.close()
            log.info(f'connection to db: {self.path} closed')
        except Exception as e:
            log.error(f'error while closing connection to db: {self.path}: {e.__str__()}')
            raise e
    
    def commit(self) -> None:
        """Commit executed code to db."""
        self.conn.commit()
    
    def insert(self, table:str, data:dict) -> None:
        """Insert data into table."""
        try:
            log.debug(f'insert data into db: {self.path}: table: {table}')
            q = ', '.join(f"{'? '*len(data)}".split())
            code = f"INSERT INTO {table} ({', '.join([key for key in data])}) VALUES ({q});"
            self._execute(code, tuple(val for _, val in data.items()))
        except Exception as e:
            log.error(f'error while inserting data into table: {table} in db: {self.path}: {e.__str__()}')
            raise e
    
    def select(self, table:str, columns:str|tuple|list, where:str) -> tuple|None:
        """Retrieve data from db."""
        try:
            log.debug(f'get {columns} from db: {self.path}: table: {table}')
            code = f'SELECT {", ".join(columns) if type(columns) != str else columns} FROM {table} WHERE {where}'
            return self._execute(code)
        except Exception as e:
            log.error(f'error while retrieving data from table: {table} from db: {self.path}: {e.__str__()}')
            raise e

# TODO: create_table function
