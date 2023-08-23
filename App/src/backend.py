from flask import Flask, render_template, request, make_response, redirect
from flask_bcrypt import Bcrypt
from src.logger import Logger
from src.sql import DB
from src.exception import IntegrityError, NoSessionError
from src.session import add_session, get_session_data
from src.functions import save_profile_img
from hashlib import sha256
from uuid import uuid4
from datetime import datetime, timedelta
from os.path import exists

# initzialize required stuff
with open('./config.json', 'r') as f:
    CONFIG:dict = __import__('json').load(f)

DB_PATH = CONFIG.get('db')['path']
TABLES = CONFIG.get('db')['tables']
COOKIE_LIFETIME = CONFIG.get('vars')['cookie_livetime'] # 86400 seconds = 24 hours

log = Logger('FlaskLog')

app = Flask(
    import_name=__name__,
    static_folder='../static/',
    template_folder='../templates/'
)
bcrypt = Bcrypt(app)


# main flask app
@app.route('/', methods=('GET',))
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
        foo = len(request.form.get('realname').split())
        creds = {
            'unique_id': sha256(f'{password}{username}{uuid4().hex}'.encode()).hexdigest(),
            'firstname': request.form.get('realname').split()[0],
            'lastname': request.form.get('realname').split()[1] if foo > 1 else None,
            'email': request.form.get('email'),
            'username': username,
            'password': password,
        }
        db = DB(DB_PATH)
        try: db.insert(TABLES['user-data'], creds)
        except IntegrityError: 
            log.info('handled exception successful')
            return error('DB entry already exist.', 'The provided email does already exists.', '/signup')
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
        try: password_hash, unique_id, username = db.select(TABLES['user-data'], ('password', 'unique_id', 'username'), f'WHERE "{email}" = email')[0]
        except TypeError: password_hash = None
        db.close()
        if password_hash is not None:
            if bcrypt.check_password_hash(password_hash, password):
                log.debug(f'successful login: retrieved data from user from db: {DB_PATH}')
                
                # generate and set session cookie
                session = uuid4().hex
                expires = datetime.now() + timedelta(seconds=COOKIE_LIFETIME)
                response = make_response(redirect('/profile'))
                response.set_cookie(key='session', value=session, max_age=COOKIE_LIFETIME, expires=expires, secure=True, httponly=True, samesite='Strict')
                # add session cookie to session table
                add_session(unique_id, session, expires, username)
                return response
            else:
                log.debug(f'login failed: wrong password for email: {email}')
                return error('Authentication Failed', 'Your credentials are not valid.', '/login')
        else:
            log.debug(f'login failed: email doesn\' match: {email}')
            return error('Authentication Failed', 'The email doesn\'t exist in the database.', '/login')
    else:
        return error('Invalid Method', 'The used http message isn\'t allowed.', '/login')


@app.route('/profile', methods=('GET', 'POST'))
def profile() -> str:
    """Profile page."""
    if request.method == 'GET':
        try: # get session stored data
            unique_id, username = get_session_data(request.cookies.get('session'), ('unique_id', 'username'))
        except NoSessionError: 
            unique_id = 'anonymous'
            username = 'Anonymous'
        finally: 
            # check if profile image was uploaded or use default
            if exists(f'static/img/profiles/{unique_id}.png'):
                profile_img = f'{unique_id}.png'
            elif exists(f'static/img/profiles/{unique_id}.jpg'):
                profile_img = f'{unique_id}.jpg'
            else: profile_img = 'anonymous.png'

        return render_template('profile.html', profile_img=profile_img, username=username)
    
    elif request.method == 'POST':
        try: 
            unique_id = get_session_data(request.cookies.get('session'), 'unique_id')[0]
            try:
                save_profile_img(unique_id, request.files.get('update-img'))
                log.debug('profile was updated')
                return success('Update Profile', 'Your profile was updated successful.', '/profile')
            except TypeError: 
                return error('Invalid Filetype', 'The filetype for the image isn\'t allowed.', '/profile')
        except NoSessionError: 
            return error('No Session', 'You have to be logged in to update your profile.', '/profile')
    
    else: 
        return error('Invalid Method', 'The used http message isn\'t allowed.', '/login')


def success(success:str, message:str, _continue:str) -> str:
    """
    Custom "Operation Succeed" page with message.
    :success: success title
    :message: info about success
    :_continue: redirect url
    """
    return render_template('success.html', success=success, message=message, _continue=_continue)


def error(error:str, message:str, back:str) -> str:
    """
    Custom error page with message.
    :error: error name in header
    :message: info about error
    :back: redirect url
    """
    return render_template('error.html', error=error, message=message, back=back)


@app.errorhandler(404)
def page_not_found(e):
    """Custom error 404 page."""
    return render_template('404.html'), 404

# TODO: add functionality for multiple image types
# TODO: create folder for every user for images
# TODO: fix image size
