from logging import Logger, Formatter, Handler
from datetime import datetime


logger = Logger('test')
log_handler = Handler()
formatt = Formatter(fmt='', style='{')
log_handler.setFormatter()
logger.addHandler(log_handler)




def log(name:str, msg:str, up:bool=True, print_:bool=True) -> None:
    """Logging messages."""
    text = f'[{name.upper() if up else name}]>[{datetime.now().strftime("%H:%M:%S")}]: {msg}'
    if print_: print(text) # check for params (up, print_)
    else: return text
