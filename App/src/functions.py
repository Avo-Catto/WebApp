from src.logger import Logger
from src.sql import DB
from src.exception import InvalidBlogIDError, JSONDecodeError
from werkzeug.datastructures import FileStorage
from PIL import Image
from os.path import exists
from os import remove
from markdown import markdown

log = Logger('FunctionsLog')

try:
    with open('./config.json', 'r') as f:
        CONFIG:dict = __import__('json').load(f)
except JSONDecodeError:
    log.critical('failed to load config file')
    exit(1)

# update loglist
log.remove_loglist(*CONFIG.get('log')['remove'])

DB_PATH = CONFIG.get('db')['path']
TABLES = CONFIG.get('db')['tables']


def save_profile_img(uid:str, img:FileStorage) -> None:
    """Save and crop profile image."""
    # obtain and process image
    input_img = Image.open(img.stream)
    ext = input_img.format.lower()
    dif = abs(input_img.width - input_img.height)
    
    # crop image
    if input_img.width > input_img.height:
        out_img = input_img.crop((dif / 2, 0, input_img.width - dif / 2, input_img.height))
    elif input_img.height > input_img.width:
        out_img = input_img.crop((0, dif / 2, input_img.width, input_img.height - dif / 2))
    else: 
        out_img = input_img.crop((dif / 2, 0, input_img.width - dif / 2, input_img.height))
        out_img = input_img.crop((0, dif / 2, input_img.width, input_img.height - dif / 2))

    log.debug(f'cropped image to: {out_img.width=}:{out_img.height=}')
    
    # save or replace image
    if ext in ('png', 'jpeg'):
        if exists(f'static/img/profiles/{uid}.png'): remove(f'static/img/profiles/{uid}.png')
        if exists(f'static/img/profiles/{uid}.jpeg'): remove(f'static/img/profiles/{uid}.jpeg')
        out_img.save(f'static/img/profiles/{uid}.{ext}', format=ext)
        log.debug(f'save profile image for: {uid}')
    else: 
        raise TypeError('file type not supported')


def save_blog_post(uid:str, title:str, blog:str, overwrite=False) -> bool:
    """
    Save blog in file. 
    Returns True if successful and False if blog already exists.
    """
    path = f'static/blogs/{uid}_{title}.md'
    if not exists(path) or overwrite:
        with open(path, 'w') as f:
            f.write(blog)
        log.debug(f'saved blog in: {path}')
        return True
    else: return False


def save_blog_entry(uid:str, username:str, title:str, tags:str) -> None:
    """Save blog data to db."""
    db = DB(DB_PATH)
    db.insert(TABLES['blog'], {
        'unique_id': uid,
        'username': username,
        'title': title,
        'tags': tags,
    })
    db.close()
    log.debug(f'saved blog in db: {username}: {title}')


def load_blog_html(blog_id:str) -> str:
    """Load blog in html format, raise InvalidBlogIDError if blog doesn't exist."""
    if exists(f'static/blogs/{blog_id}.md'):
        with open(f'static/blogs/{blog_id}.md', 'r') as f:
            return markdown(f.read(), output_format='html')
    else: raise InvalidBlogIDError


def load_blog_plain(blog_id:str) -> str:
    """Load blog in plain text, raise InvalidBlogIDError if blog doesn't exist."""
    if exists(f'static/blogs/{blog_id}.md'):
        with open(f'static/blogs/{blog_id}.md', 'r') as f:
            text = f.read().replace('\n\n\n', '\n')
        return text
    else: raise InvalidBlogIDError


def delete_blog_post(blog_id:str) -> bool:
    """
    Deletes file of blog.
    Returns True if successful and False if not.
    """
    try: 
        log.debug(f'delete blog: {blog_id}')
        remove(f'static/blogs/{blog_id}.md')
        return True
    except: 
        return False


def delete_blog_entry(blog_id:str) -> bool:
    """
    Delete blog entry in db.
    Returns True if successful and False if not.
    """
    try:
        blog = blog_id.split('_', 1)
        db = DB(DB_PATH)
        db.delete(TABLES['blog'], f'WHERE unique_id="{blog[0]}" AND title="{blog[1]}"')
        db.close()
        return True
    except (TypeError, IndexError): 
        db.close()
        return False
