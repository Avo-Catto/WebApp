from flask import Flask, render_template, request, make_response, redirect
from flask_bcrypt import Bcrypt
from src.logger import Logger
from src.sql import DB
from src.exception import IntegrityError, NoSessionError
from src.session import add_session, get_session_data
from src.functions import save_profile_img, save_blog_post
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
        try: 
            password_hash, unique_id, username, email, firstname, lastname = db.select(
                TABLES['user-data'], ('password', 'unique_id', 'username', 'email', 'firstname', 'lastname'), 
                f'WHERE "{email}" = email')[0]
            realname = f'{firstname} {lastname if lastname is not None else ""}'
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
                add_session(unique_id, session, expires, username, email, realname)
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
            unique_id, username, email, realname = get_session_data(request.cookies.get('session'), ('unique_id', 'username', 'email', 'realname'))
        except NoSessionError: 
            unique_id = 'anonymous'
            username = 'Anonymous'
            email = 'anonymous@tech.blog'
            realname = 'Bob Thomas'
        finally: 
            # check if profile image was uploaded or use default
            if exists(f'static/img/profiles/{unique_id}.png'):
                profile_img = f'{unique_id}.png'
            elif exists(f'static/img/profiles/{unique_id}.jpeg'):
                profile_img = f'{unique_id}.jpeg'
            else: profile_img = 'anonymous.png'

        return render_template('profile.html', profile_img=profile_img, username=username, email=email, realname=realname)
    
    elif request.method == 'POST':
        try: 
            log.debug('access session data')
            unique_id, username, email, realname = get_session_data(request.cookies.get('session'), ('unique_id', 'username', 'email', 'realname'))

            db = DB(DB_PATH)
            password_hash = db.select(TABLES['user-data'], 'password', f'WHERE "{unique_id}" = unique_id')[0][0]
            db.close()

            data = dict()
            # gather update data that doesn't require a password
            if request.files.get('update-img').filename != '':
                try: 
                    save_profile_img(unique_id, request.files.get('update-img'))
                    data.update({'img': True}) # only to check if profile image was updated
                except TypeError: 
                    return error('Invalid Filetype', 'The filetype for the image isn\'t allowed.', '/profile')
            if request.form.get('username') != username: 
                data.update({'username': request.form.get('username')})
            
            # gather update data that requires a password
            if request.form.get('password') != '':
                if bcrypt.check_password_hash(password_hash, request.form.get('password')):
                    if request.form.get('realname') != '':
                        name = request.form.get('realname').split()
                        data.update({'firstname': name[0], 'lastname': name[1] if len(name) > 1 else None})
                        del name
                    if request.form.get('email') != '':
                        data.update({'email': request.form.get('email')})
                    if request.form.get('newpassword') != '':
                        data.update({'password': bcrypt.generate_password_hash(request.form.get('newpassword')).decode()})
                else: 
                    return error('Wrong Password', 'The given password didn\'t match.', '/profile')

            # update profile data
            log.debug(f'user updated profile: {data}')
            if len(data) > 0:
                try: data.pop('img')
                except KeyError: pass
                
                if len(data) > 0:
                    db = DB(DB_PATH)
                    db.update(TABLES['user-data'], data, f'WHERE "{unique_id}" = unique_id')
                    log.debug(f'updated successful user data for unique_id: {unique_id}')
                    db.close()

                    # update session
                    session = uuid4().hex
                    expires = datetime.now() + timedelta(seconds=COOKIE_LIFETIME)
                    response = make_response(success('Update Profile', 'Your profile was updated successful', '/profile'))
                    response.set_cookie(key='session', value=session, max_age=COOKIE_LIFETIME, expires=expires, secure=True, httponly=True, samesite='Strict')
                    add_session(unique_id, session, expires, 
                                username if data.get('username') is None and data.get('username') != username else data.get('username'),
                                email if data.get('email') is None and data.get('email') != email else data.get('email'),
                                realname if data.get('firstname') != realname.split()[0] else f"{data.get('firstname')} {'' if data.get('lastname') is None else data.get('lastname')}" # maybe buggy?
                            )
                    
                    return response
                return success('Update Profile', 'Your profile was updated successfully', '/profile')
            else:
                return redirect('/profile')
        except NoSessionError: 
            return error('No Session', 'You have to be logged in to update your profile.', '/profile')
    else: 
        return error('Invalid Method', 'The used http message isn\'t allowed.', '/login')


@app.route('/explore', methods=('GET',))
def explore() -> str:
    """Explore page."""
    return render_template('explore.html')


@app.route('/write', methods=('GET', 'POST'))
def write() -> str:
    """Write page."""
    if request.method == 'GET':
        return render_template('write.html')
    
    elif request.method == 'POST':
        try: 
            unique_id = get_session_data(request.cookies.get('session'), 'unique_id')[0]
            title = request.form.get('title')
            terms = request.form.get('terms')
            blog = request.form.get('blog')
            log.debug(f'user posted blog: {unique_id} - {title}')
            
            # save that stuff
            save_blog_post(unique_id, title, blog)

            return success('Post Blog', 'Your blog was posted successfully', '/explore')

        except NoSessionError:
            return error('No Session', 'You have to be logged in to update your profile.', '/write')
    else:
        return error('Invalid Method', 'The used http message isn\'t allowed.', '/write')


@app.route('/read', methods=('GET',))
def read() -> str:
    """Read blog page."""
    log.debug(request.args.get('blog'))
    return render_template('read.html')


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

# TODO: write better code!
# TODO: images don't become overwritten because of different extensions
# TODO: display blog posts