from sqlite3 import IntegrityError
from json import JSONDecodeError

class TypeNameLogError(Exception):
    def __init__(self, typename:str) -> None:
        super().__init__(f'typename parameter for log function not matching: \"{typename}\"')

class TableExistError(Exception):
    def __init__(self, table_name:str) -> None:
        super().__init__(f'table already exist: \"{table_name}\"')

class NoDBError(Exception):
    def __init__(self) -> None:
        super().__init__('no db were selected')
