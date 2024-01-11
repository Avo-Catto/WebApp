from sqlite3 import IntegrityError
from json import JSONDecodeError

class TypeNameLogError(Exception):
    def __init__(self, typename:str) -> None:
        super().__init__(f'typename parameter for log function not matching: \"{typename}\"')

class TableExistError(Exception):
    def __init__(self, table_name:str) -> None:
        super().__init__(f'table already exist: \"{table_name}\"')

class DBConnectionFailedError(Exception):
    def __init__(self) -> None:
        super().__init__('failed to connect to database')

class NoSessionError(Exception):
    def __init__(self) -> None:
        super().__init__('session id not valid')

class InvalidBlogIDError(Exception):
    def __init__(self) -> None:
        super().__init__('blog doesn\'t exist')

class UserNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__('user not found')
