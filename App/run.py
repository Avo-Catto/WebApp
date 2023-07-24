# to run the app you have to be in the "App" directory
from src.backend import app
from src.sql import DB
from src.logger import Logger

DB_PATH = 'db/user.db'
create_user_table = """
CREATE TABLE IF NOT EXISTS credentials (
    id integer PRIMARY KEY,
    unique_id text NOT NULL unique,
    firstname text NOT NULL,
    lastname text NOT NULL,
    email text NOT NULL unique,
    username text NOT NULL,
    password text NOT NULL,
    date date NOT NULL
); """

if __name__ == '__main__':

    log = Logger('RunLog')

    log.info(f'connect to db: {DB_PATH}')
    db = DB(DB_PATH)
    log.info(f'create table in db: {DB_PATH}')
    db._execute(create_user_table)
    db.commit()
    log.info(f'close connection to db: {DB_PATH}')
    db.close()
    del db

    log.info('starting flask')
    app.run('127.0.0.1', 80, debug=True)

# TODO: add argparser to split initial steps from run steps
