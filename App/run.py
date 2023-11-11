# to run the app you have to be in the "App" directory
from argparse import ArgumentParser
from json import dump, load, JSONDecodeError
from src.logger import Logger
from os.path import exists
from os import remove, mkdir, listdir
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
        epilog='You have to navigate into the WebApp/App directory and execute run.py to run the application.'
    )
    parser.add_argument('--run', action='store_true', default=False, help='run application')
    parser.add_argument('--cleanup', action='store_true', default=False, help='clean up everything for a clean and fresh new setup (no functionality)')
    parser.add_argument('--setup', action='store_true', default=False, help='setup db automatically')
    parser.add_argument('--sql', action='store_true', default=False, help='start interactive interface for db (no functionality)')
    parser.add_argument('--debug', action='store_true', default=False, help='activate flask debugging mode')
    args = vars(parser.parse_args()) # parse args and convert to dict
    log.debug(f'args: {args}')


    # why do I have this?
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
            app.run(CONFIG.get('run')['address'], CONFIG.get('run')['port'], debug=args['debug'])
        
        except Exception as e:
            log.error(f'the application couldn\'t be started because of error: {e.__str__()}')
            log.info('This error occured probably, because of an error in the code or the application wasn\'t set up properly. If so, please run: python3 run.py --setup')
            session_clean_proc.terminate()
    

    if args.get('cleanup'):
        print('You are about to clean up the whole application.')
        if input('Are you sure you want to proceed? [y/n] ').lower() != 'y': 
            exit()

        try: map(lambda x: remove(f'./static/blogs/{x}'), listdir('./static/blogs'))
        except Exception as e: 
            
            log.warning(f'exception caught at deleting blogs: {e.__str__()}')
        try: map(lambda x: remove(f'./static/img/profiles/{x}') if x != 'anonymous.png' else ..., listdir('./static/img/profiles'))
        except Exception as e: 
            log.warning(f'exception caught at deleting profile images: {e.__str__()}')

        try: remove(CONFIG.get('db')['path'])
        except Exception as e: 
            if e.__str__() != "'NoneType' object is not subscriptable":
                log.warning(f'exception caught at deleting db: {e.__str__()}')

        try: remove('./config.json')
        except Exception as e: 
            log.warning(f'exception caught at deleting configs: {e.__str__()}')

        log.debug(listdir('./static/img/profiles'))


    if args.get('setup'):
        from src.sql import DB
        print('You are about to setup configs and databases for the application.')
        if input('Are you sure you want to proceed? [y/n] ').lower() != 'y': 
            exit()
        
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
                'address': '127.0.0.1',
                'port': 8080
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
        db._create_table( # blog table
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

        # save config to file
        with open('./config.json', 'w') as f:
            dump(CONFIG, f, indent=4)
        
        # blogs
        if not exists('./static/blogs'): mkdir('./static/blogs')

        if not exists('./static/blogs/noblock_noblock.md'):
            with open('./static/blogs/noblock_noblock.md', 'w') as f:
                f.write('# Empty Blog\n\nYou will see this if no block is registered in the database.')

        # info
        log.info('Setup successful, you can change configs in config.json')


# TODO: customizable port and host?
# TODO: fix auto submit credentials if you try to change site (signup & login sites)
# TODO: credits of freepic for profile image <a href="https://www.flaticon.com/de/kostenlose-icons/katze" title="katze Icons">Katze Icons erstellt von Freepik - Flaticon</a>
# TODO: the change profile input button should show that an image is selected
# TODO: make debugger mode global
# TODO: fix cleanup option