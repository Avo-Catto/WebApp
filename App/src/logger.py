from datetime import datetime
from src.exception import TypeNameLogError

class Colors:
    """ANSI color codes"""
    def __init__(self) -> None:
        if self.__check_sys():
            self.__fix_colors_windows()
        
        self.RESET = '\033[0m'
        self.RED = '\033[0;31m'
        self.RED_BOLD = '\033[1;31m'
        self.GREEN = '\033[32m'
        self.YELLOW = '\033[33m'
        self.BLUE = '\033[0;34m'

    def __fix_colors_windows(self) -> None:
        """Fixing colors for windows."""
        kernel32 = __import__('ctypes').WinDLL('kernel32')
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        del kernel32
    
    def __check_sys(self) -> bool:
        """Check for system."""
        ops = __import__('platform').system()
        if ops == 'Windows': 
            del ops
            return True
        else: 
            del ops
            return False

colors = Colors()


class Logger:
    def __init__(self, name:str, file:str, loglist:list = ['info', 'debug', 'warning', 'error', 'critical']) -> None:
        """Initialize logger and only log messages in loglist."""
        self.name = name
        self.file = file
        self.loglist = loglist
    
    def _build_message(self, msg:str, typename:str) -> str:
        """Build log string."""
        return f'[{datetime.now().strftime("%d.%m.%Y|%H:%M:%S")}]-[{typename.upper()}]-[{self.name}]-[{self.file}]: {msg}'

    def _color(self, logmsg:str, typename:str) -> str:
        """Color log message."""
        match typename.lower():
            case 'info': 
                return f'{colors.GREEN}{logmsg}{colors.RESET}'
            case 'debug':
                return f'{colors.BLUE}{logmsg}{colors.RESET}'
            case 'warning':
                return f'{colors.YELLOW}{logmsg}{colors.RESET}'
            case 'error':
                return f'{colors.RED_BOLD}{logmsg}{colors.RESET}'
            case 'critical': 
                return f'{colors.RED}{logmsg}{colors.RESET}'
            case _:
                raise TypeNameLogError(typename)

    def log(self, msg:str, typename:str = 'info') -> None:
        """
        Log message.
        typenames: info/debug/warning/error/critical
        """
        msg = self._build_message(msg, typename)
        msg = self._color(msg, typename)
        if typename in self.loglist:
            print(msg)
    
    # easier to use functions
    def info(self, msg:str) -> None: self.log(msg, 'info')
    def debug(self, msg:str) -> None: self.log(msg, 'debug')
    def warning(self, msg:str) -> None: self.log(msg, 'warning')
    def error(self, msg:str) -> None: self.log(msg, 'error')
    def critical(self, msg:str) -> None: self.log(msg, 'critical')
    