from time import time as _time

class Timer:
    __start_time: float
    __total_time: float
    __stop: bool
    __pause: bool
    def __init__(self, start: bool = False) -> None:
        self.stop()
        if start:
            self.start()

    def start(self) -> None:
        if self.__stop:
            self.__start_time = _time()
            self.__stop = False
        elif self.__pause:
            self.__start_time = _time() - self.__total_time
            self.__pause = False

    def pause(self) -> None:
        if self.__stop or self.__pause:
            return
        self.__total_time = _time() - self.__start_time
        self.__pause = True

    def stop(self) -> None:
        self.__total_time = 0
        self.__stop = True
        self.__pause = False

    def read(self) -> float:
        if self.__stop or self.__pause:
            return self.__total_time
        return _time() - self.__start_time
    
    def offset(self, seconds: float) -> None:
        if self.__stop:
            return
        if self.__pause:
            self.__total_time += seconds
        else:
            self.__start_time -= seconds