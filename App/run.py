# to run the app you have to be in the "App" directory
# TODO: add argparser to split initial steps from run steps
from src.backend import app
from src.sql import create_db, DB

DB_PATH = 'db/user.db'
create_user_table = """
CREATE TABLE IF NOT EXISTS credentials (
    id integer PRIMARY KEY,
    firstname text NOT NULL,
    lastname text NOT NULL,
    email text NOT NULL unique,
    username text NOT NULL,
    password text NOT NULL,
    date date NOT NULL
); """


if __name__ == '__main__': # works perfect

    # initial steps
    create_db(DB_PATH)
    db = DB(DB_PATH)
    db.execute(create_user_table)
    db.close()
    del db

    # run step
    app.run('127.0.0.1', 80, debug=True)

# TODO: the log messages are messed up, because I implemented them in the sql module: FIX IT!!!
