from resources import Path
from threading import Thread
from traceback import print_exception
from datetime import datetime

def log(error: BaseException) -> None:
    def write():
        with open(Path.ERRORLOG, "a") as file:
            print(f"[{datetime.now()}]", file=file)
            print_exception(error, file=file)
            print(file=file)
    Thread(target=write).start()
        