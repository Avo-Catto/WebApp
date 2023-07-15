from sqlite3 import connect
from os.path import exists


def init_db(db_name:str='db.sqlite3') -> None:
    """Setup db first time."""
    if not exists(db_name):
        try: 
            with open('db.sqlite3', 'w') as f: 
                f.close()
                print(a)
        except Exception as e:
            Log.exception(f'> error[0]: {e.__str__()}')

# only for debugging purpose
if __name__ == '__main__':
    init_db()
