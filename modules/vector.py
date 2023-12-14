from collections.abc import Iterable, Generator
from typing import overload, Any
from math import sqrt, isfinite

type NumberType = int | float
type LengthType = int | float
type VecType = tuple[NumberType, NumberType]
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

def isVecType(arg) -> bool:
    '''
    Check if an argument is an iterable of two `NumberType` element.
    '''
    return isinstance(arg, Vector) or \
        (isinstance(arg, Iterable) and len(arg) == 2 \
            and isNumberType(arg[0]) and isNumberType(arg[1]))

def isSizeType(arg) -> bool:
    '''
    Check if an argument is of `SizeType`.
    '''
    return isinstance(arg, Iterable) and len(arg) == 2 \
        and isinstance(arg[0], int) and isinstance(arg[1], int)

def VectorDot(v1: VecType, v2: VecType, /) -> NumberType:
    assert isVecType(v1) and isVecType(v2)
    return v1[0] * v2[0] + v1[1] * v2[1]

def PointDistance(p1: VecType, p2: VecType, /) -> NumberType:
    assert isVecType(p1) and isVecType(p2)
    return ((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2) ** (1/2)

def VectorMagnitude(v: VecType, /) -> NumberType:
    assert isVecType(v)
    return (v[0]**2 + v[1]**2) ** (1/2)

def UnitVector(v: VecType, /) -> VecType:
    assert (magnitude := VectorMagnitude(v)) != 0
    return v[0] / magnitude, v[1] / magnitude


class Vector:
    __x: NumberType
    __y: NumberType
    @overload
    def __init__(self, __x: NumberType, __y: NumberType, /) -> None: ...
    @overload
    def __init__(self, __v: Iterable[NumberType, NumberType]) -> None: ...

    def __init__(self, *args) -> None:
        length = len(args)
        if length == 1 and isVecType(args[0]):
            self.__x, self.__y = args[0]
        elif length == 2 and isNumberType(args[0]) and isNumberType(args[1]):
            self.__x, self.__y = args[0], args[1]
        else:
            raise TypeError("Invalid initialization argument")

    def __add__(self, __v: "Vector") -> "Vector":
        if not isVecType(__v):
            return NotImplemented
        return Vector(self.__x + __v.__x, self.__y + __v.__y)
    
    def __iadd__(self, __v: "Vector") -> None:
        if not isVecType(__v):
            return NotImplemented
        self.__x += __v.__x
        self.__y += __v.__y

    def __sub__(self, __v: "Vector") -> "Vector":
        if not isVecType(__v):
            return NotImplemented
        return Vector(self.__x - __v.__x, self.__y - __v.__y)
    
    def __isub__(self, __v: "Vector") -> None:
        if not isVecType(__v):
            return NotImplemented
        self.__x -= __v.__x
        self.__y -= __v.__y

    @overload
    def __mul__(self, __c: NumberType) -> "Vector": ...
    @overload
    def __mul__(self, __v: "Vector") -> NumberType: ...

    def __mul__(self, arg) -> "Vector | NumberType":
        '''
        Operate scalar multiplication if the argument is a `NumberType`.

        Operate inner product if the argument is a `Vector`.
        '''
        if isNumberType(arg):
            return Vector(arg * self.__x, arg * self.__y)
        if isVecType(arg):
            return self.__x * arg[0] + self.__y * arg[1]
        return NotImplemented
        
    def __rmul__(self, __c: NumberType) -> "Vector":
        if not isNumberType(__c):
            return NotImplemented
        return Vector(__c * self.__x, __c * self.__y)
    
    def __imul__(self, __c: NumberType) -> None:
        if not isNumberType(__c):
            return NotImplemented
        self.__x *= __c
        self.__y *= __c
    
    def __truediv__(self, __c: NumberType) -> "Vector":
        if not isNumberType(__c):
            return NotImplemented
        if __c == 0:
            raise ZeroDivisionError
        return Vector(self.__x / __c, self.__y / __c)
    
    def __itruediv__(self, __c: NumberType) -> None:
        if not isNumberType(__c):
            return NotImplemented
        if __c == 0:
            raise ZeroDivisionError
        self.__x /= __c
        self.__y /= __c

    def __getitem__(self, __i: int) -> NumberType:
        if not isinstance(__i, int):
            raise TypeError("Invalid index")
        if __i == 0:
            return self.__x
        if __i == 1:
            return self.__y
        raise IndexError("Invalid index")
    
    def __setitem__(self, __i: int, __value: NumberType) -> None:
        if not isinstance(__i, int):
            raise TypeError("Invalid index")
        if not isNumberType(__value):
            raise TypeError("Invalid value")
        if __i == 0:
            self.__x = __value
        elif __i == 1:
            self.__y = __value
        else:
            raise IndexError("Invalid index")

    def __iter__(self) -> Generator[NumberType, Any, None]:
        yield self.__x
        yield self.__y

    @property
    def x(self) -> NumberType:
        return self.__x
    
    @property
    def y(self) -> NumberType:
        return self.__y
    
    @x.setter
    def x(self, __x: NumberType) -> None:
        if not isNumberType(__x):
            raise TypeError("Invalid setter argument")
        self.__x = __x

    @y.setter
    def y(self, __y: NumberType) -> None:
        if not isNumberType(__y):
            raise TypeError("Invalid setter argument")
        self.__y = __y

    @property
    def magnitude(self) -> NumberType:
        return sqrt(self.__x ** 2 + self.__y ** 2)
    
    @property
    def unit(self) -> "Vector":
        if (magnitude := self.magnitude) == 0:
            raise ZeroDivisionError("Null vector has no unit vector")
        return self / magnitude