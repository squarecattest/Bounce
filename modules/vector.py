from collections.abc import Iterable as _Iterable, Generator as _Generator
from typing import overload, Self, Any
from math import sqrt, isfinite

type NumberType = int | float
type LengthType = int | float
type VectorType = Vector | _Iterable[NumberType, NumberType]
type SizeType = IntVector | _Iterable[int, int]

def isNumber(arg) -> bool:
    '''
    Check if an argument is a real number.
    '''
    return isinstance(arg, (int, float)) and isfinite(arg)

def isPosNumber(arg) -> bool:
    '''
    Check if an argument is a positive number.
    '''
    return isinstance(arg, (int, float)) and isfinite(arg) and arg >= 0

def isVector(arg) -> bool:
    '''
    Check if an argument is an iterable of two numbers.
    '''
    return isinstance(arg, Vector) or \
        (isinstance(arg, _Iterable) and len(arg) == 2 \
            and isNumber(arg[0]) and isNumber(arg[1]))

def isIntVector(arg) -> bool:
    '''
    Check if an argument is an iterable of two integer number.
    '''
    return isinstance(arg, IntVector) or \
        (isinstance(arg, _Iterable) and len(arg) == 2 \
        and isinstance(arg[0], int) and isinstance(arg[1], int))

def isPosIntVector(arg) -> bool:
    '''
    Check if an argument is an iterable of two positive integer number.
    '''
    return isinstance(arg, _Iterable) and len(arg) == 2 \
        and isinstance(arg[0], int) and isinstance(arg[1], int) \
        and arg[0] > 0 and arg[1] > 0


class Vector:
    '''
    A two dimensional vector.
    '''
    __x: NumberType
    __y: NumberType
    @overload
    def __init__(self, __x: NumberType, __y: NumberType, /) -> None: ...
    @overload
    def __init__(self, __v: _Iterable[NumberType, NumberType]) -> None: ...

    def __init__(self, *args) -> None:
        length = len(args)
        if length == 1 and isVector(args[0]):
            self.__x, self.__y = args[0]
        elif length == 2 and isNumber(args[0]) and isNumber(args[1]):
            self.__x, self.__y = args[0], args[1]
        else:
            raise TypeError("Invalid initialization argument")

    def __add__(self, __v: "Vector") -> "Vector":
        if not isVector(__v):
            return NotImplemented
        return Vector(self.__x + __v.__x, self.__y + __v.__y)
    
    def __iadd__(self, __v: "Vector") -> Self:
        if not isVector(__v):
            return NotImplemented
        self.__x += __v.__x
        self.__y += __v.__y
        return self

    def __sub__(self, __v: "Vector") -> "Vector":
        if not isVector(__v):
            return NotImplemented
        return Vector(self.__x - __v.__x, self.__y - __v.__y)
    
    def __isub__(self, __v: "Vector") -> Self:
        if not isVector(__v):
            return NotImplemented
        self.__x -= __v.__x
        self.__y -= __v.__y
        return self

    @overload
    def __mul__(self, __c: NumberType) -> "Vector": ...
    @overload
    def __mul__(self, __v: "Vector") -> NumberType: ...

    def __mul__(self, arg) -> "Vector | NumberType":
        '''
        Operate scalar multiplication if the argument is a `NumberType`.

        Operate inner product if the argument is a `Vector`.
        '''
        if isNumber(arg):
            return Vector(arg * self.__x, arg * self.__y)
        if isVector(arg):
            return self.__x * arg[0] + self.__y * arg[1]
        return NotImplemented
        
    def __rmul__(self, __c: NumberType) -> "Vector":
        if not isNumber(__c):
            return NotImplemented
        return Vector(__c * self.__x, __c * self.__y)
    
    def __imul__(self, __c: NumberType) -> Self:
        if not isNumber(__c):
            return NotImplemented
        self.__x *= __c
        self.__y *= __c
        return self
    
    def __truediv__(self, __c: NumberType) -> "Vector":
        if not isNumber(__c):
            return NotImplemented
        if __c == 0:
            raise ZeroDivisionError
        return Vector(self.__x / __c, self.__y / __c)
    
    def __itruediv__(self, __c: NumberType) -> Self:
        if not isNumber(__c):
            return NotImplemented
        if __c == 0:
            raise ZeroDivisionError
        self.__x /= __c
        self.__y /= __c
        return self

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
        if not isNumber(__value):
            raise TypeError("Invalid value")
        if __i == 0:
            self.__x = __value
        elif __i == 1:
            self.__y = __value
        else:
            raise IndexError("Invalid index")

    def __iter__(self) -> _Generator[NumberType, Any, None]:
        yield self.__x
        yield self.__y

    def copy(self) -> "Vector":
        '''
        Return a copied vector.
        '''
        return Vector(self)

    def project_on(self, __v: "Vector") -> "Vector":
        if __v.is_zerovec:
            raise ValueError("Cannot project a vector onto a zero vector")
        return __v * ((self * __v) / __v.squared_magnitude)

    @property
    def x(self) -> NumberType:
        return self.__x
    
    @property
    def y(self) -> NumberType:
        return self.__y
    
    @x.setter
    def x(self, __x: NumberType) -> None:
        if not isNumber(__x):
            raise TypeError("Invalid setter argument")
        self.__x = __x

    @y.setter
    def y(self, __y: NumberType) -> None:
        if not isNumber(__y):
            raise TypeError("Invalid setter argument")
        self.__y = __y

    @property
    def is_zerovec(self) -> bool:
        '''
        Return if self is a zero vector.
        '''
        return self.__x == 0 and self.__y == 0

    @property
    def magnitude(self) -> NumberType:
        '''
        The length / magnitude / norm of itself.
        '''
        return sqrt(self.__x ** 2 + self.__y ** 2)
    
    @property
    def squared_magnitude(self) -> NumberType:
        '''
        The squared length / magnitude / norm of itself.
        '''
        return self.__x ** 2 + self.__y ** 2
    
    @property
    def unit(self) -> "Vector":
        '''
        The unit vector of itself.
        '''
        if (magnitude := self.magnitude) == 0:
            raise ZeroDivisionError("Null vector has no unit vector")
        return self / magnitude
    
    @property
    def IntTuple(self) -> tuple[int, int]:
        '''
        The integer tuple representation of itself.
        '''
        return int(self.__x), int(self.__y)


class IntVector(Vector):
    '''
    A two dimensional vector with integer component.
    '''
    __x: int
    __y: int
    @overload
    def __init__(self, __x: int, __y: int, /) -> None: ...
    @overload
    def __init__(self, __v: _Iterable[int, int]) -> None: ...

    def __init__(self, *args) -> None:
        length = len(args)
        if length == 1 and isVector(args[0]):
            self.__x, self.__y = map(int, args[0])
        elif length == 2 and isNumber(args[0]) and isNumber(args[1]):
            self.__x, self.__y = int(args[0]), int(args[1])
        else:
            raise TypeError("Invalid initialization argument")

    @overload
    def __add__(self, __v: "IntVector") -> "IntVector": ...
    @overload
    def __add__(self, __v: Vector) -> Vector: ...

    def __add__(self, __v: "IntVector | Vector") -> "IntVector | Vector":
        if isIntVector(__v):
            return IntVector(self.__x + __v.__x, self.__y + __v.__y)
        if isVector(__v):
            return Vector(self.__x + __v.__x, self.__y + __v.__y)
        return NotImplemented
    
    def __iadd__(self, __v: "Vector") -> Self:
        if not isVector(__v):
            return NotImplemented
        self.__x += int(__v.__x)
        self.__y += int(__v.__y)
        return self
    
    @overload
    def __sub__(self, __v: "IntVector") -> "IntVector": ...
    @overload
    def __sub__(self, __v: Vector) -> Vector: ...

    def __sub__(self, __v: "IntVector | Vector") -> "IntVector | Vector":
        if isIntVector(__v):
            return IntVector(self.__x - __v.__x, self.__y - __v.__y)
        if isVector(__v):
            return Vector(self.__x - __v.__x, self.__y - __v.__y)
        return NotImplemented
    
    def __isub__(self, __v: "Vector") -> Self:
        if not isVector(__v):
            return NotImplemented
        self.__x += int(-__v.__x)
        self.__y += int(-__v.__y)
        return self

    @overload
    def __mul__(self, __c: int) -> "IntVector": ...
    @overload
    def __mul__(self, __c: NumberType) -> Vector: ...
    @overload
    def __mul__(self, __v: "IntVector") -> int: ...
    @overload
    def __mul__(self, __v: Vector) -> NumberType: ...

    def __mul__(self, arg) -> "IntVector | Vector | int | NumberType":
        '''
        Operate scalar multiplication if the argument is a `NumberType`.

        Operate inner product if the argument is a `Vector`.
        '''
        if isinstance(arg, int):
            return IntVector(arg * self.__x, arg * self.__y)
        if isNumber(arg):
            return Vector(arg * self.__x, arg * self.__y)
        if isVector(arg):
            return self.__x * arg[0] + self.__y * arg[1]
        return NotImplemented
        
    @overload
    def __rmul__(self, __c: int) -> "IntVector": ...
    @overload
    def __rmul__(self, __c: NumberType) -> Vector: ...

    def __rmul__(self, __c: int | NumberType) -> "IntVector | Vector":
        if isinstance(__c, int):
            return IntVector(__c * self.__x, __c * self.__y)
        if isNumber(__c):
            return Vector(__c * self.__x, __c * self.__y)
        return NotImplemented
    
    def __imul__(self, __c: NumberType) -> Self:
        if not isNumber(__c):
            return NotImplemented
        self.__x = int(self.__x * __c)
        self.__y = int(self.__y * __c)
        return self

    def __getitem__(self, __i: int) -> int:
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
        if not isNumber(__value):
            raise TypeError("Invalid value")
        if __i == 0:
            self.__x = int(__value)
        elif __i == 1:
            self.__y = int(__value)
        else:
            raise IndexError("Invalid index")

    def __iter__(self) -> _Generator[int, Any, None]:
        yield self.__x
        yield self.__y

    def copy(self) -> "IntVector":
        '''
        Return a copied vector.
        '''
        return IntVector(self)

    @property
    def x(self) -> int:
        return self.__x
    
    @property
    def y(self) -> int:
        return self.__y
    
    @x.setter
    def x(self, __x: NumberType) -> None:
        if not isNumber(__x):
            raise TypeError("Invalid setter argument")
        self.__x = int(__x)

    @y.setter
    def y(self, __y: NumberType) -> None:
        if not isNumber(__y):
            raise TypeError("Invalid setter argument")
        self.__y = int(__y)

    @property
    def squared_magnitude(self) -> int:
        '''
        The squared length / magnitude / norm of itself.
        '''
        return self.__x ** 2 + self.__y ** 2