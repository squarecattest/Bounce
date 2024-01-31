from collections import deque
from time import time
from random import random
from enum import Enum, auto
from typing import Iterable, Generator

class Direction(Enum):
    NONE = auto()
    LEFT = auto()
    RIGHT = auto()


class LinkedList[T]:
    class Node[S]:
        __prev: "LinkedList.Node[S] | None"
        __next: "LinkedList.Node[S] | None"
        def __init__(self, data: S, prev: "LinkedList.Node[S] | None") -> None:
            self.__data = data
            self.__prev = prev
            self.__next = None
            if prev is not None:
                prev.__next = self

        def delete(self) -> None:
            if self.__prev is not None:
                self.__prev.__next = self.__next
            if self.__next is not None:
                self.__next.__prev = self.__prev

        @property
        def data(self) -> S:
            return self.__data
        
        @property
        def prev(self) -> "LinkedList.Node[S] | None":
            return self.__prev
        
        @property
        def next(self) -> "LinkedList.Node[S] | None":
            return self.__next

    __head: Node[T] | None
    __tail: Node[T] | None

    def __init__(self) -> None:
        self.__head = self.__tail = None

    def append(self, data: T) -> None:
        self.__tail = LinkedList.Node(data, self.__tail)
        if self.__head is None:
            self.__head = self.__tail

    def extend(self, iterable: Iterable[T]) -> None:
        for element in iterable:
            self.append(element)
    
    def pop(self, node: Node[T]) -> None:
        node.delete()
        if self.__head is node:
            self.__head = node.next
        if self.__tail is node:
            self.__tail = node.prev

    @property
    def data_iter(self) -> Generator[T, None, None]:
        node = self.__head
        while node is not None:
            yield node.data
            node = node.next

    @property
    def node_iter(self) -> Generator[Node[T], None, None]:
        node = self.__head
        while node is not None:
            yield node
            node = node.next


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

    @property
    def running(self) -> bool:
        return not self.__stop and not self.__pause


class Ticker(Timer):
    __tick: float
    __ticks: int
    def __init__(self, tick: float, start: bool = False, starting_cooldown: float = 0) -> None:
        self.__tick = tick
        self.__ticks = 0
        self.__started = False
        self.__starting_cooldown = starting_cooldown
        super().__init__(start)

    def tick(self) -> bool:
        if not self.__started:
            if super().read() >= self.__starting_cooldown:
                super().offset(-self.__starting_cooldown)
                self.__started = True
                return self.tick()
            return False
        if super().read() >= self.__tick:
            super().offset(-self.__tick)
            self.__ticks += 1
            return True
        return False
    
    def stop(self) -> None:
        self.__ticks = 0
        self.__started = False
        super().stop()

    def restart(self) -> None:
        self.__ticks = 0
        self.__started = False
        super().restart()

    def skip_cooldown(self) -> None:
        self.__ticks = 0
        self.__started = True
        super().restart()
    
    @property
    def ticks(self) -> int:
        return self.__ticks
    
    @property
    def in_cooldown(self) -> bool:
        return not self.__started
    

class Chance:
    def __init__(self, chance: float) -> None:
        self.chance = chance

    def __bool__(self) -> bool:
        return random() < self.chance


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