from flask import Flask, render_template, request, make_response
from flask_bcrypt import Bcrypt
from src.logger import Logger
from src.sql import DB
from src.exception import IntegrityError
from hashlib import sha256
from uuid import uuid4
from datetime import datetime, timedelta

# initzialize required stuff
with open('./config.json', 'r') as f:
    CONFIG:dict = __import__('json').load(f)

DB_PATH = CONFIG.get('db')['path']
TABLES = CONFIG.get('db')['tables']
COOKIE_LIFETIME = 60*60*24 # 86400 seconds = 24 hours

log = Logger('FlaskLog')

app = Flask(
    import_name=__name__,
    static_folder='../static/',
    template_folder='../templates/'
)
bcrypt = Bcrypt(app)


# main flask app
@app.route('/')
def index() -> str:
    """Root page."""
    return render_template('index.html')


@app.route('/signup', methods=('GET', 'POST'))
def signup() -> str:
    """Signup page."""
    if request.method == 'GET':
        return render_template('signup.html')
    
    elif request.method == 'POST':
        password = bcrypt.generate_password_hash(request.form.get('password')).decode()
        username = request.form.get('username')
        creds = {
            'unique_id': sha256(f'{password}{username}{uuid4().hex}'.encode()).hexdigest(),
            'firstname': request.form.get('realname').split()[0],
            'lastname': request.form.get('realname').split()[1],
            'email': request.form.get('email'),
            'username': username,
            'password': password,
            'date': request.form.get('date')
        }
        db = DB(DB_PATH)
        db.insert(TABLES['user-data'], creds)
        db.close()
        log.debug(f'account was created successful: {DB_PATH}')

        return render_template('login.html')


@app.route('/login', methods=('GET', 'POST'))
def login() -> str:
    """Login page."""
    if request.method == 'GET':
        return render_template('login.html')
    
    elif request.method == 'POST':
        email = request.form.get('email', type=str)
        password = request.form.get('password', type=str)

        db = DB(DB_PATH)
        try: password_hash, unique_id, username = db.select(TABLES['user-data'], ('password', 'unique_id', 'username'), f'"{email}" = email')
        except TypeError: password_hash = None
        if password_hash is not None:
            if bcrypt.check_password_hash(password_hash, password):
                log.debug(f'successful login: retrieved data from user from db: {DB_PATH}')
                
                # generate and set session cookie
                session = uuid4().hex
                expires = datetime.now() + timedelta(seconds=COOKIE_LIFETIME) # FIXME: Session cookie ends now XD
                log.debug(f'--->>> Expires: {expires}')
                response = make_response(render_template('profile.html', message=f'You are logged in as {username}!')) # only for testing purpose
                response.set_cookie(key='session', value=session, max_age=COOKIE_LIFETIME, expires=expires, secure=True, httponly=True, samesite='Strict')
                
                # add session cookie to session table
                data = {
                    'unique_id': unique_id,
                    'session_id': session,
                    'expiration': expires,
                    'username': username
                }
                try: db.insert(TABLES['session'], data)
                except IntegrityError: 
                    log.warning('session already active')
                    log.info(f'exceptions handled in db: {db.path} table: {TABLES["session"]}')
                    db.delete(TABLES['session'], f'unique_id = "{unique_id}"')
                    db.insert(TABLES['session'], data)
                db.close()
                return response
            else:
                log.debug(f'login failed: wrong password for email: {email}') # send message to front-end
                db.close()
                return render_template('login.html')
        else:
            log.debug(f'login failed: email doesn\' match: {email}') # send message to front-end
            db.close()
            return render_template('signup.html')
    
    else:
        return('<p>Invalid Method!<br>I need an error template...</p>')


# TODO: fix auto submit credentials if you try to change site (signup & login sites)
# TODO: add session cookie functionality?
# TODO: Messages in template, for example: "You don't have any Account" or "Login failed"
# TODO: Error template
# TODO: I see a lot of uncatched exceptions, HELP!!!