from src.logger import Logger
from src.sql import DB
from src.exception import InvalidBlogIDError
from werkzeug.datastructures import FileStorage
from PIL import Image
from os.path import exists
from os import remove
from markdown import markdown

# initial stuff
with open('./config.json', 'r') as f:
    CONFIG:dict = __import__('json').load(f)

DB_PATH = CONFIG.get('db')['path']
TABLES = CONFIG.get('db')['tables']

log = Logger('FunctionsLog')

# profile image functions
def save_profile_img(uid:str, img:FileStorage) -> None:
    """Save and crop profile image."""
    input_img = Image.open(img.stream)
    ext = input_img.format.lower()
    dif = abs(input_img.width - input_img.height) # calc difference
    
    if input_img.width > input_img.height:
        out_img = input_img.crop((dif / 2, 0, input_img.width - dif / 2, input_img.height))
    elif input_img.height > input_img.width:
        out_img = input_img.crop((0, dif / 2, input_img.width, input_img.height - dif / 2))
    else: 
        out_img = input_img.crop((dif / 2, 0, input_img.width - dif / 2, input_img.height))
        out_img = input_img.crop((0, dif / 2, input_img.width, input_img.height - dif / 2))

    log.debug(f'cropped image to: {out_img.width=}:{out_img.height=}')
    log.debug(f'save profile image for: {uid}')
    
    if ext in ('png', 'jpeg'):
        if exists(f'static/img/profiles/{uid}.png'): remove(f'static/img/profiles/{uid}.png')
        if exists(f'static/img/profiles/{uid}.jpeg'): remove(f'static/img/profiles/{uid}.jpeg')
        out_img.save(f'static/img/profiles/{uid}.{ext}', format=ext)
    else: raise TypeError('type of image isn\'t supported')


def save_blog_post(uid:str, title:str, blog:str) -> bool:
    """
    Save blog in file. 
    Return True if successful and False if blog already exists.
    """
    path = f'static/blogs/{uid}_{title}.md'
    log.debug(f'save blog post: {path}')
    if not exists(path):
        with open(path, 'w') as f:
            f.write(blog)
        log.info(f'saved blog sucessfully: {path}')
        return True
    else: 
        log.warning(f'failed to save blog: {path}')
        return False


def save_blog_entry(uid:str, username:str, title:str, terms:str) -> None:
    """Save blog data to db."""
    log.info(f'save blog entry for: {username}: {title}')
    db = DB(DB_PATH)
    db.insert(TABLES['blog'], {
        'unique_id': uid,
        'username': username,
        'title': title,
        'terms': terms
    })
    db.close()


def load_blog(blog_id:str) -> str:
    """Load blog, raise InvalidBlogIDError if blog doesn't exist."""
    if exists(f'static/blogs/{blog_id}.md'):
        with open(f'static/blogs/{blog_id}.md', 'r') as f:
            return markdown(f.read(), output_format='html')
    else: raise InvalidBlogIDError
