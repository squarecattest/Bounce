from constants import ErrorlogConstant as Constant
from resources import Path
from threading import Thread
from sys import exit
from traceback import print_exception
from datetime import datetime

class Log:
    class OutOfLimit(Exception):
        pass
    __LOGS_LEFT = Constant.MAX_LOGS

    @classmethod
    def log(cls, error: BaseException) -> None:
        def write():
            with open(Path.ERRORLOG, "a") as file:
                print(f"[{datetime.now()}]", file=file)
                print_exception(error, file=file)
                print(file=file)
        if cls.__LOGS_LEFT == 0:
            raise Log.OutOfLimit
        cls.__LOGS_LEFT -= 1
        Thread(target=write).start()