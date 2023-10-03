# to run the app you have to be in the "App" directory
from argparse import ArgumentParser
from json import dump, load, JSONDecodeError
from src.logger import Logger
from os.path import exists
from os import remove, mkdir
from multiprocessing import Process

log = Logger('RunLog')

# load config
if not exists('./config.json'):
    with open('./config.json', 'x') as f:
        CONFIG:dict = dict()
else:
    try:
        with open('./config.json', 'r') as f:
            CONFIG:dict = load(f)
    except JSONDecodeError:
        CONFIG:dict = dict()

if __name__ == '__main__':
    parser = ArgumentParser(
        usage='python3 run.py *options',
        epilog='by Avo-Catto'
    )
    parser.add_argument('--run', action='store_true', default=False, help='run application')
    parser.add_argument('--setup', action='store_true', default=False, help='setup db automatically')
    parser.add_argument('--sql', action='store_true', default=False, help='start interactive interface for db')
    parser.add_argument('--no-debug', action='store_false', default=True, help='activate debugging mode')
    args = vars(parser.parse_args()) # parse args and convert to dict
    log.debug(f'available args: {args}')

    if not any(tuple(args.values())[0:3]): # has to be adjusted maybe if adding new args
        parser.print_help()
        exit()

    if args.get('run'):
        try:
            from src.backend import app
            from src.session import session_cleanup

            SESSION_CLEANUP_INTERVALL = CONFIG.get('vars')['session_cleanup'] # 60 seconds (can be incresed after checking if it works)

            log.info('starting session cleanup proc')
            session_clean_proc = Process(target=session_cleanup, args=(SESSION_CLEANUP_INTERVALL, ))
            session_clean_proc.start()

            log.info('starting flask')
            app.run('127.0.0.1', 8080, debug=args['no_debug'])
        except Exception as e:
            log.error(f'the application couldn\'t be started because of error: {e.__str__()}')
            log.info('This error occured probably, because of an error in the code or the application wasn\'t set up properly. If so, please run: python3 run.py --setup')
            session_clean_proc.terminate()

    elif args.get('setup'):
        from src.sql import DB
        print('You are about to setup configs and databases for the application.')
        if input('Are you sure you want to proceed? [y/n] ').lower() != 'y': 
            exit()
        
        db_name = input('Filename of DB: ')
        CONFIG.update({
            'db': {
                'path': f'db/{db_name}{".db" if not db_name.endswith((".db", ".database", ".sqlite3", ".sqlite")) else ""}',
                'tables': {
                    'user-data': f'{input("Name of table for whole account data: ")}',
                    'session': f'{input("Name for table of session table: ")}'
                }
            },
            'vars': {
                'cookie_livetime': int(input('Session cookie livetime in seconds: ')),
                'session_cleanup': int(input('Time intervall between session table clean up: '))
            }
        })

        if exists(CONFIG.get('db')['path']):
            print('There is already a db.\nContinuing ends up with deleting this db.')
            if input('Do you want to continue? [y/n] ').lower() == 'y':
                remove(CONFIG.get('db')['path'])
            else:
                log.info('setup new db aborted')
                exit()

        print('Please enter "y" to create a new db.')
        if not exists('./db/'): mkdir('./db/')
        db = DB(CONFIG.get('db')['path'])

        db._create_table( # user table
            CONFIG.get('db')['tables']['user-data'], (
                'id integer PRIMARY KEY',
                'unique_id text NOT NULL unique',
                'firstname text NOT NULL',
                'lastname text',
                'email text NOT NULL unique',
                'username text NOT NULL',
                'password text NOT NULL',
            )
        )
        db._create_table( # session table
            CONFIG.get('db')['tables']['session'], (
                'id integer PRIMARY KEY',
                'unique_id text NOT NULL unique',
                'session_id text',
                'expiration timestamp',
                'username text NOT NULL',
                'email text NOT NULL',
                'realname text NOT NULL'
            )
        )
        db.close()
        log.info('db setup complete')

        # save config to file
        with open('./config.json', 'w') as f:
            dump(CONFIG, f, indent=4)

# TODO: think about how to handle main args and options (subparser?)
# TODO: customizable port and host?
# TODO: setup mode, catch exceptions when updating configs + validate if tables have same name
# TODO: make app stoppable -_- (it's because of the while loop in the proc...)
# TODO: fix auto submit credentials if you try to change site (signup & login sites)
# TODO: 1. make profile viewable of data, 2. make blog posts in md, 3. make profile stuff customizable and posts too
# TODO: make heading "TechCat-Blog" to a button and redirect to root
# TODO: auf Freepic verweisen bei Profilbild <a href="https://www.flaticon.com/de/kostenlose-icons/katze" title="katze Icons">Katze Icons erstellt von Freepik - Flaticon</a>
# TODO: the change profile input button should show that an image is selected
# TODO: think about blog posts