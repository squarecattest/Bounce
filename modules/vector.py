from collections.abc import Iterable as _Iterable, Generator as _Generator
from typing import overload as _overload, Self as _Self, Any as _Any
from math import isfinite as _isfinite

type NumberType = int | float
type LengthType = int | float
type VectorType = Vector | _Iterable[NumberType]
type SizeType = IntVector | _Iterable[int]

def _isNumber(arg) -> bool:
    '''
    Check if an argument is a real number.
    '''
    return isinstance(arg, (int, float)) and _isfinite(arg)

def _toVectorArg(arg) -> tuple[NumberType, NumberType] | None:
    '''
    To be documented
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
        if length == 2 and _isNumber(args[0]) and _isNumber(args[1]):
            self.__x, self.__y = args[0], args[1]
            return
        if length == 1 and (arg := _toVectorArg(args[0])) is not None:
            self.__x, self.__y = arg
            return
        raise TypeError("Invalid initialization argument")
    
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
    
    def __iadd__(self, __v: "Vector") -> _Self:
        if not isinstance(__v, Vector):
            return NotImplemented
        self.__x += __v.__x
        self.__y += __v.__y
        return self

    def __sub__(self, __v: "Vector") -> "Vector":
        if not issubclass(type(__v), Vector):
            return NotImplemented
        return Vector(self.__x - __v.__x, self.__y - __v.__y)
    
    def __isub__(self, __v: "Vector") -> _Self:
        if not isinstance(__v, Vector):
            return NotImplemented
        self.__x -= __v.__x
        self.__y -= __v.__y
        return self

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
            return self.__x * arg.__x + self.__y * arg.__y
        return NotImplemented
        
    def __rmul__(self, __c: NumberType) -> "Vector":
        if not _isNumber(__c):
            return NotImplemented
        return Vector(__c * self.__x, __c * self.__y)
    
    def __imul__(self, __c: NumberType) -> _Self:
        if not _isNumber(__c):
            return NotImplemented
        self.__x *= __c
        self.__y *= __c
        return self
    
    def __truediv__(self, __c: NumberType) -> "Vector":
        if not _isNumber(__c):
            return NotImplemented
        if __c == 0:
            raise ZeroDivisionError
        return Vector(self.__x / __c, self.__y / __c)
    
    def __itruediv__(self, __c: NumberType) -> _Self:
        if not _isNumber(__c):
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
        if not _isNumber(__value):
            raise TypeError("Invalid value")
        if __i == 0:
            self.__x = __value
        elif __i == 1:
            self.__y = __value
        else:
            raise IndexError("Invalid index")

    def __iter__(self) -> _Generator[NumberType, _Any, None]:
        yield self.__x
        yield self.__y

    def __len__(self) -> int:
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
        Return the projected vector from itself onto `__v`.
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
            raise TypeError("Invalid setter argument")
        self.__x = __x

    @y.setter
    def y(self, __y: NumberType) -> None:
        if not _isNumber(__y):
            raise TypeError("Invalid setter argument")
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


class IntVector(Vector):
    '''
    A two dimensional vector with integer component.
    '''
    __x: int
    __y: int
    @_overload
    def __init__(self, __x: int, __y: int, /) -> None: ...
    @_overload
    def __init__(self, __v: _Iterable[int, int]) -> None: ...

    def __init__(self, *args) -> None:
        length = len(args)
        if length == 2 and _isNumber(args[0]) and _isNumber(args[1]):
            self.__x, self.__y = int(args[0]), int(args[1])
            return
        if length == 1 and (arg := _toVectorArg(args[0])) is not None:
            self.__x, self.__y = int(arg[0]), int(arg[1])
            return
        raise TypeError("Invalid initialization argument")
        
    def __neg__(self) -> "IntVector":
        return IntVector(-self.__x, -self.__y)

    @_overload
    def __add__(self, __v: "IntVector") -> "IntVector": ...
    @_overload
    def __add__(self, __v: Vector) -> Vector: ...

    def __add__(self, __v: "IntVector | Vector") -> "IntVector | Vector":
        if isinstance(__v, IntVector):
            return IntVector(self.__x + __v.__x, self.__y + __v.__y)
        if isinstance(__v, Vector):
            return Vector(self.__x + __v.x, self.__y + __v.y)
        return NotImplemented
    
    def __iadd__(self, __v: "Vector") -> _Self:
        if not isinstance(__v, Vector):
            return NotImplemented
        self.__x += int(__v.x)
        self.__y += int(__v.y)
        return self
    
    @_overload
    def __sub__(self, __v: "IntVector") -> "IntVector": ...
    @_overload
    def __sub__(self, __v: Vector) -> Vector: ...

    def __sub__(self, __v: "IntVector | Vector") -> "IntVector | Vector":
        if isinstance(__v, IntVector):
            return IntVector(self.__x - __v.__x, self.__y - __v.__y)
        if isinstance(__v, Vector):
            return Vector(self.__x - __v.x, self.__y - __v.y)
        return NotImplemented
    
    def __isub__(self, __v: "Vector") -> _Self:
        if not isinstance(__v, Vector):
            return NotImplemented
        self.__x -= int(__v.x)
        self.__y -= int(__v.y)
        return self

    @_overload
    def __mul__(self, __c: int) -> "IntVector": ...
    @_overload
    def __mul__(self, __c: NumberType) -> Vector: ...
    @_overload
    def __mul__(self, __v: "IntVector") -> int: ...
    @_overload
    def __mul__(self, __v: Vector) -> NumberType: ...

    def __mul__(self, arg) -> "IntVector | Vector | int | NumberType":
        '''
        Operate the scalar multiplication if the argument is a `NumberType`.

        Operate the inner product if the argument is a `Vector`.
        '''
        if isinstance(arg, int):
            return IntVector(arg * self.__x, arg * self.__y)
        if _isNumber(arg):
            return Vector(arg * self.__x, arg * self.__y)
        if isinstance(arg, Vector):
            return self.__x * arg.x + self.__y * arg.y
        return NotImplemented
        
    @_overload
    def __rmul__(self, __c: int) -> "IntVector": ...
    @_overload
    def __rmul__(self, __c: NumberType) -> Vector: ...

    def __rmul__(self, __c: int | NumberType) -> "IntVector | Vector":
        if isinstance(__c, int):
            return IntVector(__c * self.__x, __c * self.__y)
        if _isNumber(__c):
            return Vector(__c * self.__x, __c * self.__y)
        return NotImplemented
    
    def __imul__(self, __c: NumberType) -> _Self:
        if not _isNumber(__c):
            return NotImplemented
        self.__x = int(self.__x * __c)
        self.__y = int(self.__y * __c)
        return self
    
    def __floordiv__(self, __c: int) -> "IntVector":
        if not isinstance(__c, int):
            return NotImplemented
        if __c == 0:
            raise ZeroDivisionError
        return IntVector(self.__x // __c, self.__y // __c)

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
        if not _isNumber(__value):
            raise TypeError("Invalid value")
        if __i == 0:
            self.__x = int(__value)
        elif __i == 1:
            self.__y = int(__value)
        else:
            raise IndexError("Invalid index")

    def __iter__(self) -> _Generator[int, _Any, None]:
        yield self.__x
        yield self.__y

    def copy(self) -> "IntVector":
        '''
        Return a copied vector.
        '''
        return IntVector(self.__x, self.__y)

    @property
    def x(self) -> int:
        return self.__x
    
    @property
    def y(self) -> int:
        return self.__y
    
    @x.setter
    def x(self, __x: NumberType) -> None:
        if not _isNumber(__x):
            raise TypeError("Invalid setter argument")
        self.__x = int(__x)

    @y.setter
    def y(self, __y: NumberType) -> None:
        if not _isNumber(__y):
            raise TypeError("Invalid setter argument")
        self.__y = int(__y)

    @property
    def squared_magnitude(self) -> int:
        '''
        The squared length / magnitude / norm of itself.
        '''
        return self.__x ** 2 + self.__y ** 2
    
    @classmethod
    @property
    def zero(cls) -> "IntVector":
        '''
        Return a zero vector.
        '''
        return cls(0, 0)
    
    @classmethod
    @property
    def unit_upward(cls) -> "IntVector":
        '''
        Return a unit vector pointing upward.
        '''
        return cls(0, -1)
    
    @classmethod
    @property
    def unit_downward(cls) -> "IntVector":
        '''
        Return a unit vector pointing upward.
        '''
        return cls(0, 1)
    
    @classmethod
    @property
    def unit_leftward(cls) -> "IntVector":
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