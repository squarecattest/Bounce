from typing import Iterable
from math import isfinite

_GRAVITY = -60
_COEFFICIENT_OF_FRICTION = _COF = 0
type NumberType = int | float
type LengthType = int | float
type PosType = tuple[NumberType, NumberType]
type SizeType = tuple[int, int]

def isNumberType(arg) -> bool:
    '''
    Check if an argument is of `NumberType`.
    '''
    return isinstance(arg, (int, float)) and isfinite(arg)

def isLengthType(arg) -> bool:
    '''
    Check if an argument is of `LengthType`.
    '''
    return isinstance(arg, (int, float)) and isfinite(arg) and arg >= 0

def isPosType(arg) -> bool:
    '''
    Check if an argument is an iterable of two `NumberType` element.
    '''
    return isinstance(arg, Iterable) and len(arg) == 2 \
        and isNumberType(arg[0]) and isNumberType(arg[1])

def isSizeType(arg) -> bool:
    '''
    Check if an argument is of `SizeType`.
    '''
    return isinstance(arg, Iterable) and len(arg) == 2 \
        and isinstance(arg[0], int) and isinstance(arg[1], int)


class PhysicsGround:
    '''
    The class represents physical interaction of the ground.
    '''
    __y_top: NumberType

    def __init__(self, y_top: NumberType):
        assert isNumberType(y_top)
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
    __x: NumberType
    __y: NumberType
    __size: SizeType
    __vx: NumberType

    def __init__(self, position: PosType, size: SizeType, velocity_x: NumberType) -> None:
        assert isPosType(position)
        assert isSizeType(size)
        assert isNumberType(velocity_x)
        self.__x, self.__y = position
        self.__size = tuple(size)
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
    def size(self): return self.size
    @property
    def velocity_x(self): return self.__vx


class PhysicsBall:
    '''
    The class represents physical interaction of a ball.
    '''
    __x: NumberType
    __y: NumberType
    __vx: NumberType
    __vy: NumberType
    __radius: LengthType
    __onground: bool
    __ground: PhysicsGround | PhysicsSlab | None

    def __init__(self, position: tuple[NumberType, NumberType], radius: LengthType) -> None:
        assert isPosType(position)
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
        pass #############

    def detect_collision(self, *args: PhysicsGround | PhysicsSlab):
        for arg in args:
            pass

    @property
    def position(self): return self.__x, self.__y
    @property
    def position_int(self): return int(self.__x), int(self.__y)
    @property
    def position_x(self): return self.__x
    @property
    def position_y(self): return self.__y