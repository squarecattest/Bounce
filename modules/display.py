from pygame import Surface as _Surface, Color as _Color
from pygame.font import Font as _Font
from vector import Vector
from typing import Union as _Union

type ColorType = _Union[_Color, int, str, tuple[int, int, int], tuple[int, int, int, int]]
_COLOR_BLACK = (0, 0, 0)

class Align:
    '''
    The class representing an alignment mode for a displayable object. The two strings in the 
    alignment type show the align mode:
    - The first string is the mode of the screen alignment. 
    - The second string is the mode of the surface alignment.

    The strings specify different alignment mode:
    - DEFAULT: Coordinates are given with respect to the top-left corner.
    - CENTERED: Coordinates are given with respect to the center of the surface.
    - LEFT: Coordinates are given with respect to the center of the left side.
    '''
    def __init__(self, mode: str) -> None:
        if not isinstance(mode, str):
            raise TypeError(f"Excepted string, got {type(mode).__name__}")
        match mode:
            case "DEFAULT_DEFAULT":
                self.__meth = lambda screen, surface: Vector.zero
            case "DEFAULT_CENTERED":
                self.__meth = lambda screen, surface: -(Vector(surface.get_size()) // 2)
            case "CENTERED_CENTERED":
                self.__meth = lambda screen, surface: \
                    Vector(screen.get_size()) // 2 - Vector(surface.get_size()) // 2
            case "CENTERED_LEFT":
                self.__meth = lambda screen, surface: \
                    Vector(screen.get_size()) // 2 - Vector(0, surface.get_size()[1] // 2)
            case _:
                raise ValueError(f"Unknown alignment mode '{mode}'")
    
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
            The reference point on the screen. When the display coordinate (the offset of the 
            surface) is (0, 0), the reference point is the coordinate of the top-left corner of 
            the surface.
        '''
        return self.__meth(screen, surface)
    
    @classmethod
    @property
    def DEFAULT_DEFAULT(cls) -> "Align":
        return cls("DEFAULT_DEFAULT")

    @classmethod
    @property
    def DEFAULT_CENTERED(cls) -> "Align":
        return cls("DEFAULT_CENTERED")

    @classmethod
    @property
    def CENTERED_CENTERED(cls) -> "Align":
        return cls("CENTERED_CENTERED")

    @classmethod
    @property
    def CENTERED_LEFT(cls) -> "Align":
        return cls("CENTERED_LEFT")


class Displayable:
    '''
    The class representing a displayable object. 

    Attributes
    ----------
    surface: :class:`pygame.Surface`
        The displaying surface of the object.
    display_coordinate: :class:`Vector`
        The display coordinate relative to the reference point.
    align: :class:`Align`
        The alignment mode of the object.
    '''
    def __init__(self, surface: _Surface, display_coordinate: Vector, align: Align) -> None:
        self.surface = surface
        self.display_coordinate = display_coordinate
        self.align = align

    def __topleft(self, screen: _Surface) -> Vector:
        return self.align(screen, self.surface) + self.display_coordinate

    def display(self, screen: _Surface) -> None:
        '''
        Display the object in the screen.

        Parameters
        ----------
        screen: :class:`pygame.surface`
            The main screen which the surface is displayed on.
        '''
        screen.blit(self.surface, self.__topleft(screen).inttuple)

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
        top_left = self.__topleft(screen)
        size_x, size_y = self.surface.get_size()
        return top_left.x <= input_coordinate.x < top_left.x + size_x \
            and top_left.y <= input_coordinate.y < top_left.y + size_y

    
class DisplayableText(Displayable):
    '''
    The class representing a displayable text.

    Attributes
    ----------
    surface: :class:`pygame.Surface`
        The displaying surface of the object.
    display_coordinate: :class:`Vector`
        The display coordinate relative to the reference point.
    align: :class:`Align`
        The alignment mode of the object.

    Properties
    ----------
    font: :class:`pygame.font.Font`
        The font of the text.
    text: :class:`str`
        The content of the text.
    color: :class:`tuple[int, int, int]`
        The color of the text.
    '''
    def __init__(
            self, 
            display_coordinate: Vector, 
            align: Align, 
            font: _Font, 
            text: str = "", 
            color: ColorType = _COLOR_BLACK
    ) -> None:
        self.__font = font
        self.__text = text
        self.__color = color
        self.__update_surface()
        super().__init__(self.surface, display_coordinate, align)

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
