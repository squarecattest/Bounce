from .constants import ErrorlogConstant as Constant
from .resources import Path
import logging

_LOGS_LEFT = Constant.MAX_LOGS
logging.basicConfig(
    filename=Path.ERRORLOG, 
    filemode="a", 
    format="\n[%(asctime)s]\n[%(levelname)s]\n", 
    encoding="UTF-8"
)

class OutOfLogs(Exception):
    pass

def log(e: BaseException) -> None:
    global _LOGS_LEFT
    if _LOGS_LEFT == 0:
        raise OutOfLogs
    _LOGS_LEFT -= 1
    logging.exception(e)