# to run the app you have to be in the "App" directory

from argparse import ArgumentParser
from src.backend import app
from src.sql import DB
from src.logger import Logger
from json import dump, load

# load config
with open('./config.json', 'r') as f:
    CONFIG:dict = load(f)

if __name__ == '__main__':
    parser = ArgumentParser(
        usage='python3 run.py *options',
        epilog='by Avo-Catto'
    )
    parser.add_argument('--run', action='store_true', default=False, help='run application')
    parser.add_argument('--setup', action='store_true', default=False, help='setup db automatically')
    parser.add_argument('--sql', action='store_true', default=False, help='start interactive interface for db')
    parser.add_argument('--debug', action='store_true', default=False, help='activate debugging mode')
    args = vars(parser.parse_args()) # parse args and convert to dict
    # has to be adjusted maybe if adding new args
    if not any(tuple(args.values())[0:3]):
        parser.print_help()
        exit()

    log = Logger('RunLog')

    if args.get('run'):
        log.info('starting flask')
        app.run('127.0.0.1', 80, debug=True)
    
    elif args.get('setup'): # TODO: make it better
        print('You are about to setup configs and databases for the application.')
        if input('Are you sure you want to proceed? [y/n] ').lower() != 'y':
            exit()
        
        CONFIG.update({
            'backend-db': input('Pleas specify the name for the db of the backend which stores account data: '),
        })

        print('Please enter "y" to create a new db.')
        db = DB(CONFIG.get('backend-db'))
        db._create_table(
            'credentials', (
                'id integer PRIMARY KEY',
                'unique_id text NOT NULL unique',
                'firstname text NOT NULL',
                'lastname text NOT NULL',
                'email text NOT NULL unique',
                'username text NOT NULL',
                'password text NOT NULL',
                'date date NOT NULL'
            )
        )
        db.close()

        print('Setup complete!')

        # save config to file
        with open('./config.json', 'w') as f:
            dump(CONFIG, f, indent=4)

# TODO: think about how to handle main args and options (subparser?)
# TODO: customizable port and host?
# TODO: add argparser to split initial steps from run steps
# TODO: add interactive mode for db
# TODO: add more configurability to db (specify custom table name for credentials)
