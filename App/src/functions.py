from src.logger import Logger
from werkzeug.datastructures import FileStorage
from PIL import Image

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
    
    log.debug(f'cropped image to: {out_img.width=}:{out_img.height=}')
    log.debug(f'save profile image for: {uid}')
    
    if ext in ('png', 'jpeg'):
        out_img.save(f'static/img/profiles/{uid}.{ext}', format=ext)
    else: raise TypeError('type of image isn\'t supported')
