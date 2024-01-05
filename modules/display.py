from pygame import Surface, Color as pgColor
from pygame.font import Font
from pygame.transform import rotate
from vector import Vector, NumberType
from language import Language, TranslateName, Translatable
from resources import Color
from enum import Enum, Flag, auto
from itertools import product
from functools import reduce
from typing import Union, Callable, Generator

type ColorType = Union[pgColor, int, str, tuple[int, int, int], tuple[int, int, int, int]]

def _typename(arg) -> str:
    return type(arg).__name__

class Alignment:
    '''
    The class representing an alignment mode for a displayable object. Two modes will be 
    specified in this class, one for the screen and one for the surface. The two points of 
    the screen and the surface given by the alignment modes will be aligned, which gives the 
    unique reference point of a displayable object.
    '''
    class Mode(Enum):
        DEFAULT = auto()
        '''
        The surface will be aligned at the top-left corner.
        '''
        CENTERED = auto()
        '''
        The surface will be aligned at the center of the surface.
        '''
        LEFT = auto()
        '''
        The surface will be aligned at the center of the left side.
        '''
        RIGHT = auto()
        '''
        The surface will be aligned at the center of the right side.
        '''
        TOP = auto()
        '''
        The surface will be aligned at the center of the top side.
        '''
        BOTTOM = auto()
        '''
        The surface will be aligned at the center of the bottom side.
        '''

    class Flag(Flag):
        NONE = 0
        FILL = auto()
        '''
        Repeat the surface to fill the specified region. If the alignment mode is a side, the 
        facing direction will be filled. (For example, if the mode is ``LEFT``, the right part 
        of the screen will be filled.) Otherwise, the whole screen will be filled.
        '''
        REFERENCED = auto()
        '''
        Place the surface with an offset.
        '''

    class Facing(Enum):
        LEFT = auto()
        RIGHT = auto()
        UP = auto()
        DOWN = auto()
        ALL = auto()

    @staticmethod
    def __mode(align: Mode) -> Callable[[Surface], Vector]:
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
    
    __screenmeth: Callable[[Surface], Vector]
    __surfacemeth: Callable[[Surface], Vector]
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
        
        self.__screenmeth = Alignment.__mode(screen_mode)
        self.__surfacemeth = Alignment.__mode(surface_mode)
        self.flags = reduce(lambda flag, newflag: flag | newflag, flags, Alignment.Flag.NONE)
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
    
    def __call__(
            self, 
            screen: Surface, 
            surface: Surface, 
            offset: Vector = Vector.zero
        ) -> Vector:
        '''
        Return the display coordinate on the screen of the given alignment mode.

        Parameters
        ----------
        screen: :class:`pygame.Surface`
            The main screen which the surface is displayed on.
        surface: :class:`pygame.Surface`
            The surface object to be displayed on the screen.
        offset: :class:`Vector`
            The offset of the display relative to the reference point.

        Returns
        -------
        :class:`Vector`
            The display coordinate.
        '''
        return self.__screenmeth(screen) - self.__surfacemeth(surface) + self.__offset + offset
    
    def repeat(
            self, 
            screen: Surface, 
            surface: Surface, 
            offset: Vector
        ) -> Generator[Vector, None, None]:
        '''
        Return a generator which generates all the display coordinates on the screen of the 
        given alignment mode with flag ``FILL``.
        
        Parameters
        ----------
        screen: :class:`pygame.Surface`
            The main screen which the surface is displayed on.
        surface: :class:`pygame.Surface`
            The surface object to be displayed on the screen.
        offset: :class:`Vector`
            The offset of the display relative to the reference point.

        Returns
        -------
        :class:`Generator[Vector, None, None]`
            The generator which generates all the display coordinates.
        '''
        def LowerBound(coordinate: int, surface_size: int) -> int:
            return -(1 + (coordinate - 1) // surface_size)
        def UpperBound(coordinate: int, screen_size: int, surface_size: int) -> int:
            return 1 + (screen_size - coordinate + surface_size) // surface_size
        
        display = self.__call__(screen, surface) + offset
        display_x, display_y = display.inttuple
        screen_x, screen_y = screen.get_size()
        surface_x, surface_y = surface.get_size()
        match self.__facing:
            case Alignment.Facing.LEFT:
                range_x = range(LowerBound(display_x, surface_x), 1)
                range_y = range(
                    LowerBound(display_y, surface_y), 
                    UpperBound(display_y, screen_y, surface_y) + 1
                )
            case Alignment.Facing.RIGHT:
                range_x = range(0, UpperBound(display_x, screen_x, surface_x) + 1)
                range_y = range(
                    LowerBound(display_y, surface_y), 
                    UpperBound(display_y, screen_y, surface_y) + 1
                )
            case Alignment.Facing.UP:
                range_x = range(
                    LowerBound(display_x, surface_x), 
                    UpperBound(display_x, screen_x, surface_x) + 1
                )
                range_y = range(LowerBound(display_y, surface_y), 1)
            case Alignment.Facing.DOWN:
                range_x = range(
                    LowerBound(display_x, surface_x), 
                    UpperBound(display_x, screen_x, surface_x) + 1
                )
                range_y = range(0, UpperBound(display_y, screen_y, surface_y) + 1)
            case Alignment.Facing.ALL:
                range_x = range(
                    LowerBound(display_x, surface_x), 
                    UpperBound(display_x, screen_x, surface_x) + 1
                )
                range_y = range(
                    LowerBound(display_y, surface_y), 
                    UpperBound(display_y, screen_y, surface_y) + 1
                )

        for i, j in product(range_x, range_y):
            yield display + Vector(i * surface_x, j * surface_y)
    

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
    def __init__(self, surface: Surface, alignment: Alignment) -> None:
        self.surface = surface
        self.alignment = alignment

    def display(self, screen: Surface, offset: Vector) -> None:
        '''
        Display the object on the screen.

        Parameters
        ----------
        screen: :class:`pygame.surface`
            The main screen which the surface is displayed on.
        offset: :class:`Vector`
            The offset of the display relative to the reference point.
        '''
        if not Alignment.Flag.FILL in self.alignment.flags:
            screen.blit(self.surface, self.alignment(screen, self.surface, offset).inttuple)
            return
        for display in self.alignment.repeat(screen, self.surface, offset):
            screen.blit(self.surface, display.inttuple)

    def contains(
            self, 
            screen: Surface, 
            offset: Vector, 
            input_coordinate: Vector
        ) -> bool:
        '''
        Check whether the player input hits inside the surface.

        Parameters
        ----------
        screen: :class:`pygame.surface`
            The main screen which the surface is displayed on.
        offset: :class:`Vector`
            The offset of the display relative to the reference point.
        input_coordinate: :class:`Vector`
            The coordinate of the player input.

        Returns
        -------
        `bool`
            Whether the player input hits inside the surface.
        '''
        top_left = self.alignment(screen, self.surface, offset)
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
    offset: :class:`Vector`
        The offset of the display relative to the reference point.
    alignment: :class:`Alignment`
        The alignment mode of the object.
    '''
    def __init__(
        self, surface: Surface, offset: Vector, alignment: Alignment
    ) -> None:
        super().__init__(surface, alignment)
        self.offset = offset

    def display(self, screen: Surface) -> None:
        '''
        Display the object on the screen.

        Parameters
        ----------
        screen: :class:`pygame.surface`
            The main screen which the surface is displayed on.
        '''
        return super().display(screen, self.offset)

    def contains(self, screen: Surface, input_coordinate: Vector) -> bool:
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
        return super().contains(screen, self.offset, input_coordinate)


class DisplayableText(StaticDisplayable):
    '''
    The class representing a static displayable text.

    Attributes
    ----------
    surface: :class:`pygame.Surface`
        The displaying surface of the object.
    offset: :class:`Vector`
        The offset of the display relative to the reference point.
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
    background: Union[:class:`ColorType`, ``None``]
        The background color of the text. 
    alpha: :class:`int`
        The alpha value of the surface.
    '''
    def __init__(
            self, 
            offset: Vector, 
            alignment: Alignment, 
            font: Font, 
            text: str = "", 
            color: ColorType = Color.BLACK, 
            background: ColorType | None = None, 
            alpha: int = 255
    ) -> None:
        self.__font = font
        self.__text = text
        self.__color = color
        self.__background = background
        self.__alpha = alpha
        self.__update_surface()
        super().__init__(self.surface, offset, alignment)

    def __update_surface(self) -> None:
        self.surface = self.__font.render(self.__text, False, self.__color, self.__background)
        self.surface.set_alpha(self.__alpha)

    @property
    def font(self) -> Font:
        return self.__font
    
    @font.setter
    def font(self, __font: Font) -> None:
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

    @property
    def background(self) -> ColorType | None:
        return self.__background
    
    @background.setter
    def background(self, __c: ColorType | None) -> None:
        self.__background = __c
        self.__update_surface()

    @property
    def alpha(self) -> int:
        return self.__alpha
    
    @alpha.setter
    def alpha(self, __a: int) -> None:
        self.__alpha = __a
        self.__update_surface()
 

class DisplayableTranslatable(DisplayableText):
    
    '''
    The class representing a static displayable translated text.

    Attributes
    ----------
    surface: :class:`pygame.Surface`
        The displaying surface of the object.
    offset: :class:`Vector`
        The offset of the display relative to the reference point.
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
    background: Union[:class:`ColorType`, ``None``]
        The background color of the text. 
    alpha: :class:`int`
        The alpha value of the surface.
    '''
    def __init__(
            self, 
            offset: Vector, 
            alignment: Alignment, 
            font: Font, 
            translation: TranslateName, 
            language: Language, 
            color: ColorType = Color.BLACK, 
            background: ColorType | None = None, 
            alpha: int = 255
    ) -> None:
        self.__translatable = Translatable(translation, language)
        super().__init__(
            offset, 
            alignment, 
            font, 
            self.__translatable.get(language), 
            color, 
            background, 
            alpha
        )

    def display(self, screen: Surface, language: Language = None) -> None:
        if language == self.__translatable.language or language is None:
            return super().display(screen)
        super().__text = self.__translatable.get(language)
        super().__update_surface()
        super().display(screen)

    @property
    def language(self) -> Language:
        return self.__translatable.language
    
    @language.setter
    def language(self, language: Language) -> None:
        super().__text = self.__translatable.get(language)
        super().__update_surface()

 
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
    def __init__(self, frame: Surface, base_surface: Surface, alignment: Alignment) -> None:
        self.frame = frame
        self.base_surface = base_surface
        self.surface = self.frame.copy()
        self.alignment = alignment
        self.__blit_alignment = Alignment(Alignment.Mode.CENTERED, Alignment.Mode.CENTERED)

    def __blit(self, angle: NumberType) -> None:
        self.surface = self.frame.copy()
        StaticDisplayable(
            rotate(self.base_surface, -angle), 
            Vector.zero, 
            self.__blit_alignment
        ).display(self.surface)
        

    def display(self, screen: Surface, offset: Vector, angle: NumberType) -> None:
        '''
        Display the object on the screen.

        Parameters
        ----------
        screen: :class:`pygame.surface`
            The main screen which the surface is displayed on.
        offset: :class:`Vector`
            The offset of the display relative to the reference point.
        angle: :class:`NumberType`
            The rotation angle of the ball, in unit of degree.
        '''
        self.__blit(angle)
        return super().display(screen, offset)