from src.logger import Logger
from werkzeug.datastructures import FileStorage

log = Logger('FunctionsLog')

def save_profile_img(uid:str, filestorage:FileStorage) -> None:
    """Save profile image."""
    log.debug(f'{uid}: {filestorage}')
    ftype = filestorage.content_type.split('/') # ["image", "png"/"jpg"]
    if ftype[0] == 'image' and any((ftype[1] == 'png', ftype[1] == 'jpg')):
        with open(f'static/img/profiles/{uid}.{ftype[1]}', 'wb') as f:
            f.write(filestorage.stream.read())
            log.debug(f'saved profile image for: {uid}')
    elif filestorage.content_type == 'application/octet-stream': pass
    else: raise TypeError('type of image isn\'t allowed')
