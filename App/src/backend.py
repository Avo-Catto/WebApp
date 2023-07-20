# TODO: SQLite can't handle special characters, I have to encode them...
from flask import Flask, render_template, request
from flask_bcrypt import Bcrypt
from src.logger import Logger
from src.sql import DB, create_db

# initzialize required stuff
DB_PATH = 'db/user.db'

log = Logger('FlaskLog', __file__)

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
        log.info('someone signs up')

        creds = {
            'firstname': request.form.get('realname').split()[0],
            'lastname': request.form.get('realname').split()[1],
            'email': request.form.get('email'),
            'username': request.form.get('username'),
            'password': bcrypt.generate_password_hash(request.form.get('password')).decode(),
            'date': request.form.get('date')
        }

        db = DB(DB_PATH)
        db.insert('credentials', creds)
        db.close()

        return render_template('login.html')


@app.route('/login', methods=('GET', 'POST'))
def login() -> str:
    """Login page."""
    if request.method == 'GET':
        return render_template('login.html')
    
    elif request.method == 'POST':
        password = request.form.get('password', type=str)
        email = request.form.get('email', type=str)
        log.debug(f'Password: {password}')

        password_hash = bcrypt.generate_password_hash(password).decode()
        log.debug(f'Password-Hash: {password_hash}')

        # login step

        return render_template('login.html')
    
    else:
        return('<p>Invalid Method!<br>I need an error template...</p>')
    