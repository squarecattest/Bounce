from collections import deque
from time import time

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
            self.__start_time = time()
            self.__stop = False
        elif self.__pause:
            self.__start_time = time() - self.__total_time
            self.__pause = False

    def pause(self) -> None:
        if self.__stop or self.__pause:
            return
        self.__total_time = time() - self.__start_time
        self.__pause = True

    def stop(self) -> None:
        self.__total_time = 0
        self.__stop = True
        self.__pause = False

    def restart(self) -> None:
        self.__stop = False
        self.__pause = False
        self.__start_time = time()

    def read(self, restart=False) -> float:
        if self.__stop or self.__pause:
            readout =  self.__total_time
        else:
            readout = time() - self.__start_time
        if restart:
            self.restart()
        return readout
    
    def offset(self, seconds: float) -> None:
        if self.__stop:
            return
        if self.__pause:
            self.__total_time += seconds
        else:
            self.__start_time -= seconds


class Ticker(Timer):
    __tick: float
    __ticks: int
    def __init__(self, tick: float, start: bool = False) -> None:
        self.__tick = tick
        self.__ticks = 0
        super().__init__(start)

    def tick(self) -> bool:
        if super().read() >= self.__tick:
            super().offset(-self.__tick)
            self.__ticks += 1
            return True
        return False
    
    @property
    def ticks(self) -> int:
        return self.__ticks


class FPSCounter:
    def __init__(self, counts: int, start: bool = True) -> None:
        self.__counter = deque(maxlen=counts)
        self.__timer = Timer(start=start)
        self.__counts = counts

    def tick(self) -> None:
        t = self.__timer.read(restart=True)
        if not self.__counter:
            self.__counter.extend((t, ) * self.__counts)
        else:
            self.__counter.append(t)

    def read(self) -> int:
        return int(self.__counts / sum(self.__counter))
    
def time_string(second: float) -> str:
    return f"{int(second // 60):02d}:{int(second % 60):02d}"