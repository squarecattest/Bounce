from collections.abc import Iterable as _Iterable, Generator as _Generator
from typing import overload as _overload, Self as _Self, Literal as _Literal, Any as _Any
from math import isfinite as _isfinite

type NumberType = int | float
type LengthType = int | float
type VectorType = Vector | _Iterable[NumberType]
type SizeType = Vector | _Iterable[int]

def _isNumber(arg, /) -> bool:
    '''
    Check if an argument is a real number.
    '''
    return isinstance(arg, int) or isinstance(arg, float) and _isfinite(arg)

def _toVectorArg(arg, /) -> tuple[NumberType, NumberType] | None:
    '''
    Convert a vector-like argument to a tuple form. The argument must be an iterable and 
    contain two :class:`NumberType` elements. If the argument is of inappropriate type, 
    ``None`` will be returned.
    '''
    try:
        it = iter(arg)
        x = next(it)
        y = next(it)
    except:
        return None
    if not _isNumber(x) or not _isNumber(y):
        return None
    try:
        next(it)
    except StopIteration:
        return x, y
    except:
        pass
    return None

def _getTypeName(arg, /) -> str:
    '''
    Get the error type name of a value. Used for exception raising.
    '''
    if isinstance(arg, float) and not _isfinite(arg):
        return str(arg)
    return type(arg).__name__
    

class Vector:
    '''
    A two dimensional vector.
    '''
    __x: NumberType
    __y: NumberType
    @_overload
    def __init__(self, __x: NumberType, __y: NumberType, /) -> None: ...
    @_overload
    def __init__(self, __v: _Iterable[NumberType]) -> None: ...

    def __init__(self, *args) -> None:
        length = len(args)
        if length == 2:
            if not _isNumber(args[0]):
                raise TypeError(
                    f"Expected real number for the first argument, got {_getTypeName(args[0])}"
                )
            if not _isNumber(args[1]):
                raise TypeError(
                    f"Expected real number for the second argument, got {_getTypeName(args[1])}"
                )
            self.__x, self.__y = args[0], args[1]
            return
        if length == 1:
            if (arg := _toVectorArg(args[0])) is None:
                raise TypeError("Expected 2d-vector-like argument")
            self.__x, self.__y = arg
            return
        raise TypeError(f"Expected 1 or 2 arguments, got {length}")
    
    def __eq__(self, __v: VectorType) -> bool:
        if isinstance(__v, Vector):
            return self.__x == __v.__x and self.__y == __v.__y
        __v = _toVectorArg(__v)
        if __v is None:
            return NotImplemented
        return self.__x == __v[0] and self.__y == __v[1]
        
    def __neg__(self) -> "Vector":
        return Vector(-self.__x, -self.__y)

    def __add__(self, __v: "Vector") -> "Vector":
        if not isinstance(__v, Vector):
            return NotImplemented
        return Vector(self.__x + __v.__x, self.__y + __v.__y)

    def __sub__(self, __v: "Vector") -> "Vector":
        if not isinstance(__v, Vector):
            return NotImplemented
        return Vector(self.__x - __v.__x, self.__y - __v.__y)

    @_overload
    def __mul__(self, __c: NumberType) -> "Vector": ...
    @_overload
    def __mul__(self, __v: "Vector") -> NumberType: ...

    def __mul__(self, arg: "NumberType | Vector") -> "Vector | NumberType":
        '''
        Operate the scalar multiplication if the argument is a `NumberType`.

        Operate the inner product if the argument is a `Vector`.
        '''
        if _isNumber(arg):
            return Vector(arg * self.__x, arg * self.__y)
        if isinstance(arg, Vector):
            return self.__x * arg.x + self.__y * arg.y
        return NotImplemented

    def __rmul__(self, __c: NumberType) -> "Vector":
        if not _isNumber(__c):
            return NotImplemented
        return Vector(__c * self.__x, __c * self.__y)
    
    def __imul__(self, __c: NumberType) -> _Self:
        if not _isNumber(__c):
            return NotImplemented
        return Vector(__c * self.__x, __c * self.__y)
    
    def __truediv__(self, __c: NumberType) -> "Vector":
        if not _isNumber(__c):
            return NotImplemented
        if __c == 0:
            raise ZeroDivisionError
        return Vector(self.__x / __c, self.__y / __c)
    
    def __floordiv__(self, __c: NumberType) -> "Vector":
        if not _isNumber(__c):
            return NotImplemented
        if __c == 0:
            raise ZeroDivisionError
        return Vector(self.__x // __c, self.__y // __c)

    def __getitem__(self, __i: int) -> NumberType:
        if not isinstance(__i, int):
            raise TypeError(f"Expected integer index 0 or 1, got {type(__i).__name__}")
        if __i == 0:
            return self.__x
        if __i == 1:
            return self.__y
        raise IndexError(f"Expected integer index 0 or 1, got {__i}")
    
    def __setitem__(self, __i: int, __value: NumberType) -> None:
        if not isinstance(__i, int):
            raise TypeError(f"Expected integer index 0 or 1, got {type(__i).__name__}")
        if not __i in (0, 1):
            raise IndexError(f"Expected integer index 0 or 1, got {__i}")
        if not _isNumber(__value):
            raise TypeError(f"Expected real number value, got {_getTypeName(__value)}")
        if __i == 0:
            self.__x = __value
        else:
            self.__y = __value

    def __iter__(self) -> _Generator[NumberType, _Any, None]:
        yield self.__x
        yield self.__y

    def __len__(self) -> _Literal[2]:
        return 2
    
    def __str__(self) -> str:
        return f"({self.__x}, {self.__y})"
    
    def __repr__(self) -> str:
        return f"Vector({self.__x}, {self.__y})"
    
    def __format__(self, __format_spec: str) -> str:
        return f"({format(self.__x, __format_spec)}, {format(self.__y, __format_spec)})"

    def copy(self) -> "Vector":
        '''
        Return a copied vector.
        '''
        return Vector(self.__x, self.__y)

    def project_on(self, __v: "Vector") -> "Vector":
        '''
        Return the projected vector onto `__v`.
        '''
        if __v.is_zerovec:
            raise ValueError("Cannot project a vector onto a zero vector")
        return __v * ((self * __v) / __v.squared_magnitude)
    
    def dot(self, __v: "Vector") -> NumberType:
        '''
        Return the inner product of itself and the vector.
        '''
        if not isinstance(__v, Vector):
            raise TypeError("Invalid argument")
        return self.__x * __v.__x + self.__y * __v.__y

    @property
    def x(self) -> NumberType:
        return self.__x
    
    @property
    def y(self) -> NumberType:
        return self.__y
    
    @x.setter
    def x(self, __x: NumberType) -> None:
        if not _isNumber(__x):
            raise TypeError(f"Expected real number value, got {_getTypeName(__x)}")
        self.__x = __x

    @y.setter
    def y(self, __y: NumberType) -> None:
        if not _isNumber(__y):
            raise TypeError(f"Expected real number value, got {_getTypeName(__y)}")
        self.__y = __y

    @property
    def is_zerovec(self) -> bool:
        '''
        Whether itself is a zero vector.
        '''
        return self.__x == 0 and self.__y == 0

    @property
    def magnitude(self) -> NumberType:
        '''
        The length / magnitude / norm of itself.
        '''
        return (self.__x ** 2 + self.__y ** 2) ** (1/2)
    
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
            raise ZeroDivisionError("Zero vector has no unit vector")
        return self / magnitude
    
    @property
    def inttuple(self) -> tuple[int, int]:
        '''
        The integer tuple representation of itself.
        '''
        return int(self.__x), int(self.__y)
    
    @classmethod
    @property
    def zero(cls) -> "Vector":
        '''
        Return a zero vector.
        '''
        return cls(0, 0)
    
    @classmethod
    @property
    def unit_upward(cls) -> "Vector":
        '''
        Return a unit vector pointing upward.
        '''
        return cls(0, -1)
    
    @classmethod
    @property
    def unit_downward(cls) -> "Vector":
        '''
        Return a unit vector pointing upward.
        '''
        return cls(0, 1)
    
    @classmethod
    @property
    def unit_leftward(cls) -> "Vector":
        '''
        Return a unit vector pointing rightward.
        '''
        return cls(-1, 0)
    
    @classmethod
    @property
    def unit_rightward(cls) -> "Vector":
        '''
        Return a unit vector pointing rightward.
        '''
        return cls(1, 0)