from argparse import ArgumentParser
from json import dump, load, JSONDecodeError
from src.logger import Logger
from os.path import exists
from os import remove, mkdir, listdir
from multiprocessing import Process

log = Logger('RunLog')

# load config
if exists('./config.json'):
    try:
        with open('./config.json', 'r') as f:
            CONFIG:dict = load(f)
    except JSONDecodeError:
        CONFIG:dict = dict()
else: 
    CONFIG:dict = dict()


def run() -> None:
    """Run the application."""
    try:
        from src.backend import app
        from src.session import session_cleanup

        # start session cleanup background process
        log.info('starting session cleanup proc')
        session_clean_proc = Process(target=session_cleanup, args=(CONFIG.get('vars')['session_cleanup'], ))
        session_clean_proc.start()

        # run application
        log.info('starting flask')
        app.run(CONFIG.get('run')['address'], CONFIG.get('run')['port'], debug=args['debug'])
    
    except Exception as e:
        log.error(f'the application couldn\'t be started because of error: {e.__str__()}')
        log.info('This error occured probably, because of an error in the code or the application wasn\'t set up properly. If so, please run: python3 run.py --setup')
        try: session_clean_proc.terminate()
        except Exception as e: log.warning(e.__str__())


def cleanup() -> None:
    """Cleanup directories and delete files with custom data."""
    print('You are about to clean up the whole application.')
    if input('Are you sure you want to proceed? [y/n] ').lower() != 'y': 
        exit()

    # clean up blogs
    try: 
        tuple(map(lambda x: remove(f'./static/blogs/{x}'), listdir('./static/blogs')))
        log.debug('deleting blogs')
    except Exception as e: 
        log.warning(f'exception caught at deleting blogs: {e.__str__()}')
    
    # clean up profile images
    try: 
        tuple(map(lambda x: remove(f'./static/img/profiles/{x}') if x != 'anonymous.png' else ..., listdir('./static/img/profiles')))
        log.debug('deleting profile images')
    except Exception as e: 
        log.warning(f'exception caught at deleting profile images: {e.__str__()}')

    # clean up database
    try: 
        remove(CONFIG.get('db')['path'])
        log.debug('deleting database')
    except Exception as e: 
        if e.__str__() != "'NoneType' object is not subscriptable":
            log.warning(f'exception caught at deleting db: {e.__str__()}')

    # clean up configs
    try: 
        remove('./config.json')
        log.debug('deleting configs')
    except Exception as e: 
        log.warning(f'exception caught at deleting configs: {e.__str__()}')

    log.info('cleanup succeed')


def setup() -> None:
    """Set everything up."""
    from src.sql import DB
    
    # config file
    CONFIG.update({
        'db': {
            'path': 'db/main.db',
            'tables': {
                'user-data': 'users',
                'session': 'sessions',
                'blog': 'blogs'
            }
        },
        'vars': {
            'cookie_livetime': 43200,
            'session_cleanup': 600
        },
        'run': {
            'address': '0.0.0.0',
            'port': 8080
        },
        'log': {
            'remove':['debug'] if args['debug'] is False else []
        }
    })

    # save config to file
    with open('./config.json', 'w') as f: 
        dump(CONFIG, f, indent=4)

    # database stuff
    if not exists('./db/'): mkdir('./db/') # db directory
    DB.create_db( # db file
        CONFIG.get('db')['path'], 
        True if exists(CONFIG.get('db')['path']) else False,
        'Do you want to overwrite the current setup?'
    )
    db = DB(CONFIG.get('db')['path']) # connect to db

    # table in db
    db.create_table( # user table
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
    db.create_table( # session table
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
    db.create_table( # blog table
        CONFIG.get('db')['tables']['blog'], (
            'id integer PRIMARY KEY',
            'unique_id text NOT NULL',
            'username text NOT NULL',
            'title text NOT NULL',
            'terms text'
        )
    )
    db.close()
    log.info('db setup complete')
    
    # blogs
    if not exists('./static/blogs'): mkdir('./static/blogs')
    if not exists('./static/blogs/noblock_noblock.md'):
        with open('./static/blogs/noblock_noblock.md', 'w') as f:
            f.write('# Empty Blog\n\nYou will see this if no block is registered in the database.')

    # info
    log.info('Setup successful, you can change configs in config.json')


def sql() -> None:
    """SQL terminal to interact directly with the database."""
    from src.sql import DB

    # check if database exist
    if not exists(CONFIG.get('db')['path']):
        log.error(f'database doesn\'t exist: {CONFIG.get("db")["path"]}')
        exit(1)

    # start database terminal
    db = DB(CONFIG.get('db')['path'])
    print('You can execute commands on the database now.\bTo exit press: [ctrl] + [C]')
    try:
        while True:
            try: print(f'[-]> {db.execute(input("[+]> "))}')
            except Exception: continue
    except KeyboardInterrupt:
        db.close()


if __name__ == '__main__':
    parser = ArgumentParser(
        usage='python3 run.py [options]',
        epilog='You have to navigate into the WebApp/App directory and execute run.py to run the application.'
    )
    parser.add_argument('--run',        action='store_true', default=False, help='run application')
    parser.add_argument('--cleanup',    action='store_true', default=False, help='clean up everything for a clean and fresh new setup (no functionality)')
    parser.add_argument('--setup',      action='store_true', default=False, help='setup db automatically')
    parser.add_argument('--sql',        action='store_true', default=False, help='start interactive interface for db (no functionality)')
    parser.add_argument('--debug',      action='store_true', default=False, help='activate flask debugging mode')
    args = vars(parser.parse_args()) # parse args and convert to dict

    # update logging config
    if not args['debug']: log.remove_loglist('debug')
    if exists('./config.json'):
        with open('./config.json', 'w') as f:
            CONFIG.update({'log':{'remove':['debug'] if args['debug'] is False else []}})
            dump(CONFIG, f, indent=4)

    if args.get('run'):     run()
    if args.get('cleanup'): cleanup()
    if args.get('setup'):   setup()
    if args.get('sql'):     sql()
