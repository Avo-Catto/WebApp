from flask import Flask, render_template, request, make_response, redirect
from flask_bcrypt import Bcrypt
from src.logger import Logger
from src.sql import DB
from src.exception import IntegrityError, NoSessionError, InvalidBlogIDError, JSONDecodeError, UserNotFoundError
from src.session import add_session, get_session_data, remove_session
from src.functions import save_profile_img, save_blog_post, save_blog_entry, load_blog_html, load_blog_plain, delete_blog_entry, delete_blog_post
from hashlib import sha256
from uuid import uuid4
from datetime import datetime, timedelta
from os.path import exists
from random import choices
from urllib.parse import quote

log = Logger('FlaskLog')

# load config
try:
    with open('./config.json', 'r') as f:
        CONFIG:dict = __import__('json').load(f)
except JSONDecodeError:
    log.critical('failed to load config file')
    exit(1)

# settings & vars
log.remove_loglist(*CONFIG.get('log')['remove'])

DB_PATH = CONFIG.get('db')['path']
TABLES = CONFIG.get('db')['tables']
COOKIE_LIFETIME = CONFIG.get('vars')['cookie_livetime'] # 86400 seconds = 24 hours

app = Flask(
    import_name=__name__,
    static_folder='../static/',
    template_folder='../templates/'
)
bcrypt = Bcrypt(app)


# flask paths
@app.route('/', methods=('GET',))
def index() -> str:
    """Root path."""
    return redirect('/explore')


@app.route('/signup', methods=('GET', 'POST'))
def signup() -> str:
    """Signup path."""
    if request.method == 'GET':
        return render_template('signup.html')
    
    elif request.method == 'POST':
        # obtain post data and process it
        password = bcrypt.generate_password_hash(request.form.get('password')).decode()
        username = request.form.get('username')
        len_realname = len(request.form.get('realname').split())
        creds = {
            'unique_id': sha256(f'{password}{username}{uuid4().hex}'.encode()).hexdigest(),
            'firstname': request.form.get('realname').split()[0],
            'lastname': ' '.join(request.form.get('realname').split()[1:len_realname]) if len_realname > 1 else None,
            'email': request.form.get('email'),
            'username': username,
            'password': password,
        }
        # insert data into db
        db = DB(DB_PATH)
        try: db.insert(TABLES['user-data'], creds)
        except IntegrityError: 
            log.debug('creating new account failed: email already registered')
            return error('DB entry already exist.', 'The provided email does exist already.', '/signup')
        db.close()
        log.debug('created new account')

        return render_template('login.html')


@app.route('/login', methods=('GET', 'POST'))
def login() -> str:
    """Login path."""
    if request.method == 'GET':
        return render_template('login.html')
    
    elif request.method == 'POST':
        # obtain post data
        email = request.form.get('email')
        password = request.form.get('password')
        # obtain account data from db
        db = DB(DB_PATH)
        try: 
            password_hash, unique_id, username, email, firstname, lastname = db.select(
                TABLES['user-data'], ('password', 'unique_id', 'username', 'email', 'firstname', 'lastname'), 
                f'WHERE "{email}" = email')[0]
            realname = f'{firstname} {lastname if lastname is not None else ""}'
        except TypeError: password_hash = None
        db.close()
        # check password hash
        if password_hash is not None:
            if bcrypt.check_password_hash(password_hash, password):
                log.debug('login succeed')
                # generate and set session cookie
                session = uuid4().hex
                expires = datetime.now() + timedelta(seconds=COOKIE_LIFETIME)
                response = make_response(redirect('/profile'))
                response.set_cookie(key='session', value=session, max_age=COOKIE_LIFETIME, expires=expires, secure=True, httponly=True, samesite='Strict')
                log.debug('session cookie set')
                # add session cookie to db
                add_session(unique_id, session, expires, username, email, realname)
                log.debug('session cookie added')
                return response
            else:
                log.debug('login failed: wrong password')
                return error('Authentication Failed', 'Your credentials are not valid.', '/login')
        else:
            log.debug('login failed: email doesn\' match')
            return error('Authentication Failed', 'The email doesn\'t exist in the database.', '/login')
    else: 
        return error('Invalid Method', 'The used http message isn\'t allowed.', '/login')


@app.route('/logout', methods=('GET',))
def logout() -> redirect:
    """Logout path."""
    if request.method == 'GET':
        # remove session cookie from browser and db
        try: remove_session(request.cookies.get('session'))
        except NoSessionError: pass
        resplonse = make_response(success('Logout Succeed', 'You were logged out successfully.', '/explore'))
        resplonse.delete_cookie('session')
        return resplonse
    else:
        return error('Invalid Method', 'The used http message isn\'t allowed.', '/explore')


@app.route('/profile', methods=('GET', 'POST'))
def profile() -> str:
    """Profile path."""
    if request.method == 'GET':
        try:
            if request.args.get('view'):
                # view account
                log.debug('view account')
                unique_id = request.args.get('view')
                if unique_id == 'noblock': raise NoSessionError
                db = DB(DB_PATH)
                try:
                    # obtain data about account
                    username, firstname, lastname, email = db.select(TABLES['user-data'], ('username', 'firstname', 'lastname', 'email'), f'WHERE unique_id="{unique_id}"')[0]
                    realname = f'{firstname} {lastname}'
                except TypeError: raise UserNotFoundError
                db.close()
            else:
                # obtain session data
                unique_id, username, email, realname = get_session_data(request.cookies.get('session'), ('unique_id', 'username', 'email', 'realname'))

        except UserNotFoundError:
            return error('User Not Found', 'The requested user wasn\'t found.')

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

            # load blogs for side bar
            db = DB(DB_PATH)
            blogs = db.select(TABLES.get('blog'), ('unique_id', 'title'), where=f'WHERE unique_id="{unique_id}"')
            try: blogs = tuple(map(lambda b: (quote(f'{b[0]}_{b[1]}'), b[1]), blogs))
            except TypeError: blogs = ()
            db.close()

        return render_template('profile.html', profile_img=profile_img, username=username, email=email, realname=realname, blogs=blogs)

    elif request.method == 'POST': 
        # update profile
        try: 
            # obtain session data and hash password
            unique_id, username, email, realname = get_session_data(request.cookies.get('session'), ('unique_id', 'username', 'email', 'realname'))
            db = DB(DB_PATH)
            password_hash = db.select(TABLES['user-data'], 'password', f'WHERE "{unique_id}" = unique_id')[0][0]
            db.close()

            data = dict()
            # obtain update data that doesn't require a password
            if request.files.get('update-img').filename != '':
                try: 
                    save_profile_img(unique_id, request.files.get('update-img'))
                    data.update({'img': True}) # only to check if profile image was updated
                except TypeError: 
                    return error('Invalid Filetype', 'The filetype for the image isn\'t allowed.', '/profile')
            if request.form.get('username') != username: 
                data.update({'username': request.form.get('username')})
            
            # obtain update data that requires a password
            if request.form.get('password') != '':
                if bcrypt.check_password_hash(password_hash, request.form.get('password')):
                    if request.form.get('realname') != '':
                        name = request.form.get('realname').split()
                        data.update({'firstname': name[0], 'lastname': ' '.join(name[1:len(name)]) if len(name) > 1 else None})
                    if request.form.get('email') != '':
                        data.update({'email': request.form.get('email')})
                    if request.form.get('newpassword') != '':
                        data.update({'password': bcrypt.generate_password_hash(request.form.get('newpassword')).decode()})
                else: 
                    return error('Wrong Password', 'The given password didn\'t match.', '/profile')

            # if update
            if len(data) > 0:
                try: data.pop('img')
                except KeyError: pass
                
                if len(data) > 0:
                    # update profile
                    db = DB(DB_PATH)
                    db.update(TABLES['user-data'], data, f'WHERE "{unique_id}" = unique_id')
                    db.close()

                    # update session
                    session = uuid4().hex
                    expires = datetime.now() + timedelta(seconds=COOKIE_LIFETIME)
                    response = make_response(success('Update Profile', 'Your profile was updated successful', '/profile'))
                    response.set_cookie(key='session', value=session, max_age=COOKIE_LIFETIME, expires=expires, secure=True, httponly=True, samesite='Strict')
                    add_session(unique_id, session, expires, 
                                username if data.get('username') is None and data.get('username') != username else data.get('username'),
                                email if data.get('email') is None and data.get('email') != email else data.get('email'),
                                realname if data.get('firstname') != realname.split()[0] else f"{data.get('firstname')} {'' if data.get('lastname') is None else data.get('lastname')}" # I know it's a bad habit
                            )
                    log.debug('account updated')
                    
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
    """Explore path."""
    if request.method == 'GET':
        if request.args.get('blog'): 
            # read blog
            try:
                blog_id = request.args.get('blog')
                uid = blog_id.split("_")[0]
                # check if author for options to edit or delete the blog
                try:
                    unique_id = get_session_data(request.cookies.get('session'), 'unique_id')[0]
                    authorized = True if unique_id == uid else False
                except NoSessionError: 
                    authorized = False
                # handle link to profile of author
                try: 
                    db = DB(DB_PATH)
                    username = db.select(TABLES['blog'], 'username', f'WHERE unique_id="{uid}"')[0][0]
                    db.close()
                except TypeError: 
                    db.close()
                    username = 'anonymous'
                # return blog
                log.debug(f'requested blog: {blog_id}')
                return render_template('read.html', blog=load_blog_html(blog_id), unique_id=uid, username=username, authorized=authorized, blog_id=blog_id)
            
            except InvalidBlogIDError:
                return error('Blog not found', 'The requested blog wasn\'t found.', '/explore')
        
        elif request.args.get('search'):
            # search for blog
            title = []
            tags = []
            # filter tags and title
            for i in request.args.get('search').split():
                if i.startswith('#'): tags.append(i.removeprefix('#'))
                else: title.append(i)
            try:
                db = DB(DB_PATH)
                # build where statement
                title_statement = f'title LIKE \"%{" ".join(title) if title else ""}%\"' if len(title) != 0 else ''
                tags_statement = 'tags LIKE "%{}%" AND ' * len(tags)
                where_statement = f'WHERE {title_statement}{" AND " if title and tags else ""}{tags_statement}'.format(*tags).removesuffix(' AND ')
                # select matching blogs from db
                blogs = db.select(TABLES['blog'], ('unique_id', 'title'), where=where_statement)
                blogs = tuple(map(lambda b: (quote(f'{b[0]}_{b[1]}'), b[1]), blogs)) # fromat blog info for url
                db.close()
                # return results
                log.debug(f'Search results: {len(blogs)}')
                return render_template('explore.html', blogs=blogs)
            
            except TypeError:
                db.close()
                return error('No Blog Found', 'No blog was found.', '/explore')
        
        else:
            # get random blogs
            db = DB(DB_PATH)
            db_res = db.select(TABLES['blog'], ('unique_id', 'title'))
            if db_res is not None: blogs = choices(db_res, k=5)
            else: blogs = (('noblock', 'noblock'),)
            blogs = tuple(map(lambda b: (quote(f'{b[0]}_{b[1]}'), b[1]), blogs)) # fromat blog info for url
            db.close()
            return render_template('explore.html', blogs=blogs)
    else: 
        return error('Invalid Method', 'The used http message isn\'t allowed.', '/explore')


@app.route('/blog/<route>', methods=('GET', 'POST'))
def blog(route) -> str:
    """Blog path."""
    if request.method == 'GET':
        if route == 'write':
            return render_template('write.html', title='', tags='', blog='')
        
        elif route == 'edit':
            # edit existing blog
            try:
                blog_id = request.args.get('id')
                unique_id_blog = blog_id.split('_')[0]
                title = blog_id.split('_', 1)[1]
            except: return error('Couldn\'t load Blog', 'An error occured by loading the blog data.', '/')
            
            # authentication validation
            try: unique_id = get_session_data(request.cookies.get('session'), 'unique_id')[0]
            except NoSessionError: return error('No Session', 'You have to be logged in to perform blog actions.', '/')
            if blog_id.split('_')[0] != unique_id: return error('Action Not Permitted', 'The action is not permitted.', '/')
            
            # obtain relevant data of blog from db
            db = DB(DB_PATH)
            tags = db.select(TABLES['blog'], 'tags', f'WHERE unique_id="{unique_id_blog}" AND title="{title}"')[0][0]
            db.close()

            # load blog in plain text and return html
            try: blog = load_blog_plain(blog_id)
            except InvalidBlogIDError: return error('Blog not found', 'The requested blog wasn\'t found.', '/')
            finally: return render_template('write.html', title=title, tags=tags, blog=blog)
        
        elif route == 'delete':
            # delete blog
            try:
                blog_id = request.args.get('id')
                # authentication validation
                try: unique_id = get_session_data(request.cookies.get('session'), 'unique_id')[0]
                except NoSessionError: return error('No Session', 'You have to be logged in to perform blog actions.', '/')
                if blog_id.split('_')[0] == unique_id:

                    # delete blog entry in db and file
                    if all((delete_blog_entry(blog_id), delete_blog_post(blog_id))):
                        log.debug(f'deleted blog: {blog_id}')
                        return success('Blog Deleted', 'The blog was deleted successfully', '/explore')
                    else: return error('Blog not Deleted', 'The blog couldn\'t be deleted.', '/')
                else: return error('Action Not Permitted', 'The action is not permitted.', '/')
            
            except Exception as e:
                log.error(f'Major Error: {e.__str__()}')
                return error('Major Error', 'An unexpected error occured, please contact the Admin.', '/')

    
    elif request.method == 'POST':
        if route == 'write' or 'edit':
            # write or edit blog
            try: 
                # obtain blog data
                unique_id, username = get_session_data(request.cookies.get('session'), ('unique_id', 'username'))
                title = request.form.get('title')
                tags = request.form.get('tags')
                blog = request.form.get('blog')
                log.debug(f'user posted blog: {unique_id} - {title}')

                if route == 'edit':
                    # delete blog data for replacing with edited blog
                    try:
                        blog_id = request.args.get('id')
                        delete_blog_post(blog_id)
                        delete_blog_entry(blog_id)
                    except: pass
                # save blog
                if save_blog_post(unique_id, title, blog, overwrite=True if route == 'edit' else False):
                    save_blog_entry(unique_id, username, title, tags)
                    log.debug(f'blog saved: {title}')
                    return success('Post Blog', 'Your blog was posted successfully', '/explore')
                else: 
                    return error('Blog Exists', 'You already have a blog with the same name.', '/blog')

            except NoSessionError:
                return error('No Session', 'You have to be logged in to update your profile.', '/blog/write')
    else: 
        return error('Invalid Method', 'The used http message isn\'t allowed.', '/blog')


@app.route('/navbar', methods=('GET',))
def navbar() -> str:
    """Loads the navigation bar."""
    return render_template('navbar.html', session=True if request.cookies.get('session') else False)


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
