from pygame import Surface as _Surface, Color as _Color
from pygame.font import Font as _Font
from pygame.transform import rotate
from vector import Vector, NumberType
from enum import Enum as _Enum, Flag as _Flag, auto as _auto
from itertools import product as _product
from functools import reduce as _reduce
from typing import Union as _Union, Callable as _Callable, Generator as _Generator

type ColorType = _Union[_Color, int, str, tuple[int, int, int], tuple[int, int, int, int]]
_COLOR_BLACK = (0, 0, 0)

def _typename(arg) -> str:
    return type(arg).__name__

class Alignment:
    '''
    The class representing an alignment mode for a displayable object. Two modes will be 
    specified in this class, one for the screen and one for the surface. The two points of 
    the screen and the surface given by the alignment modes will be aligned, which gives the 
    unique reference point of a displayable object.
    '''
    class Flag(_Flag):
        NONE = 0
        FILL = _auto()
        '''
        Repeat the surface to fill the specified region. If the alignment mode is a side, the 
        facing direction will be filled. (For example, if the mode is ``LEFT``, the right part 
        of the screen will be filled.) Otherwise, the whole screen will be filled.
        '''
        REFERENCED = _auto()
        '''
        Place the surface with an offset.
        '''

    class Mode(_Enum):
        DEFAULT = _auto()
        '''
        The surface will be aligned at the top-left corner.
        '''
        CENTERED = _auto()
        '''
        The surface will be aligned at the center of the surface.
        '''
        LEFT = _auto()
        '''
        The surface will be aligned at the center of the left side.
        '''
        RIGHT = _auto()
        '''
        The surface will be aligned at the center of the right side.
        '''
        TOP = _auto()
        '''
        The surface will be aligned at the center of the top side.
        '''
        BOTTOM = _auto()
        '''
        The surface will be aligned at the center of the bottom side.
        '''

    class Facing(_Enum):
        LEFT = _auto()
        RIGHT = _auto()
        UP = _auto()
        DOWN = _auto()
        ALL = _auto()

    @staticmethod
    def __mode(align: Mode) -> _Callable[[_Surface], Vector]:
        match align:
            case Alignment.Mode.DEFAULT:
                return lambda surface: Vector.zero
            case Alignment.Mode.CENTERED:
                return lambda surface: Vector(surface.get_size()) // 2
            case Alignment.Mode.LEFT:
                return lambda surface: Vector(0, surface.get_size()[1] // 2)
            case Alignment.Mode.RIGHT:
                return lambda surface: Vector(surface.get_size()[0], surface.get_size()[1] // 2)
            case Alignment.Mode.TOP:
                return lambda surface: Vector(surface.get_size()[0] // 2, 0)
            case Alignment.Mode.BOTTOM:
                return lambda surface: Vector(surface.get_size()[0] // 2, surface.get_size()[1])
            case _:
                raise ValueError(f"Unknown alignment mode")
    
    __screen_meth: _Callable[[_Surface], Vector]
    __surface_meth: _Callable[[_Surface], Vector]
    flags: Flag
    __facing: Facing
    __offset: Vector
    def __init__(
            self, screen_mode: Mode, surface_mode: Mode, *flags: Flag, **kwargs
        ) -> None:
        '''
        Parameters
        ----------
        screen_mode: :class:`Alignment.Mode`
            The alignment mode of the screen.
        surface_mode: :class:`Alignment.Mode`
            The alignment mode of the surface.
        *flags: :class:`Alignment.Flag`
            The flags for the alignment.
        **kwargs:
            facing: Union[:class:`Alignment.Facing`, 'LEFT', 'RIGHT', 'UP', 'DOWN']
                The direction facing towards the filled region. Required and only used when 
                ``Alignment.Flag.FILL` is specified.
            offset: :class:`Vector`
                The offset of the alignment. Required and only used when 
                ``Alignment.Flag.REFERENCED`` is specified.

        '''
        if not screen_mode in Alignment.Mode:
            raise TypeError(
                f"Excepted Alignment.Mode for the first argument, got {_typename(screen_mode)}"
            )
        if not surface_mode in Alignment.Mode:
            raise TypeError(
                f"Excepted Alignment.Mode for the second argument, got {_typename(surface_mode)}"
            )
        for flag in flags:
            if not flag in Alignment.Flag:
                raise TypeError(
                    f"Expected Alignment.Flag for flags argument, got {_typename(flag)}"
                )
        
        self.__screen_meth = Alignment.__mode(screen_mode)
        self.__surface_meth = Alignment.__mode(surface_mode)
        self.flags = _reduce(lambda flag, newflag: flag | newflag, flags, Alignment.Flag.NONE)
        self.__offset = Vector.zero
        if Alignment.Flag.FILL in self.flags:
            match facing := kwargs.get("facing"):
                case Alignment.Facing():
                    self.__facing = facing
                case str() if facing in ("LEFT", "RIGHT", "UP", "DOWN", "ALL"):
                    match facing:
                        case "LEFT":
                            self.__facing = Alignment.Facing.LEFT
                        case "RIGHT":
                            self.__facing = Alignment.Facing.RIGHT
                        case "UP":
                            self.__facing = Alignment.Facing.UP
                        case "DOWN":
                            self.__facing = Alignment.Facing.DOWN
                        case "ALL":
                            self.__facing = Alignment.Facing.ALL
                case str():
                    raise ValueError(f"Unknown facing: {facing}")
                case _:
                    raise TypeError(
                        "Expected 'facing' key with a facing value for a filling alignment"
                    )
        if Alignment.Flag.REFERENCED in self.flags:
            if not isinstance(offset := kwargs.get("offset"), Vector):
                raise TypeError(
                    "Expected 'offset' key with a vector value for a referenced alignment"
                )
            self.__offset = offset
    
    def __call__(self, screen: _Surface, surface: _Surface) -> Vector:
        '''
        Return the reference point on the screen of the given alignment mode.

        Parameters
        ----------
        screen: :class:`pygame.Surface`
            The main screen which the surface is displayed on.
        surface: :class:`pygame.Surface`
            The surface object to be displayed on the screen.

        Returns
        -------
        :class:`Vector`
            The reference point. A reference point is the top-left corner of the surface on the 
            screen. If a display coordinate is given when dispalying, the surface will be 
            displayed with the display coordinate as an offset.
        '''
        return self.__screen_meth(screen) - self.__surface_meth(surface) + self.__offset
    
    def repeat(self, screen: _Surface, surface: _Surface) -> _Generator[Vector, None, None]:
        '''
        Return a generator which generates all the reference points on the screen of the given 
        alignment mode with flag ``FILL``.
        
        Parameters
        ----------
        screen: :class:`pygame.Surface`
            The main screen which the surface is displayed on.
        surface: :class:`pygame.Surface`
            The surface object to be displayed on the screen.

        Returns
        -------
        :class:`Generator[Vector, None, None]`
            The generator which generates all the reference points. A reference point is the 
            top-left corner of the surface on the screen. If a display coordinate is given when 
            dispalying, the surface will be displayed with the display coordinate as an offset.
        '''
        def LowerBound(coordinate: int, surface_size: int) -> int:
            return -(1 + (coordinate - 1) // surface_size)
        def UpperBound(coordinate: int, screen_size: int, surface_size: int) -> int:
            return 1 + (screen_size - coordinate + surface_size) // surface_size
        
        reference = self.__call__(screen, surface)
        reference_x, reference_y = reference.inttuple
        screen_x, screen_y = screen.get_size()
        surface_x, surface_y = surface.get_size()
        match self.__facing:
            case Alignment.Facing.LEFT:
                range_x = range(LowerBound(reference_x, surface_x), 1)
                range_y = range(
                    LowerBound(reference_y, surface_y), 
                    UpperBound(reference_y, screen_y, surface_y) + 1
                )
            case Alignment.Facing.RIGHT:
                range_x = range(0, UpperBound(reference_x, screen_x, surface_x) + 1)
                range_y = range(
                    LowerBound(reference_y, surface_y), 
                    UpperBound(reference_y, screen_y, surface_y) + 1
                )
            case Alignment.Facing.UP:
                range_x = range(
                    LowerBound(reference_x, surface_x), 
                    UpperBound(reference_x, screen_x, surface_x) + 1
                )
                range_y = range(LowerBound(reference_y, surface_y), 1)
            case Alignment.Facing.DOWN:
                range_x = range(
                    LowerBound(reference_x, surface_x), 
                    UpperBound(reference_x, screen_x, surface_x) + 1
                )
                range_y = range(0, UpperBound(reference_y, screen_y, surface_y) + 1)
            case Alignment.Facing.ALL:
                range_x = range(
                    LowerBound(reference_x, surface_x), 
                    UpperBound(reference_x, screen_x, surface_x) + 1
                )
                range_y = range(
                    LowerBound(reference_y, surface_y), 
                    UpperBound(reference_y, screen_y, surface_y) + 1
                )

        for i, j in _product(range_x, range_y):
            yield reference + Vector(i * surface_x, j * surface_y)
    

class Displayable:
    '''
    The class representing a displayable object. 

    Attributes
    ----------
    surface: :class:`pygame.Surface`
        The displaying surface of the object.
    alignment: :class:`Alignment`
        The alignment mode of the object.
    '''
    def __init__(self, surface: _Surface, alignment: Alignment) -> None:
        self.surface = surface
        self.alignment = alignment

    def __topleft(self, screen: _Surface, display_coordinate: Vector) -> Vector:
        return self.alignment(screen, self.surface) + display_coordinate

    def display(self, screen: _Surface, display_coordinate: Vector) -> None:
        '''
        Display the object on the screen.

        Parameters
        ----------
        screen: :class:`pygame.surface`
            The main screen which the surface is displayed on.
        display_coordinate: :class:`Vector`
            The display coordinate relative to the reference point.
        '''
        if not Alignment.Flag.FILL in self.alignment.flags:
            screen.blit(self.surface, self.__topleft(screen, display_coordinate).inttuple)
            return
        for reference in self.alignment.repeat(screen, self.surface):
            screen.blit(self.surface, (reference + display_coordinate).inttuple)

    def contains(
            self, screen: _Surface, display_coordinate: Vector, input_coordinate: Vector
        ) -> bool:
        '''
        Check whether the player input hits inside the surface.

        Parameters
        ----------
        screen: :class:`pygame.surface`
            The main screen which the surface is displayed on.
        display_coordinate: :class:`Vector`
            The display coordinate relative to the reference point.
        input_coordinate: :class:`Vector`
            The coordinate of the player input.

        Returns
        -------
        `bool`
            Whether the player input hits inside the surface.
        '''
        top_left = self.__topleft(screen, display_coordinate)
        size_x, size_y = self.surface.get_size()
        return top_left.x <= input_coordinate.x < top_left.x + size_x \
            and top_left.y <= input_coordinate.y < top_left.y + size_y
    

class StaticDisplayable(Displayable):
    '''
    The class representing a displayable object whose coordinates are not frequently changed.

    Attributes
    ----------
    surface: :class:`pygame.Surface`
        The displaying surface of the object.
    display_coordinate: :class:`Vector`
        The display coordinate relative to the reference point.
    alignment: :class:`Alignment`
        The alignment mode of the object.
    '''
    def __init__(
        self, surface: _Surface, display_coordinate: Vector, alignment: Alignment
    ) -> None:
        super().__init__(surface, alignment)
        self.display_coordinate = display_coordinate

    def display(self, screen: _Surface) -> None:
        '''
        Display the object on the screen.

        Parameters
        ----------
        screen: :class:`pygame.surface`
            The main screen which the surface is displayed on.
        '''
        return super().display(screen, self.display_coordinate)

    def contains(self, screen: _Surface, input_coordinate: Vector) -> bool:
        '''
        Check whether the player input hits inside the surface.

        Parameters
        ----------
        screen: :class:`pygame.surface`
            The main screen which the surface is displayed on.
        input_coordinate: :class:`Vector`
            The coordinate of the player input.

        Returns
        -------
        `bool`
            Whether the player input hits inside the surface.
        '''
        return super().contains(screen, self.display_coordinate, input_coordinate)


class DisplayableText(StaticDisplayable):
    '''
    The class representing a static displayable text.

    Attributes
    ----------
    surface: :class:`pygame.Surface`
        The displaying surface of the object.
    display_coordinate: :class:`Vector`
        The display coordinate relative to the reference point.
    alignment: :class:`Alignment`
        The alignment mode of the object.

    Properties
    ----------
    font: :class:`pygame.font.Font`
        The font of the text.
    text: :class:`str`
        The content of the text.
    color: :class:`ColorType`
        The color of the text.
    '''
    def __init__(
            self, 
            display_coordinate: Vector, 
            alignment: Alignment, 
            font: _Font, 
            text: str = "", 
            color: ColorType = _COLOR_BLACK
    ) -> None:
        self.__font = font
        self.__text = text
        self.__color = color
        self.__update_surface()
        super().__init__(self.surface, display_coordinate, alignment)

    def __update_surface(self) -> None:
        self.surface = self.__font.render(self.__text, False, self.__color)

    @property
    def font(self) -> _Font:
        return self.__font
    
    @font.setter
    def font(self, __font: _Font) -> None:
        self.__font = __font
        self.__update_surface()

    @property
    def text(self) -> str:
        return self.__text

    @text.setter
    def text(self, __t: str) -> None:
        self.__text = __t
        self.__update_surface()

    @property
    def color(self) -> ColorType:
        return self.__color

    @color.setter
    def color(self, __c: ColorType) -> None:
        self.__color = __c
        self.__update_surface()


class DisplayableBall(Displayable):
    '''
    The class representing a displayable object. 

    Attributes
    ----------
    base_surface: :class:`pygame.Surface`
        The unrotated surface of the object.
    alignment: :class:`Alignment`
        The alignment mode of the object.
    '''
    def __init__(self, base_surface: _Surface, alignment: Alignment) -> None:
        self.base_surface = self.surface = base_surface
        self.alignment = alignment

    def display(self, screen: _Surface, display_coordinate: Vector, angle: NumberType) -> None:
        '''
        Display the object on the screen.

        Parameters
        ----------
        screen: :class:`pygame.surface`
            The main screen which the surface is displayed on.
        display_coordinate: :class:`Vector`
            The display coordinate relative to the reference point.
        angle: :class:`NumberType`
            The rotation angle of the ball, in unit of degree.
        '''
        self.surface = rotate(self.base_surface, -angle)
        return super().display(screen, display_coordinate)