# to run code you have to be in the "App" directory
from src.sql import create_db, log

if __name__ == '__main__':
    create_db('./db/main.sqlite3')
