from constants import ErrorlogConstant as Constant
from resources import Path
from threading import Thread
from traceback import print_exception
from datetime import datetime

class OutOfLogs(Exception):
    pass

_LOGS_LEFT = Constant.MAX_LOGS

def _write(error: BaseException):
    with open(Path.ERRORLOG, "a") as file:
        print(f"[{datetime.now()}]", file=file)
        print_exception(error, file=file)
        print(file=file)

def log(error: BaseException) -> None:
    global _LOGS_LEFT
    if _LOGS_LEFT == 0:
        raise OutOfLogs
    _LOGS_LEFT -= 1
    Thread(target=_write, args=(error, )).start()