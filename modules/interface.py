import pygame
from pygame import Surface
from pygame.event import Event
from pygame import draw
from game import Game, get_level, get_height
from display import (
    Alignment, 
    Displayable, 
    DisplayableBall, 
    DisplayableText, 
    DisplayableTranslatable, 
    StaticDisplayable
)
from language import TranslateName
from resources import Font, Texture, Color, Path, MAIN_SCREEN, CENTER_SCREEN
from vector import Vector, NumberType
from physics import _to_degree
from language import Language
from setting import Setting
from utils import Timer, Ticker, time_string
from constants import GeneralConstant, InterfaceConstant as Constant
from collections import deque
from enum import Enum, IntEnum, Flag, auto
from abc import ABC, abstractmethod
from typing import Any, NamedTuple, Union, Iterable, Generator, Literal


type Request = Union[GameRequest, OptionRequest]

class GameRequest(Enum):
    GOTO_OPTIONS = auto()
    GOTO_ACHIEVEMENT = auto()
    GOTO_CONTROLS = auto()
    QUIT = auto()


class OptionRequest(Enum):
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]) -> Any:
        return Enum._generate_next_value_(
            name, 
            len(GameRequest) + 1, 
            count, 
            last_values
        )
    
    CHANGE_LANGUAGE = auto()
    CHANGE_FPS = auto()
    BACK = auto()


class Interface(ABC):
    BACKGROUND = StaticDisplayable(
        Texture.BACKGROUND, 
        Vector.zero, 
        Alignment(
            Alignment.Mode.CENTERED, 
            Alignment.Mode.CENTERED, 
            Alignment.Flag.FILL, 
            facing=Alignment.Facing.ALL
        )
    )

    @property
    def isGameInterface(self) -> bool:
        return isinstance(self, GameInterface)

    @abstractmethod
    def add_event(self, event: Event) -> None:
        pass

    @abstractmethod
    def get_request(self) -> Iterable[Request]:
        pass

    @abstractmethod
    def display(main_screen: Surface, center_screen: Surface, *args, **kwargs) -> None:
        pass


class GameInterface(Interface):
    class GameEvent(Enum):
        EMPTY = auto()
        GAME_SPACE = auto()
        GAME_GAMEOVER = auto()
        GAME_RESTART = auto()
        GAME_RELOAD = auto()
        GAME_RELOADED = auto()
        GAME_DEBUG = auto()
        SELECTION_UP = auto()
        SELECTION_DOWN = auto()
        SELECTION_ENTER = auto()
        QUIT = auto()

    class GameStatus(Flag):
        LOADED = auto()
        STARTING = auto()
        STARTED = auto()
        GAMEOVER = auto()
        RESTARTING = auto()
        RELOADING = auto()

    class PageSelection(IntEnum):
        OPTIONS = auto()
        ACHIEVEMENT = auto()
        CONTROLS = auto()
        QUIT = auto()

        def upper(self) -> "GameInterface.PageSelection":
            if self == 1:
                return self
            return GI.PS(self - 1)
        
        def lower(self) -> "GameInterface.PageSelection":
            if self == len(GI.PS):
                return self
            return GI.PS(self + 1)

    class DebugMsgTimer(NamedTuple):
        msg: str
        timer: Timer

    GE = GameEvent
    GS = GameStatus
    PS = PageSelection

    def __init__(self, language: Language) -> None:
        self.game = Game(Path.LEVEL)
        self.language = language
        self.ingame_timer = Timer()
        self.tick_timer = Timer(start=True)
        self.transform_timer = Timer()
        self.status = GI.GS.LOADED
        self.bounce = False
        self.debugging = False
        self.record_height = 0
        self.height = 0
        self.selection = GI.PS.OPTIONS
        self.requests: deque[GameRequest] = deque()
        self.debug_msgs: deque[GI.DebugMsgTimer] = deque()
        self.ball_display = DisplayableBall(
            Texture.BALL_FRAME, 
            Texture.BALL_SURFACE, 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.ground_display = Displayable(
            Texture.GROUND, 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.TOP, 
                Alignment.Flag.FILL, 
                Alignment.Flag.REFERENCED, 
                facing=Alignment.Facing.DOWN, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.slab_display = Displayable(
            Texture.SLAB, Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED,
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.scoreboard_bg = StaticDisplayable(
            Texture.SCOREBOARD, 
            Vector(560, 0), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.TOP, 
                Alignment.Flag.FILL, 
                Alignment.Flag.REFERENCED, 
                facing=Alignment.Facing.UP, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.start_display = DisplayableTranslatable(
            Vector(560, 580), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            ), 
            Font.Game.START_TEXT, 
            TranslateName.game_start_text, 
            language, 
            Color.Game.START_TEXT
        )
        self.gameover_display = DisplayableTranslatable(
            Vector.zero, 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED
            ), 
            Font.Game.RESTART_TEXT, 
            TranslateName.game_restart_text, 
            self.language, 
            Color.Game.RESTART_TEXT
        )
        self.selection_displays = (
            DisplayableTranslatable(
                Vector.zero, 
                Alignment(
                    Alignment.Mode.CENTERED, 
                    Alignment.Mode.LEFT, 
                    Alignment.Flag.REFERENCED, 
                    offset=Constant.SCREEN_OFFSET
                ), 
                Font.Game.SELECTION_MENU_TEXT, 
                TranslateName.game_selctionmenu_options, 
                self.language, 
                Color.Game.SELECTION_MENU_TEXT
            ), 
            DisplayableTranslatable(
                Vector.zero, 
                Alignment(
                    Alignment.Mode.CENTERED, 
                    Alignment.Mode.LEFT, 
                    Alignment.Flag.REFERENCED, 
                    offset=Constant.SCREEN_OFFSET
                ), 
                Font.Game.SELECTION_MENU_TEXT, 
                TranslateName.game_selctionmenu_achievements, 
                self.language, 
                Color.Game.SELECTION_MENU_TEXT
            ), 
            DisplayableTranslatable(
                Vector.zero, 
                Alignment(
                    Alignment.Mode.CENTERED, 
                    Alignment.Mode.LEFT, 
                    Alignment.Flag.REFERENCED, 
                    offset=Constant.SCREEN_OFFSET
                ), 
                Font.Game.SELECTION_MENU_TEXT, 
                TranslateName.game_selctionmenu_controls, 
                self.language, 
                Color.Game.SELECTION_MENU_TEXT
            ), 
            DisplayableTranslatable(
                Vector.zero, 
                Alignment(
                    Alignment.Mode.CENTERED, 
                    Alignment.Mode.LEFT, 
                    Alignment.Flag.REFERENCED, 
                    offset=Constant.SCREEN_OFFSET
                ), 
                Font.Game.SELECTION_MENU_TEXT, 
                TranslateName.game_selctionmenu_quit, 
                self.language, 
                Color.Game.SELECTION_MENU_TEXT
            )
        )
        self.selection_menu_arrow_display = Displayable(
            Texture.SELECTION_MENU_ARROW, 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.blackscene_display = StaticDisplayable(
            Surface(GeneralConstant.DEFAULT_SCREEN_SIZE), 
            Vector.zero, 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED
            )
        )
        self.blackscene_display.surface.fill(Color.BLACK)
        self.blackscene_alpha = 0
        self.blackscene_display.surface.set_colorkey(Color.Game.RESTART_COLORKEY)

    def __tick(self) -> None:
        ticks = int(Constant.INGAME_FPS * self.tick_timer.read())
        self.tick_timer.offset(-ticks * Constant.DT)
        self.game.tick(Constant.DT, self.bounce)
        self.bounce = False
        for _ in range(ticks - 1):
            self.game.tick(Constant.DT, False)
        self.height = max(self.height, self.game.ball.pos_y)
        if not GI.GameStatus.GAMEOVER in self.status and self.game.gameover:
            self.__handle_event(GI.GE.GAME_GAMEOVER)
        self.__read_debug_msg()

    def add_event(self, event: Event) -> None:
        self.__handle_event(self.__event_converter(event))

    def get_request(self) -> Generator[GameRequest, None, None]:
        while self.requests:
            yield self.requests.popleft()

    def __restart(self) -> None:
        self.game.restart()
        self.ingame_timer.stop()
        self.tick_timer.restart()
        self.height = 0
        self.debug_msgs.clear()
        self.selection = GI.PS.OPTIONS

    def __handle_event(self, event: GameEvent) -> None:
        match event:
            case GI.GE.GAME_SPACE if GI.GS.GAMEOVER in self.status \
                and not GI.GS.RESTARTING in self.status:
                if self.transform_timer.read() > 2:
                    self.__handle_event(GI.GE.GAME_RESTART)
            case GI.GE.GAME_SPACE if (GI.GS.RELOADING | GI.GS.LOADED) & self.status:
                self.ingame_timer.start()
                self.status |= GI.GS.STARTING | GI.GS.STARTED
                self.bounce = True
            case GI.GE.GAME_SPACE if (GI.GS.STARTING | GI.GS.STARTED) & self.status:
                self.bounce = True
            case GI.GE.GAME_DEBUG:
                self.debugging = not self.debugging
            case GI.GE.GAME_GAMEOVER:
                self.ingame_timer.pause()
                self.transform_timer.restart()
                self.status = GI.GS.GAMEOVER
            case GI.GE.GAME_RESTART:
                self.blackscene_display.surface.fill(Color.BLACK)
                self.transform_timer.restart()
                self.status |= GI.GS.RESTARTING
            case GI.GE.GAME_RELOAD:
                self.__restart()
                self.transform_timer.restart()
                self.status = GI.GS.RELOADING
            case GI.GE.GAME_RELOADED:
                self.status |= GI.GS.LOADED
            case GI.GE.SELECTION_UP if (
                (GI.GS.RELOADING | GI.GS.LOADED) & self.status
                and not (GI.GS.STARTING | GI.GS.STARTED) & self.status
            ):
                self.selection = self.selection.upper()
            case GI.GE.SELECTION_DOWN if (
                (GI.GS.RELOADING | GI.GS.LOADED) & self.status
                and not (GI.GS.STARTING | GI.GS.STARTED) & self.status
            ):
                self.selection = self.selection.lower()
            case GI.GE.SELECTION_ENTER if (
                (GI.GS.RELOADING | GI.GS.LOADED) & self.status
                and not (GI.GS.STARTING | GI.GS.STARTED) & self.status
            ):
                match self.selection:
                    case GI.PS.OPTIONS:
                        self.requests.append(GameRequest.GOTO_OPTIONS)
                    case GI.PS.ACHIEVEMENT:
                        self.requests.append(GameRequest.GOTO_ACHIEVEMENT)
                    case GI.PS.CONTROLS:
                        self.requests.append(GameRequest.GOTO_CONTROLS)
                    case GI.PS.QUIT:
                        self.requests.append(GameRequest.QUIT)
            case GI.GE.QUIT:
                pass

    def __event_converter(self, event: Event) -> GameEvent:
        match event.type:
            case pygame.KEYDOWN:
                match event.key:
                    case pygame.K_SPACE:
                        return GI.GE.GAME_SPACE
                    case pygame.K_d:
                        return GI.GE.GAME_DEBUG
                    case pygame.K_UP:
                        return GI.GE.SELECTION_UP
                    case pygame.K_DOWN:
                        return GI.GE.SELECTION_DOWN
                    case pygame.K_RETURN:
                        return GI.GE.SELECTION_ENTER
            case pygame.QUIT:
                return GI.GE.QUIT
        return GI.GE.EMPTY
    
    def __read_debug_msg(self) -> None:
        self.debug_msgs.extend(
            GI.DebugMsgTimer(text, Timer(start=True)) for text in self.game.ball.debug_msgs
        )
        while (
            self.debug_msgs
            and self.debug_msgs[0].timer.read() > Constant.DEBUG_TEXT_LASTING_TIME
        ):
            self.debug_msgs.popleft()

    def display(
            self, 
            main_screen: Surface, 
            center_screen: Surface, 
            set_FPS: int, 
            real_FPS: int
        ) -> None:
        Interface.BACKGROUND.display(main_screen)
        center_screen.fill(Color.WHITE)
        self.__tick()
        self.ground_display.display(
            center_screen, 
            self.game.position_map(self.game.ground.position)
        )
        for slab in self.game.slabs:
            self.slab_display.display(
                center_screen, 
                self.game.position_map(slab.position)
            )
        self.__level_display(center_screen)
        self.ball_display.display(
            center_screen, 
            self.game.position_map(self.game.ball.position), 
            self.game.ball.deg_angle
        )
        if self.debugging:
            self.__debug_display(center_screen, set_FPS, real_FPS)
        if (GI.GS.RELOADING | GI.GS.LOADED | GI.GS.STARTING) & self.status:
            self.__starting_display(center_screen)
        if GI.GS.GAMEOVER in self.status:
            self.__gameover_display(center_screen)
        self.__scoreboard_display(center_screen)
        if GI.GS.RESTARTING in self.status:
            self.__restarting_display(center_screen)
        if GI.GS.RELOADING in self.status:
            self.__reloading_display(center_screen)

    def __starting_display(self, screen: Surface) -> None:
        offset = 1000 * (self.ingame_timer.read() - 0.1) ** 2 - 10
        if offset > 110:
            self.status &= ~GI.GS.STARTING
            return
        self.start_display.offset = Vector(560, Constant.STARTING_TEXT_CENTER + offset)
        self.start_display.display(screen, self.language)
        for i, display in enumerate(self.selection_displays, start=1):
            display.offset = Vector(
                Constant.SELECTION_MENU_XPOS, 
                Constant.STARTING_TEXT_CENTER 
                    + Constant.SELECTION_MENU_SEP * (i - (len(GI.PS) + 1) / 2) 
                    + offset
            )
            display.display(screen, self.language)
            display.color = Color.Game.SELECTION_MENU_TEXT
        self.selection_menu_arrow_display.display(
            screen, 
            Vector(
                Constant.SELECTION_MENU_ARROW_XPOS, 
                Constant.STARTING_TEXT_CENTER 
                    + Constant.SELECTION_MENU_SEP * (self.selection - (len(GI.PS) + 1) / 2) 
                    + offset
            )
        )

    def __level_display(self, screen: Surface) -> None:
        def at_level(level: int) -> None:
            DisplayableText(
                self.game.position_map(Vector(7, get_height(level)) + Vector(2, -2)), 
                Alignment(
                    Alignment.Mode.CENTERED, 
                    Alignment.Mode.LEFT, 
                    Alignment.Flag.REFERENCED, 
                    offset=Constant.SCREEN_OFFSET
                ), 
                Font.Game.LEVEL_TEXT, 
                str(level), 
                Color.Game.LEVEL_SHADOW
            ).display(screen)
            DisplayableText(
                self.game.position_map(Vector(7, get_height(level)) - Vector(2, -2)), 
                Alignment(
                    Alignment.Mode.CENTERED, 
                    Alignment.Mode.LEFT, 
                    Alignment.Flag.REFERENCED, 
                    offset=Constant.SCREEN_OFFSET
                ), 
                Font.Game.LEVEL_TEXT, 
                str(level), 
                Color.Game.LEVEL_TEXT
            ).display(screen)
        at_level(1)
        for slab_level in self.game.slab_levels:
            at_level(slab_level.level)

    def __scoreboard_display(self, screen: Surface) -> None:
        self.scoreboard_bg.display(screen)
        scoreboard_alignment = Alignment(
            Alignment.Mode.CENTERED, 
            Alignment.Mode.LEFT, 
            Alignment.Flag.REFERENCED, 
            offset=Constant.SCREEN_OFFSET
        )
        DisplayableTranslatable(
            Vector(6, 10), 
            scoreboard_alignment, 
            Font.Game.SCOREBOARD_TITLE, 
            TranslateName.game_scoreboard_record_height, 
            self.language, 
            Color.Game.SCOREBOARD_TITLE
        ).display(screen)
        DisplayableText(
            Vector(6, 34), 
            scoreboard_alignment, 
            Font.Game.SCOREBOARD_VALUE, 
            f"{self.record_height}", 
            Color.Game.SCOREBOARD_VALUE
        ).display(screen)
        DisplayableTranslatable(
            Vector(286, 10), 
            scoreboard_alignment, 
            Font.Game.SCOREBOARD_TITLE, 
            TranslateName.game_scoreboard_height, 
            self.language, 
            Color.Game.SCOREBOARD_TITLE
        ).display(screen)
        DisplayableText(
            Vector(286, 34), 
            scoreboard_alignment, 
            Font.Game.SCOREBOARD_VALUE, 
            f"{int(self.height)}", 
            Color.Game.SCOREBOARD_VALUE
        ).display(screen)
        DisplayableTranslatable(
            Vector(566, 10), 
            scoreboard_alignment, 
            Font.Game.SCOREBOARD_TITLE, 
            TranslateName.game_scoreboard_level, 
            self.language, 
            Color.Game.SCOREBOARD_TITLE
        ).display(screen)
        DisplayableText(
            Vector(566, 34), 
            scoreboard_alignment, 
            Font.Game.SCOREBOARD_VALUE, 
            f"{get_level(self.game.ball.pos_y)}", 
            Color.Game.SCOREBOARD_VALUE
        ).display(screen)
        DisplayableTranslatable(
            Vector(846, 10), 
            scoreboard_alignment, 
            Font.Game.SCOREBOARD_TITLE, 
            TranslateName.game_scoreboard_time, 
            self.language, 
            Color.Game.SCOREBOARD_TITLE
        ).display(screen)
        DisplayableText(
            Vector(846, 34), 
            scoreboard_alignment, 
            Font.Game.SCOREBOARD_VALUE, 
            f"{time_string(self.ingame_timer.read())}", 
            Color.Game.SCOREBOARD_VALUE
        ).display(screen)

    def __debug_display(self, screen: Surface, set_FPS: int, real_FPS: int) -> None:
        base_position = Vector(2, 72)
        unit_offset = Vector(0, Constant.DEBUG_TEXT_SEP)
        text_alignment = Alignment(
            Alignment.Mode.CENTERED, 
            Alignment.Mode.LEFT, 
            Alignment.Flag.REFERENCED, 
            offset=Constant.SCREEN_OFFSET
        )
        debug_texts = [
            f"FPS(setting/real-time): {set_FPS}/{real_FPS}", 
            f"position: {self.game.ball.position:.1f}", 
            f"velocity: {self.game.ball.velocity:.1f}", 
            f"angle: {self.game.ball.deg_angle:.1f} deg / {self.game.ball.rad_angle:.2f} rad", 
            f"angular frequency: {self.game.ball.angular_frequency:.2f} rad/s", 
            f"ground: {self.game.ball.ground_text}", 
            f"bounceable: {("false", "true")[self.game.ball.bounceable]}"
        ]
        debug_texts.extend(debug_msg.msg for debug_msg in self.debug_msgs)
        for i, debug_text in enumerate(debug_texts):
            DisplayableText(
                base_position + unit_offset * i, 
                text_alignment, 
                Font.Game.DEBUG_TEXT, 
                debug_text, 
                Color.Game.DEBUG_TEXT, 
                Color.Game.DEBUG_BACKGROUND, 
                Constant.DEBUG_TEXT_ALPHA
            ).display(screen)

    def __gameover_display(self, screen: Surface) -> None:
        if (t := self.transform_timer.read()) > 2 and int(t / 0.5) % 2 == 0:
            self.gameover_display.language = self.language
            background = Surface(
                (Vector(self.gameover_display.surface.get_size()) + Vector(10, 10)).inttuple
            )
            background.fill(Color.Game.RESTART_BACKGROUND)
            background.set_alpha(Constant.RESTART_TEXT_ALPHA)
            self.gameover_display.display(background, self.language)
            StaticDisplayable(
                background, 
                Constant.GAMEOVER_DISPLAY_POS, 
                Alignment(
                    Alignment.Mode.CENTERED, 
                    Alignment.Mode.CENTERED, 
                    Alignment.Flag.REFERENCED, 
                    offset=Constant.SCREEN_OFFSET
                )
            ).display(screen)

    def __restarting_display(self, screen: Surface) -> None:
        background = Surface(
            (Vector(self.gameover_display.surface.get_size()) + Vector(10, 10)).inttuple
        )
        background.fill(Color.Game.RESTART_BACKGROUND)
        self.gameover_display.display(background, self.language)
        StaticDisplayable(
            background, 
            Vector(560, 580), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        ).display(screen)

        self.blackscene_alpha = int(
            self.transform_timer.read() * 255 / Constant.GAMEOVER_FADEOUT_SECOND
        )
        if self.blackscene_alpha < 255:
            self.blackscene_display.surface.set_alpha(self.blackscene_alpha)
            self.blackscene_display.display(screen)
            return
        self.blackscene_display.surface.set_alpha(255)
        self.blackscene_display.display(screen)
        self.__handle_event(GI.GE.GAME_RELOAD)

    def __reloading_display(self, screen: Surface) -> None:
        if (ratio := self.transform_timer.read() / Constant.RESTART_SCENE_SECOND) >= 1:
            self.__handle_event(GI.GE.GAME_RELOADED)
            return
        self.restart_scene_radius = Constant.DEFAULT_SCREEN_DIAGONAL ** ratio
        draw.circle(
            self.blackscene_display.surface, 
            Color.Game.RESTART_COLORKEY, 
            (Vector(GeneralConstant.DEFAULT_SCREEN_SIZE) // 2).inttuple, 
            self.restart_scene_radius
        )
        self.blackscene_display.display(screen)


class OptionInterface(Interface):
    class OptionEvent(Enum):
        EMPTY = auto()
        SELECTION_UP = auto()
        SELECTION_DOWN = auto()
        CURSOR_ON_EMPTY = auto()
        CURSOR_ON_LANGUAGE = auto()
        CURSOR_ON_FPS = auto()
        CURSOR_ON_BGM = auto()
        CURSOR_ON_SE = auto()
        CURSOR_ON_BACK = auto()
        CLICK_ON_LANGUAGE = auto()
        CLICK_ON_FPS = auto()
        CLICK_ON_BGM = auto()
        CLICK_ON_SE = auto()
        CLICK_ON_BACK = auto()
        CLICK_ON_LANGUAGE_LEFT_ARROW = auto()
        CLICK_ON_LANGUAGE_RIGHT_ARROW = auto()
        CLICK_ON_FPS_LEFT_ARROW = auto()
        CLICK_ON_FPS_RIGHT_ARROW = auto()
        CLICKRELEASE_ON_LANGUAGE = auto()
        CLICKRELEASE_ON_FPS = auto()
        CLICKRELEASE_ON_BGM = auto()
        CLICKRELEASE_ON_SE = auto()
        CLICKRELEASE_ON_BACK = auto()
        CLICKRELEASE_ON_LANGUAGE_LEFT_ARROW = auto()
        CLICKRELEASE_ON_LANGUAGE_RIGHT_ARROW = auto()
        CLICKRELEASE_ON_FPS_LEFT_ARROW = auto()
        CLICKRELEASE_ON_FPS_RIGHT_ARROW = auto()
        CLICKRELEASE = auto()
        LEFT_SWITCH_LANGUAGE = auto()
        RIGHT_SWITCH_LANGUAGE = auto()
        LEFT_SWITCH_FPS = auto()
        RIGHT_SWITCH_FPS = auto()
        START_MOUSE_VOLUME_CHANGE = auto()
        STOP_MOUSE_VOLUME_CHANGE = auto()
        START_KEY_UP_VOLUME = auto()
        START_KEY_DOWN_VOLUME = auto()
        STOP_KEY_VOLUME_CHANGE = auto()
        UNIT_VOLUME_UP = auto()
        UNIT_VOLUME_DOWN = auto()
        CHANGE_BGM = auto()
        CHANGE_SE = auto()
        BACK = auto()

    class OptionStatus(Flag):
        EMPTY = 0
        CURSOR_ON_LANGUAGE = auto()
        CURSOR_ON_FPS = auto()
        CURSOR_ON_BGM = auto()
        CURSOR_ON_SE = auto()
        CURSOR_ON_BACK = auto()
        CURSOR_ON = \
            CURSOR_ON_LANGUAGE | CURSOR_ON_FPS | CURSOR_ON_BGM | CURSOR_ON_SE | CURSOR_ON_BACK
        PRESSING_LANGUAGE = auto()
        PRESSING_FPS = auto()
        PRESSING_BGM = auto()
        PRESSING_SE = auto()
        PRESSING_BACK = auto()
        PRESSING_LANGUAGE_LEFT_ARROW = auto()
        PRESSING_LANGUAGE_RIGHT_ARROW = auto()
        PRESSING_FPS_LEFT_ARROW = auto()
        PRESSING_FPS_RIGHT_ARROW = auto()
        PRESSING = (
            PRESSING_LANGUAGE | PRESSING_FPS | PRESSING_BGM | PRESSING_SE | PRESSING_BACK
            | PRESSING_LANGUAGE_LEFT_ARROW | PRESSING_LANGUAGE_RIGHT_ARROW
            | PRESSING_FPS_LEFT_ARROW | PRESSING_FPS_RIGHT_ARROW
        )
        MOUSE_VOLUME_CHANGE = auto()
        KEY_VOLUME_UP = auto()
        KEY_VOLUME_DOWN = auto()
        KEY_VOLUME_CHANGE = KEY_VOLUME_UP | KEY_VOLUME_DOWN
    
    class PageSelection(IntEnum):
        LANGUAGE = auto()
        FPS = auto()
        BGM = auto()
        SE = auto()
        BACK = auto()
        def __lshift__(self, one: Literal[1]) -> "OptionInterface.PageSelection":
            if self == 1:
                return self
            return OI.PS(self - 1)
        def __rshift__(self, one: Literal[1]) -> "OptionInterface.PageSelection":
            if self == len(OI.PS):
                return self
            return OI.PS(self + 1)

    OE = OptionEvent
    OS = OptionStatus
    PS = PageSelection

    def __init__(self) -> None:
        self.settings = Setting.load()
        self.requests: deque[OptionRequest] = deque()
        self.status = OI.OS.EMPTY
        self.selection = OI.PS.LANGUAGE
        self.volume_value = 0
        self.last_mouse_pos = (0, 0)
        self.volume_ticker = Ticker(
            Constant.OPTION_VOLUME_TICKER_TICK, 
            starting_cooldown=Constant.OPTION_VOLUME_TICKER_STARTCOOLDOWN
        )
        self.title_display = DisplayableTranslatable(
            Vector(Constant.OPTION_TITLE_POS), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            ), 
            Font.Option.TITLE, 
            TranslateName.option_title, 
            self.settings.language, 
            Color.Option.TITLE
        )
        def shadowed(text: DisplayableTranslatable) -> DisplayableTranslatable:
            return DisplayableTranslatable(
                text.offset + Constant.OPTION_SHADOW_OFFSET, 
                text.alignment, 
                text.font, 
                text.translation, 
                text.language, 
                Color.Option.TEXT_SHADOW
            )
        selections = len(OI.PS) - 1
        self.language_text = DisplayableTranslatable(
            Vector(
                Constant.OPTION_TEXT_XPOS, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.LANGUAGE - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            ), 
            Font.Option.TEXT, 
            TranslateName.option_language, 
            self.settings.language, 
            Color.Option.TEXT
        )
        self.shadowed_language_text = shadowed(self.language_text)
        self.FPS_text = DisplayableTranslatable(
            Vector(
                Constant.OPTION_TEXT_XPOS, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.FPS - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            ), 
            Font.Option.TEXT, 
            TranslateName.option_fps, 
            self.settings.language, 
            Color.Option.TEXT
        )
        self.shadowed_FPS_text = shadowed(self.FPS_text)
        self.BGM_volume_text = DisplayableTranslatable(
            Vector(
                Constant.OPTION_TEXT_XPOS, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.BGM - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            ), 
            Font.Option.TEXT, 
            TranslateName.option_bgm, 
            self.settings.language, 
            Color.Option.TEXT
        )
        self.shadowed_BGM_volume_text = shadowed(self.BGM_volume_text)
        self.SE_volume_text = DisplayableTranslatable(
            Vector(
                Constant.OPTION_TEXT_XPOS, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.SE - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            ), 
            Font.Option.TEXT, 
            TranslateName.option_se, 
            self.settings.language, 
            Color.Option.TEXT
        )
        self.shadowed_SE_volume_text = shadowed(self.SE_volume_text)
        self.back_text = DisplayableTranslatable(
            Vector(
                Constant.OPTION_TEXT_XPOS, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.BACK - (selections + 1) / 2 + Constant.OPTION_BACK_EXTRA_SEP) 
                    * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            ), 
            Font.Option.BACKTEXT, 
            TranslateName.option_back, 
            self.settings.language, 
            Color.Option.TEXT
        )
        self.shadowed_back_text = shadowed(self.back_text)
        self.arrow_display = Displayable(
            Texture.SELECTION_MENU_ARROW, 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.language_bar = StaticDisplayable(
            Texture.OPTION_SELECTION_BAR, 
            Vector(
                Constant.OPTION_BARS_XPOS, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.LANGUAGE - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.language_bar_left_arrow = StaticDisplayable(
            Texture.OPTION_SELECTION_LEFT_ARROW, 
            Vector(
                Constant.OPTION_BARS_XPOS - Texture.OPTION_SELECTION_BAR.get_size()[0] // 2, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.LANGUAGE - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.language_bar_right_arrow = StaticDisplayable(
            Texture.OPTION_SELECTION_RIGHT_ARROW, 
            Vector(
                Constant.OPTION_BARS_XPOS + Texture.OPTION_SELECTION_BAR.get_size()[0] // 2, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.LANGUAGE - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.RIGHT, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.language_bar_left_arrow_pressed = StaticDisplayable(
            Texture.OPTION_SELECTION_LEFT_ARROW_PRESSED, 
            Vector(
                Constant.OPTION_BARS_XPOS - Texture.OPTION_SELECTION_BAR.get_size()[0] // 2, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.LANGUAGE - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.language_bar_right_arrow_pressed = StaticDisplayable(
            Texture.OPTION_SELECTION_RIGHT_ARROW_PRESSED, 
            Vector(
                Constant.OPTION_BARS_XPOS + Texture.OPTION_SELECTION_BAR.get_size()[0] // 2, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.LANGUAGE - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.RIGHT, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.language_bar_text = DisplayableTranslatable(
            Vector(
                Constant.OPTION_BARS_XPOS, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.LANGUAGE - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            ), 
            Font.Option.BARTEXT, 
            TranslateName.name, 
            self.settings.language, 
            Color.Option.BARTEXT
        )
        self.FPS_bar = StaticDisplayable(
            Texture.OPTION_SELECTION_BAR, 
            Vector(
                Constant.OPTION_BARS_XPOS, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.FPS - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.FPS_bar_left_arrow = StaticDisplayable(
            Texture.OPTION_SELECTION_LEFT_ARROW, 
            Vector(
                Constant.OPTION_BARS_XPOS - Texture.OPTION_SELECTION_BAR.get_size()[0] // 2, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.FPS - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.FPS_bar_right_arrow = StaticDisplayable(
            Texture.OPTION_SELECTION_RIGHT_ARROW, 
            Vector(
                Constant.OPTION_BARS_XPOS + Texture.OPTION_SELECTION_BAR.get_size()[0] // 2, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.FPS - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.RIGHT, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.FPS_bar_left_arrow_pressed = StaticDisplayable(
            Texture.OPTION_SELECTION_LEFT_ARROW_PRESSED, 
            Vector(
                Constant.OPTION_BARS_XPOS - Texture.OPTION_SELECTION_BAR.get_size()[0] // 2, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.FPS - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.FPS_bar_right_arrow_pressed = StaticDisplayable(
            Texture.OPTION_SELECTION_RIGHT_ARROW_PRESSED, 
            Vector(
                Constant.OPTION_BARS_XPOS + Texture.OPTION_SELECTION_BAR.get_size()[0] // 2, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.FPS - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.RIGHT, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.FPS_bar_text = DisplayableText(
            Vector(
                Constant.OPTION_BARS_XPOS, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.FPS - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            ), 
            Font.Option.BARTEXT, 
            str(self.settings.FPS), 
            Color.Option.BARTEXT
        )
        self.BGM_bar = StaticDisplayable(
            Texture.OPTION_VOLUME_BAR, 
            Vector(
                Constant.OPTION_BARS_XPOS, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.BGM - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.SE_bar = StaticDisplayable(
            Texture.OPTION_VOLUME_BAR, 
            Vector(
                Constant.OPTION_BARS_XPOS, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.SE - (selections + 1) / 2) * Constant.OPTION_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.Volume_button = DisplayableBall(
            Texture.OPTION_VOLUME_POINT_FRAME, 
            Texture.OPTION_VOLUME_POINT_SURFACE, 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=Constant.SCREEN_OFFSET
            )
        )
        self.volume_button_offset = Vector.zero
    
    def __tick(self) -> None:
        while self.volume_ticker.tick():
            if OI.OS.KEY_VOLUME_UP in self.status:
                self.__handle_event(OI.OE.UNIT_VOLUME_UP)
            elif OI.OS.KEY_VOLUME_DOWN in self.status:
                self.__handle_event(OI.OE.UNIT_VOLUME_DOWN)

    def display(self, main_screen: Surface, center_screen: Surface) -> None:
        self.__tick()
        Interface.BACKGROUND.display(main_screen)
        Interface.BACKGROUND.display(center_screen)
        self.title_display.display(center_screen, self.settings.language)
        self.__text_display(center_screen)
        self.__bar_display(center_screen)
        if self.selection == OI.PS.BACK:
            self.arrow_display.display(
                center_screen, 
                Vector(
                    Constant.OPTION_ARROW_XPOS, 
                    Constant.OPTION_YCENTER 
                        + (OI.PS.BACK - len(OI.PS) / 2 + Constant.OPTION_BACK_EXTRA_SEP) 
                        * Constant.OPTION_SEP, 
                )
            )
        else:
            self.arrow_display.display(
                center_screen, 
                Vector(
                    Constant.OPTION_ARROW_XPOS, 
                    Constant.OPTION_YCENTER 
                        + Constant.OPTION_SEP * (self.selection - (len(GI.PS) + 1) / 2) 
                )
            )
    
    def add_event(self, event: Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self.last_mouse_pos = event.pos
        return self.__handle_event(self.__event_converter(event))

    def get_request(self) -> Iterable[Request]:
        while self.requests:
            yield self.requests.popleft()

    def __handle_event(self, event: OptionEvent) -> None:
        match event:
            case OI.OE.SELECTION_UP:
                self.__select_to(self.selection << 1)
            case OI.OE.SELECTION_DOWN:
                self.__select_to(self.selection >> 1)
            case OI.OE.CURSOR_ON_EMPTY:
                self.language_text.color = Color.Option.TEXT
                self.FPS_text.color = Color.Option.TEXT
                self.BGM_volume_text.color = Color.Option.TEXT
                self.SE_volume_text.color = Color.Option.TEXT
                self.back_text.color = Color.Option.TEXT
                self.status &= ~OI.OS.CURSOR_ON
            case OI.OE.CURSOR_ON_LANGUAGE:
                self.language_text.color = Color.Option.TEXT_SELECTING
                self.FPS_text.color = Color.Option.TEXT
                self.BGM_volume_text.color = Color.Option.TEXT
                self.SE_volume_text.color = Color.Option.TEXT
                self.back_text.color = Color.Option.TEXT
                self.status &= ~OI.OS.CURSOR_ON | OI.OS.CURSOR_ON_LANGUAGE
            case OI.OE.CURSOR_ON_FPS:
                self.language_text.color = Color.Option.TEXT
                self.FPS_text.color = Color.Option.TEXT_SELECTING
                self.BGM_volume_text.color = Color.Option.TEXT
                self.SE_volume_text.color = Color.Option.TEXT
                self.back_text.color = Color.Option.TEXT
                self.status &= ~OI.OS.CURSOR_ON | OI.OS.CURSOR_ON_FPS
            case OI.OE.CURSOR_ON_BGM:
                self.language_text.color = Color.Option.TEXT
                self.FPS_text.color = Color.Option.TEXT
                self.BGM_volume_text.color = Color.Option.TEXT_SELECTING
                self.SE_volume_text.color = Color.Option.TEXT
                self.back_text.color = Color.Option.TEXT
                self.status &= ~OI.OS.CURSOR_ON | OI.OS.CURSOR_ON_BGM
            case OI.OE.CURSOR_ON_SE:
                self.language_text.color = Color.Option.TEXT
                self.FPS_text.color = Color.Option.TEXT
                self.BGM_volume_text.color = Color.Option.TEXT
                self.SE_volume_text.color = Color.Option.TEXT_SELECTING
                self.back_text.color = Color.Option.TEXT
                self.status &= ~OI.OS.CURSOR_ON | OI.OS.CURSOR_ON_SE
            case OI.OE.CURSOR_ON_BACK:
                self.language_text.color = Color.Option.TEXT
                self.FPS_text.color = Color.Option.TEXT
                self.BGM_volume_text.color = Color.Option.TEXT
                self.SE_volume_text.color = Color.Option.TEXT
                self.back_text.color = Color.Option.TEXT_SELECTING
                self.status &= ~OI.OS.CURSOR_ON | OI.OS.CURSOR_ON_BACK
            case OI.OE.CLICK_ON_LANGUAGE:
                self.__handle_event(OI.OE.CURSOR_ON_EMPTY)
                self.status |= OI.OS.PRESSING_LANGUAGE
            case OI.OE.CLICK_ON_FPS:
                self.__handle_event(OI.OE.CURSOR_ON_EMPTY)
                self.status |= OI.OS.PRESSING_FPS
            case OI.OE.CLICK_ON_BGM:
                self.__handle_event(OI.OE.CURSOR_ON_EMPTY)
                self.status |= OI.OS.PRESSING_BGM
            case OI.OE.CLICK_ON_SE:
                self.__handle_event(OI.OE.CURSOR_ON_EMPTY)
                self.status |= OI.OS.PRESSING_SE
            case OI.OE.CLICK_ON_BACK:
                self.__handle_event(OI.OE.CURSOR_ON_EMPTY)
                self.status |= OI.OS.PRESSING_BACK
            case OI.OE.CLICK_ON_LANGUAGE_LEFT_ARROW if (
                self.selection == OI.PS.LANGUAGE and self.settings.language != 1
            ):
                self.status |= OI.OS.PRESSING_LANGUAGE_LEFT_ARROW
            case OI.OE.CLICK_ON_LANGUAGE_RIGHT_ARROW if (
                self.selection == OI.PS.LANGUAGE and self.settings.language != len(Language)
            ):
                self.status |= OI.OS.PRESSING_LANGUAGE_RIGHT_ARROW
            case OI.OE.CLICK_ON_FPS_LEFT_ARROW if (
                self.selection == OI.PS.FPS and not self.settings.isFPSmin
            ):
                self.status |= OI.OS.PRESSING_FPS_LEFT_ARROW
            case OI.OE.CLICK_ON_FPS_RIGHT_ARROW if (
                self.selection == OI.PS.FPS and not self.settings.isFPSmax
            ):
                self.status |= OI.OS.PRESSING_FPS_RIGHT_ARROW
            case OI.OE.CLICKRELEASE_ON_LANGUAGE:
                if OI.OS.PRESSING_LANGUAGE in self.status:
                    self.__select_to(OI.PS.LANGUAGE)
                self.status &= ~OI.OS.PRESSING
            case OI.OE.CLICKRELEASE_ON_FPS:
                if OI.OS.PRESSING_FPS in self.status:
                    self.__select_to(OI.PS.FPS)
                self.status &= ~OI.OS.PRESSING
            case OI.OE.CLICKRELEASE_ON_BGM:
                if OI.OS.PRESSING_BGM in self.status:
                    self.__select_to(OI.PS.BGM)
                self.status &= ~OI.OS.PRESSING
            case OI.OE.CLICKRELEASE_ON_SE:
                if OI.OS.PRESSING_SE in self.status:
                    self.__select_to(OI.PS.SE)
                self.status &= ~OI.OS.PRESSING
            case OI.OE.CLICKRELEASE_ON_BACK:
                if OI.OS.PRESSING_BACK in self.status:
                    self.__handle_event(OI.OE.BACK)
                self.status &= ~OI.OS.PRESSING
            case OI.OE.CLICKRELEASE_ON_LANGUAGE_LEFT_ARROW:
                if OI.OS.PRESSING_LANGUAGE_LEFT_ARROW in self.status:
                    self.__handle_event(OI.OE.LEFT_SWITCH_LANGUAGE)
                self.status &= ~OI.OS.PRESSING
            case OI.OE.CLICKRELEASE_ON_LANGUAGE_RIGHT_ARROW:
                if OI.OS.PRESSING_LANGUAGE_RIGHT_ARROW in self.status:
                    self.__handle_event(OI.OE.RIGHT_SWITCH_LANGUAGE)
                self.status &= ~OI.OS.PRESSING
            case OI.OE.CLICKRELEASE_ON_FPS_LEFT_ARROW:
                if OI.OS.PRESSING_FPS_LEFT_ARROW in self.status:
                    self.__handle_event(OI.OE.LEFT_SWITCH_FPS)
                self.status &= ~OI.OS.PRESSING
            case OI.OE.CLICKRELEASE_ON_FPS_RIGHT_ARROW:
                if OI.OS.PRESSING_FPS_RIGHT_ARROW in self.status:
                    self.__handle_event(OI.OE.RIGHT_SWITCH_FPS)
                self.status &= ~OI.OS.PRESSING
            case OI.OE.CLICKRELEASE:
                self.status &= ~OI.OS.PRESSING
            case OI.OE.LEFT_SWITCH_LANGUAGE:
                self.settings.lshift_language()
                self.__text_language_update()
                self.add_event(Event(pygame.MOUSEMOTION, pos=self.last_mouse_pos))
                self.requests.append(OptionRequest.CHANGE_LANGUAGE)
            case OI.OE.RIGHT_SWITCH_LANGUAGE:
                self.settings.rshift_language()
                self.__text_language_update()
                self.add_event(Event(pygame.MOUSEMOTION, pos=self.last_mouse_pos))
                self.requests.append(OptionRequest.CHANGE_LANGUAGE)
            case OI.OE.LEFT_SWITCH_FPS:
                self.settings.lshift_FPS()
                self.FPS_bar_text.text = str(self.settings.FPS)
                self.requests.append(OptionRequest.CHANGE_FPS)
            case OI.OE.RIGHT_SWITCH_FPS:
                self.settings.rshift_FPS()
                self.FPS_bar_text.text = str(self.settings.FPS)
                self.requests.append(OptionRequest.CHANGE_FPS)
            case OI.OE.START_MOUSE_VOLUME_CHANGE:
                self.status |= OI.OS.MOUSE_VOLUME_CHANGE
            case OI.OE.STOP_MOUSE_VOLUME_CHANGE:
                self.status &= ~OI.OS.MOUSE_VOLUME_CHANGE
            case OI.OE.START_KEY_UP_VOLUME:
                self.status &= ~OI.OS.KEY_VOLUME_DOWN
                self.status |= OI.OS.KEY_VOLUME_UP
                self.volume_ticker.restart()
                self.__handle_event(OI.OE.UNIT_VOLUME_UP)
            case OI.OE.START_KEY_DOWN_VOLUME:
                self.status &= ~OI.OS.KEY_VOLUME_UP
                self.status |= OI.OS.KEY_VOLUME_DOWN
                self.volume_ticker.restart()
                self.__handle_event(OI.OE.UNIT_VOLUME_DOWN)
            case OI.OE.STOP_KEY_VOLUME_CHANGE:
                self.status &= ~OI.OS.KEY_VOLUME_CHANGE
            case OI.OE.UNIT_VOLUME_UP:
                if self.volume_value < 100:
                    self.volume_value += 1
                    if self.selection == OI.PS.BGM:
                        self.__handle_event(OI.OE.CHANGE_BGM)
                    elif self.selection == OI.PS.SE:
                        self.__handle_event(OI.OE.CHANGE_SE)
                    self.volume_button_offset = self.__volume_button_offset()
            case OI.OE.UNIT_VOLUME_DOWN:
                if self.volume_value > 0:
                    self.volume_value -= 1
                    if self.selection == OI.PS.BGM:
                        self.__handle_event(OI.OE.CHANGE_BGM)
                    elif self.selection == OI.PS.SE:
                        self.__handle_event(OI.OE.CHANGE_SE)
                    self.volume_button_offset = self.__volume_button_offset()
            case OI.OE.CHANGE_BGM:
                self.settings.set_BGM_volume(self.volume_value)
            case OI.OE.CHANGE_SE:
                self.settings.set_SE_volume(self.volume_value)
            case OI.OE.BACK:
                self.status = OI.OS.EMPTY
                self.selection = OI.PS.LANGUAGE
                self.last_mouse_pos = (0, 0)
                self.settings.save()
                self.requests.append(OptionRequest.BACK)

    def __event_converter(self, event: Event) -> OptionEvent:
        match event.type:
            case pygame.KEYDOWN:
                match event.key:
                    case pygame.K_LEFT:
                        match self.selection:
                            case OI.PS.LANGUAGE:
                                return OI.OE.LEFT_SWITCH_LANGUAGE
                            case OI.PS.FPS:
                                return OI.OE.LEFT_SWITCH_FPS
                            case OI.PS.BGM | OI.PS.SE:
                                return OI.OE.START_KEY_DOWN_VOLUME
                    case pygame.K_RIGHT:
                        match self.selection:
                            case OI.PS.LANGUAGE:
                                return OI.OE.RIGHT_SWITCH_LANGUAGE
                            case OI.PS.FPS:
                                return OI.OE.RIGHT_SWITCH_FPS
                            case OI.PS.BGM | OI.PS.SE:
                                return OI.OE.START_KEY_UP_VOLUME
                    case pygame.K_UP:
                        return OI.OE.SELECTION_UP
                    case pygame.K_DOWN:
                        return OI.OE.SELECTION_DOWN
                    case pygame.K_RETURN if self.selection == OI.PS.BACK:
                        return OI.OE.BACK
                    case pygame.K_ESCAPE:
                        return OI.OE.BACK
            case pygame.KEYUP:
                match event.key:
                    case pygame.K_LEFT if OI.OS.KEY_VOLUME_DOWN in self.status:
                        return OI.OE.STOP_KEY_VOLUME_CHANGE
                    case pygame.K_RIGHT if OI.OS.KEY_VOLUME_UP in self.status:
                        return OI.OE.STOP_KEY_VOLUME_CHANGE
            case pygame.MOUSEBUTTONDOWN if event.button == pygame.BUTTON_LEFT:
                pos = Vector(event.pos)
                if (
                    self.selection == OI.PS.LANGUAGE 
                    and self.language_bar_left_arrow.contains(MAIN_SCREEN, pos)
                ):
                    return OI.OE.CLICK_ON_LANGUAGE_LEFT_ARROW
                if (
                    self.selection == OI.PS.LANGUAGE 
                    and self.language_bar_right_arrow.contains(MAIN_SCREEN, pos)
                ):
                    return OI.OE.CLICK_ON_LANGUAGE_RIGHT_ARROW
                if (
                    self.selection == OI.PS.FPS 
                    and self.FPS_bar_left_arrow.contains(MAIN_SCREEN, pos)
                ):
                    return OI.OE.CLICK_ON_FPS_LEFT_ARROW
                if (
                    self.selection == OI.PS.FPS 
                    and self.FPS_bar_right_arrow.contains(MAIN_SCREEN, pos)
                ):
                    return OI.OE.CLICK_ON_FPS_RIGHT_ARROW
                if (
                    (self.selection == OI.PS.BGM or self.selection == OI.PS.SE)
                    and self.Volume_button.contains(
                        MAIN_SCREEN, 
                        self.volume_button_offset, 
                        pos
                    )
                ):
                    return OI.OE.START_MOUSE_VOLUME_CHANGE
                if (
                    self.language_text.contains(MAIN_SCREEN, pos) 
                    and not self.selection == OI.PS.LANGUAGE
                ):
                    return OI.OE.CLICK_ON_LANGUAGE
                if (
                    self.FPS_text.contains(MAIN_SCREEN, pos)
                    and not self.selection == OI.PS.FPS
                ):
                    return OI.OE.CLICK_ON_FPS
                if (
                    self.BGM_volume_text.contains(MAIN_SCREEN, pos)
                    and not self.selection == OI.PS.BGM
                ):
                    return OI.OE.CLICK_ON_BGM
                if (
                    self.SE_volume_text.contains(MAIN_SCREEN, pos)
                    and not self.selection == OI.PS.SE
                ):
                    return OI.OE.CLICK_ON_SE
                if self.back_text.contains(MAIN_SCREEN, pos):
                    return OI.OE.CLICK_ON_BACK
            case pygame.MOUSEBUTTONUP if event.button == pygame.BUTTON_LEFT:
                if OI.OS.MOUSE_VOLUME_CHANGE in self.status:
                    return OI.OE.STOP_MOUSE_VOLUME_CHANGE
                pos = Vector(event.pos)
                if self.language_bar_left_arrow.contains(MAIN_SCREEN, pos):
                    return OI.OE.CLICKRELEASE_ON_LANGUAGE_LEFT_ARROW
                if self.language_bar_right_arrow.contains(MAIN_SCREEN, pos):
                    return OI.OE.CLICKRELEASE_ON_LANGUAGE_RIGHT_ARROW
                if self.FPS_bar_left_arrow.contains(MAIN_SCREEN, pos):
                    return OI.OE.CLICKRELEASE_ON_FPS_LEFT_ARROW
                if self.FPS_bar_right_arrow.contains(MAIN_SCREEN, pos):
                    return OI.OE.CLICKRELEASE_ON_FPS_RIGHT_ARROW
                if self.language_text.contains(MAIN_SCREEN, pos):
                    return OI.OE.CLICKRELEASE_ON_LANGUAGE
                if self.FPS_text.contains(MAIN_SCREEN, pos):
                    return OI.OE.CLICKRELEASE_ON_FPS
                if self.BGM_volume_text.contains(MAIN_SCREEN, pos):
                    return OI.OE.CLICKRELEASE_ON_BGM
                if self.SE_volume_text.contains(MAIN_SCREEN, pos):
                    return OI.OE.CLICKRELEASE_ON_SE
                if self.back_text.contains(MAIN_SCREEN, pos):
                    return OI.OE.CLICKRELEASE_ON_BACK
                return OI.OE.CLICKRELEASE
            case pygame.MOUSEMOTION if self.status & OI.OS.MOUSE_VOLUME_CHANGE:
                position_x = event.pos[0] - MAIN_SCREEN.get_size()[0] // 2 \
                    - Constant.SCREEN_OFFSET.x
                barsize = Texture.OPTION_VOLUME_BAR.get_size()[0]
                x_range = (
                    Constant.OPTION_BARS_XPOS - barsize / 2, 
                    Constant.OPTION_BARS_XPOS + barsize / 2
                )
                if position_x < x_range[0]:
                    self.volume_value = 0
                    self.volume_button_offset.x = x_range[0]
                elif position_x > x_range[1]:
                    self.volume_value = 100
                    self.volume_button_offset.x = x_range[1]
                else:
                    self.volume_value = int(
                        100 * (position_x - x_range[0]) / (x_range[1] - x_range[0])
                    )
                    self.volume_button_offset.x = position_x
                if self.selection == OI.PS.BGM:
                    return OI.OE.CHANGE_BGM
                elif self.selection == OI.PS.SE:
                    return OI.OE.CHANGE_SE
            case pygame.MOUSEMOTION if not self.status & OI.OS.PRESSING:
                position = Vector(event.pos)
                if (
                    self.language_text.contains(MAIN_SCREEN, position) 
                    and self.selection != OI.PS.LANGUAGE
                ):
                    return OI.OE.CURSOR_ON_LANGUAGE
                elif (
                    self.FPS_text.contains(MAIN_SCREEN, position)
                    and self.selection != OI.PS.FPS
                ):
                    return OI.OE.CURSOR_ON_FPS
                elif (
                    self.BGM_volume_text.contains(MAIN_SCREEN, position)
                    and self.selection != OI.PS.BGM
                ):
                    return OI.OE.CURSOR_ON_BGM
                elif (
                    self.SE_volume_text.contains(MAIN_SCREEN, position)
                    and self.selection != OI.PS.SE
                ):
                    return OI.OE.CURSOR_ON_SE
                elif self.back_text.contains(MAIN_SCREEN, position):
                    return OI.OE.CURSOR_ON_BACK
                else:
                    return OI.OE.CURSOR_ON_EMPTY
        return OI.OE.EMPTY

    def __text_display(self, screen: Surface) -> None:        
        if OI.OS.PRESSING_LANGUAGE in self.status:
            self.shadowed_language_text.display(screen, self.settings.language)
            self.language_text.language = self.settings.language
        else:
            self.language_text.display(screen, self.settings.language)
            self.shadowed_language_text.language = self.settings.language
        
        if OI.OS.PRESSING_FPS in self.status:
            self.shadowed_FPS_text.display(screen, self.settings.language)
            self.FPS_text.language = self.settings.language
        else:
            self.FPS_text.display(screen, self.settings.language)
            self.shadowed_FPS_text.language = self.settings.language
        
        if OI.OS.PRESSING_BGM in self.status:
            self.shadowed_BGM_volume_text.display(screen, self.settings.language)
            self.BGM_volume_text.language = self.settings.language
        else:
            self.BGM_volume_text.display(screen, self.settings.language)
            self.shadowed_BGM_volume_text.language = self.settings.language
        
        if OI.OS.PRESSING_SE in self.status:
            self.shadowed_SE_volume_text.display(screen, self.settings.language)
            self.SE_volume_text.language = self.settings.language
        else:
            self.SE_volume_text.display(screen, self.settings.language)
            self.shadowed_SE_volume_text.language = self.settings.language

        if OI.OS.PRESSING_BACK in self.status:
            self.shadowed_back_text.display(screen, self.settings.language)
            self.back_text.language = self.settings.language
        else:
            self.back_text.display(screen, self.settings.language)
            self.shadowed_back_text.language = self.settings.language

    def __bar_display(self, screen: Surface) -> None:
        match self.selection:
            case OI.PS.LANGUAGE:
                self.language_bar.display(screen)
                self.language_bar_text.display(screen, self.settings.language)
                if not self.settings.language == 1:
                    if OI.OS.PRESSING_LANGUAGE_LEFT_ARROW in self.status:
                        self.language_bar_left_arrow_pressed.display(screen)
                    else:
                        self.language_bar_left_arrow.display(screen)
                if not self.settings.language == len(Language):
                    if OI.OS.PRESSING_LANGUAGE_RIGHT_ARROW in self.status:
                        self.language_bar_right_arrow_pressed.display(screen)
                    else:
                        self.language_bar_right_arrow.display(screen)
            case OI.PS.FPS:
                self.FPS_bar.display(screen)
                self.FPS_bar_text.display(screen)
                if not self.settings.isFPSmin:
                    if OI.OS.PRESSING_FPS_LEFT_ARROW in self.status:
                        self.FPS_bar_left_arrow_pressed.display(screen)
                    else:
                        self.FPS_bar_left_arrow.display(screen)
                if not self.settings.isFPSmax:
                    if OI.OS.PRESSING_FPS_RIGHT_ARROW in self.status:
                        self.FPS_bar_right_arrow_pressed.display(screen)
                    else:
                        self.FPS_bar_right_arrow.display(screen)
            case OI.PS.BGM:
                self.BGM_bar.display(screen)
                self.Volume_button.display(
                    screen, 
                    self.volume_button_offset, 
                    self.volume_button_angle
                )
            case OI.PS.SE:
                self.SE_bar.display(screen)
                self.Volume_button.display(
                    screen, 
                    self.volume_button_offset, 
                    self.volume_button_angle
                )

    def __select_to(self, selection: PageSelection) -> None:
        if self.selection == selection:
            return
        self.selection = selection
        if selection == OI.PS.BGM:
            self.volume_value = self.settings.BGM_Volume
            self.volume_button_offset = self.__volume_button_offset()
        elif selection == OI.PS.SE:
            self.volume_value = self.settings.SE_Volume
            self.volume_button_offset = self.__volume_button_offset()
        self.__handle_event(OI.OE.STOP_KEY_VOLUME_CHANGE)
        self.__handle_event(OI.OE.STOP_MOUSE_VOLUME_CHANGE)
        self.__handle_event(OI.OE.CLICKRELEASE)
        self.add_event(Event(pygame.MOUSEMOTION, pos=self.last_mouse_pos))

    def __text_language_update(self) -> None:
        language = self.settings.language
        self.title_display.language = language
        self.language_text.language = language
        self.FPS_text.language = language
        self.BGM_volume_text.language = language
        self.SE_volume_text.language = language
        self.back_text.language = language
        self.shadowed_language_text.language = language
        self.shadowed_FPS_text.language = language
        self.shadowed_BGM_volume_text.language = language
        self.shadowed_SE_volume_text.language = language
        self.shadowed_back_text.language = language

    def __volume_button_offset(self) -> Vector:
        if self.selection == OI.PS.BGM:
            return Vector(
                Constant.OPTION_BARS_XPOS 
                    + Texture.OPTION_VOLUME_BAR.get_size()[0] 
                    * (self.volume_value - 50) / 100, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.BGM - len(OI.PS) / 2) * Constant.OPTION_SEP
            )
        if self.selection == OI.PS.SE:
            return Vector(
                Constant.OPTION_BARS_XPOS 
                    + Texture.OPTION_VOLUME_BAR.get_size()[0] 
                    * (self.volume_value - 50) / 100, 
                Constant.OPTION_YCENTER 
                    + (OI.PS.SE - len(OI.PS) / 2) * Constant.OPTION_SEP
            )
        return Vector.zero
    
    @property
    def volume_button_angle(self) -> NumberType:
        reference = Constant.OPTION_BARS_XPOS + Texture.OPTION_VOLUME_BAR.get_size()[0] / 2
        return _to_degree(
            (self.volume_button_offset.x - reference) / Constant.OPTION_VOLUME_BUTTON_RADIUS
        )


GI = GameInterface
OI = OptionInterface