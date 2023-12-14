from typing import Iterable
from math import isfinite

_GRAVITY = -60
type PosType = int | float
type LengthType = int | float

def isPosType(arg) -> bool:
    '''
    Check if an argument is of `PosType`.
    '''
    return isinstance(arg, (int, float)) and isfinite(arg)

def isPosTuple(arg) -> bool:
    '''
    Check if an argument is an iterable of two `PosType` element.
    '''
    return isinstance(arg, Iterable) and len(arg) == 2 and isPosType(arg[0]) and isPosType(arg[1])

def isLengthType(arg) -> bool:
    '''
    Check if an argument is of `LengthType`.
    '''
    return isinstance(arg, (int, float)) and isfinite(arg) and arg >= 0


class PhysicsGround:
    '''
    The class represents physical interaction of the ground.
    '''
    __y_top: PosType

    def __init__(self, y_top: PosType):
        assert isPosType(y_top)
        self.__y_top = y_top
    
    @property
    def position_y_top(self): return self.__y_top
    @property
    def position_y_top_int(self): return int(self.__y_top)
    @property
    def velocity_x(self): return 0
    

class PhysicsSlab:
    '''
    The class represents physical interaction of a floating slab.
    '''
    __x: PosType
    __y: PosType
    __vx: PosType

    def __init__(
        self,
        position: tuple[PosType, PosType],
        size: tuple[int, int],
        velocity_x: PosType
    ) -> None:
        assert isPosTuple(position)
        assert isinstance(size, Iterable) and len(size) == 2
        assert isinstance(size[0], int) and isinstance(size[1], int)
        assert isPosType(velocity_x)
        self.__x, self.__y = position
        self.__vx = velocity_x

    def accelerate(self, dt: float) -> None:
        '''
        Change the position of the slab with respect to time interval `dt`.
        '''
        assert isinstance(dt, float)
        self.__x += self.__vx * dt

    @property
    def position(self): return self.__x, self.__y
    @property
    def position_int(self): return int(self.__x), int(self.__y)
    @property
    def position_x(self): return self.__x
    @property
    def position_y(self): return self.__y
    @property
    def velocity_x(self): return self.__vx


class PhysicsBall:
    '''
    The class represents physical interaction of a ball.
    '''
    __x: PosType
    __y: PosType
    __vx: PosType
    __vy: PosType
    __radius: LengthType
    __onground: bool
    __ground: PhysicsGround | PhysicsSlab | None

    def __init__(self, position: tuple[PosType, PosType], radius: LengthType) -> None:
        assert isPosTuple(position)
        assert isLengthType(radius)
        self.__x, self.__y = position
        self.__vx = self.__vy = 0
        self.__radius = radius
        self.__onground = False
        self.__ground = None

    def accelerate(self, dt: float) -> None:
        '''
        Change the position and velocity of the ball with respect to time interval `dt`.
        '''
        assert isinstance(dt, float)
        self.__x += self.__vx * dt
        self.__y -= self.__vy * dt # since y=0 is the top side of the window
        self.__vy += _GRAVITY * dt

    @property
    def position(self): return self.__x, self.__y
    @property
    def position_int(self): return int(self.__x), int(self.__y)
    @property
    def position_x(self): return self.__x
    @property
    def position_y(self): return self.__y