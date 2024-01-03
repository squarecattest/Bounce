from collections import deque as _deque
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

    def restart(self) -> None:
        self.__stop = False
        self.__pause = False
        self.__start_time = _time()

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

class FPSCounter:
    def __init__(self, counts: int, start: bool = True) -> None:
        self.__counter = _deque(maxlen=counts)
        self.__timer = Timer(start=start)
        self.__counts = counts

    def tick(self) -> None:
        t = self.__timer.read()
        if not self.__counter:
            self.__counter.extend((t, ) * self.__counts)
        else:
            self.__counter.append(t)
        self.__timer.restart()

    def read(self) -> int:
        return int(self.__counts / sum(self.__counter))
    
def time_string(second: float) -> str:
    return f"{int(second // 60):02d}:{int(second % 60):02d}"