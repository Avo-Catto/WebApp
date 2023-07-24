# TODO: catch exceptions
from flask import Flask, render_template, request, make_response
from flask_bcrypt import Bcrypt
from src.logger import Logger
from src.sql import DB
from hashlib import sha256
from uuid import uuid4

# initzialize required stuff
DB_PATH = 'db/user.db'
COOKIE_LIFETIME = 60*60*24 # seconds (lives for 24 hours)

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
        db.insert('credentials', creds)
        db.commit()
        db.close()

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
        password_hash = db.select('credentials', 'password', f'"{email}" = email')
        log.debug(f'password hash: {password_hash[0]}')
        if len(password_hash) == 1:
            if bcrypt.check_password_hash(password_hash[0], password):
                user_data = db.select('credentials', '*', f'"{email}" = email')
                log.debug(f'successful login: retrieved data from db: {DB_PATH}: {user_data}')
                db.close()
                # generate and set session cookie
                session = uuid4().hex
                response = make_response(render_template('profile.html'))
                response.set_cookie(key='session', value=session, max_age=COOKIE_LIFETIME, secure=True, httponly=False, samesite='Strict')
                return response
            else:
                log.debug(f'login failed: wrong password for email: {email}')
                db.close()
                return render_template('login.html')
        else:
            log.debug(f'login failed: email doesn\' match: {email}')
            db.close()
            return render_template('signup.html')
    
    else:
        return('<p>Invalid Method!<br>I need an error template...</p>')


# TODO: add session cookie functionality?
# TODO: Messages in template, for example: "You don't have any Account" or "Login failed"
# TODO: Error template
