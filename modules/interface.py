from __future__ import annotations
import pygame
from pygame import Surface
from pygame.event import Event as pygameEvent
from pygame import draw
from .game import Game, get_level, get_height
from .display import (
    Alignment, 
    Displayable, 
    DisplayableBall, 
    DisplayableText, 
    DisplayableTranslatable, 
    StaticDisplayable
)
from .language import Language, TranslateName, Translatable
from .resources import Font, Texture, Color, Path, MAIN_SCREEN, BGM, Sound
from .vector import Vector, NumberType
from .physics import _to_degree
from .data import Achievement, HighScore, Datas
from .setting import Setting
from .utils import LinearRange, Timer, Ticker, Chance, time_string
from .constants import GeneralConstant, InterfaceConstant as Constant
from random import randint
from collections import deque
from enum import Enum, IntEnum, Flag, auto
from abc import ABC, abstractmethod
from typing import Any, NamedTuple, Union, Iterable, Generator, Literal


type Request = Union[GameRequest, OptionRequest, AchievementRequest, ControlRequest]

BASIC_ALIGNMENT = Alignment(
    Alignment.Mode.CENTERED, 
    Alignment.Mode.CENTERED, 
    Alignment.Flag.REFERENCED, 
    offset=GeneralConstant.SCREEN_OFFSET
)

def save():
    Datas.save()

class GameRequest(Enum):
    GOTO_OPTIONS = auto()
    GOTO_ACHIEVEMENT = auto()
    GOTO_CONTROLS = auto()
    RELOAD_ACHIEVEMENT_INTERFACE = auto()
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
    QUIT = auto()


class AchievementRequest(Enum):
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]) -> Any:
        return Enum._generate_next_value_(
            name, 
            len(GameRequest) + len(OptionRequest) + 1, 
            count, 
            last_values
        )
    
    BACK = auto()
    QUIT = auto()


class ControlRequest(Enum):
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: list[Any]) -> Any:
        return Enum._generate_next_value_(
            name, 
            len(GameRequest) + len(OptionRequest) + len(AchievementRequest) + 1, 
            count, 
            last_values
        )
    
    BACK = auto()
    QUIT = auto()


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
    def add_event(self, event: pygameEvent) -> None:
        pass

    @abstractmethod
    def get_request(self) -> Iterable[Request]:
        pass

    @abstractmethod
    def display(self, main_screen: Surface, center_screen: Surface, *args, **kwargs) -> None:
        BGM.loop()


def CURRENT_CURSOR() -> pygameEvent:
    return pygameEvent(pygame.MOUSEMOTION, pos=pygame.mouse.get_pos())


class GameInterface(Interface):
    class Event(Enum):
        EMPTY = auto()
        GAME_SPACE = auto()
        GAME_GAMEOVER = auto()
        GAME_TO_RESTART_SCREEN = auto()
        GAME_RESTART = auto()
        GAME_RELOAD = auto()
        GAME_RELOADED = auto()
        GAME_DEBUG = auto()
        GAME_HIGHSCORE_UPDATE = auto()
        SELECTION_UP = auto()
        SELECTION_DOWN = auto()
        SELECTION_LEFT = auto()
        SELECTION_RIGHT = auto()
        SELECTION_ENTER = auto()
        PAUSE = auto()
        CONTINUE = auto()
        RESTART_CONFIRM = auto()
        CURSOR_ON_EMPTY = auto()
        CURSOR_ON_OPTION = auto()
        CURSOR_ON_ACHIEVEMENT = auto()
        CURSOR_ON_CONTROL = auto()
        CURSOR_ON_QUIT = auto()
        CURSOR_ON_CONTINUE = auto()
        CURSOR_ON_RESTART = auto()
        CURSOR_ON_BUTTON_NO = auto()
        CURSOR_ON_BUTTON_YES = auto()
        CLICK_ON_OPTIONS = auto()
        CLICK_ON_ACHIEVEMENT = auto()
        CLICK_ON_CONTROL = auto()
        CLICK_ON_QUIT = auto()
        CLICK_ON_CONTINUE = auto()
        CLICK_ON_RESTART = auto()
        CLICK_ON_BUTTON_NO = auto()
        CLICK_ON_BUTTON_YES = auto()
        CLICKRELEASE_ON_OPTIONS = auto()
        CLICKRELEASE_ON_ACHIEVEMENT = auto()
        CLICKRELEASE_ON_CONTROLS = auto()
        CLICKRELEASE_ON_QUIT = auto()
        CLICKRELEASE_ON_CONTINUE = auto()
        CLICKRELEASE_ON_RESTART = auto()
        CLICKRELEASE_ON_BUTTON_NO = auto()
        CLICKRELEASE_ON_BUTTON_YES = auto()
        CLICKRELEASE = auto()
        TEST = auto()
        QUIT = auto()

    class Status(Flag):
        EMPTY = 0
        LOADED = auto()
        STARTING = auto()
        STARTED = auto()
        PAUSE = auto()
        PAUSE_CONFIRM = auto()
        GAMEOVER = auto()
        RESTART_SCREEN = auto()
        RESTARTING = auto()
        RELOADING = auto()
        DISPLAY_ACHIEVEMENT = auto()
        PRESSING_OPTIONS = auto()
        PRESSING_ACHIEVEMENT = auto()
        PRESSING_CONTROLS = auto()
        PRESSING_QUIT = auto()
        PRESSING_CONTINUE = auto()
        PRESSING_RESTART = auto()
        PRESSING_BUTTON_NO = auto()
        PRESSING_BUTTON_YES = auto()
        PRESSING = (
            PRESSING_OPTIONS | PRESSING_ACHIEVEMENT | PRESSING_CONTROLS | PRESSING_QUIT
            | PRESSING_CONTINUE | PRESSING_RESTART | PRESSING_BUTTON_NO | PRESSING_BUTTON_YES
        )

    class PageSelection(IntEnum):
        OPTIONS = auto()
        ACHIEVEMENT = auto()
        CONTROLS = auto()
        QUIT = auto()

        def upper(self) -> GameInterface.PageSelection:
            if self == 1:
                return self
            return GIP(self - 1)
        
        def lower(self) -> GameInterface.PageSelection:
            if self == len(GIP):
                return self
            return GIP(self + 1)

    class DebugMsgTimer(NamedTuple):
        msg: str
        ticker: Ticker

    def __init__(self, language: Language) -> None:
        self.game = Game(Path.LEVEL)
        self.language = language
        self.tick_timer = Timer(start=True)
        self.transform_timer = Timer()
        self.status = GIS.LOADED
        self.bounce = False
        self.debugging = False
        self.height = 0
        self.new_record = False
        self.selection = GIP.OPTIONS
        self.requests: deque[GameRequest] = deque()
        self.debug_msgs: deque[GI.DebugMsgTimer] = deque()
        self.logo_display = Displayable(
            Texture.LOGO, 
            BASIC_ALIGNMENT
        )
        self.scoreboard_bg = StaticDisplayable(
            Texture.SCOREBOARD, 
            Constant.Game.SCOREBOARD_DISPLAY_POS, 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.TOP, 
                Alignment.Flag.FILL, 
                Alignment.Flag.REFERENCED, 
                facing=Alignment.Facing.UP, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )
        self.start_display = DisplayableTranslatable(
            Constant.Game.START_DISPLAY_POS, 
            BASIC_ALIGNMENT, 
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
        self.new_record_display = DisplayableTranslatable(
            Vector.zero, 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED
            ), 
            Font.Game.NEW_RECORD_TEXT, 
            TranslateName.game_new_record_text, 
            self.language, 
            Color.Game.NEW_RECORD_TEXT
        )
        def pressed(text: DisplayableTranslatable) -> DisplayableTranslatable:
            return DisplayableTranslatable(
                text.offset + Constant.Game.SELECTION_PRESSED_OFFSET, 
                text.alignment, 
                text.font, 
                text.translation, 
                text.language, 
                Color.Game.SELECTION_MENU_TEXT_PRESSED
            )
        self.selection_displays = (
            DisplayableTranslatable(
                Vector(
                    Constant.Game.SELECTION_MENU_XPOS, 
                    Constant.Game.STARTING_TEXT_CENTER 
                        + Constant.Game.SELECTION_MENU_SEP 
                        * (GIP.OPTIONS - (len(GIP) + 1) / 2) 
                ), 
                Alignment(
                    Alignment.Mode.CENTERED, 
                    Alignment.Mode.LEFT, 
                    Alignment.Flag.REFERENCED, 
                    offset=GeneralConstant.SCREEN_OFFSET
                ), 
                Font.Game.SELECTION_MENU_TEXT, 
                TranslateName.game_selctionmenu_options, 
                self.language, 
                Color.Game.SELECTION_MENU_TEXT
            ), 
            DisplayableTranslatable(
                Vector(
                    Constant.Game.SELECTION_MENU_XPOS, 
                    Constant.Game.STARTING_TEXT_CENTER 
                        + Constant.Game.SELECTION_MENU_SEP 
                        * (GIP.ACHIEVEMENT - (len(GIP) + 1) / 2) 
                ), 
                Alignment(
                    Alignment.Mode.CENTERED, 
                    Alignment.Mode.LEFT, 
                    Alignment.Flag.REFERENCED, 
                    offset=GeneralConstant.SCREEN_OFFSET
                ), 
                Font.Game.SELECTION_MENU_TEXT, 
                TranslateName.game_selctionmenu_achievements, 
                self.language, 
                Color.Game.SELECTION_MENU_TEXT
            ), 
            DisplayableTranslatable(
                Vector(
                    Constant.Game.SELECTION_MENU_XPOS, 
                    Constant.Game.STARTING_TEXT_CENTER 
                        + Constant.Game.SELECTION_MENU_SEP 
                        * (GIP.CONTROLS - (len(GIP) + 1) / 2) 
                ), 
                Alignment(
                    Alignment.Mode.CENTERED, 
                    Alignment.Mode.LEFT, 
                    Alignment.Flag.REFERENCED, 
                    offset=GeneralConstant.SCREEN_OFFSET
                ), 
                Font.Game.SELECTION_MENU_TEXT, 
                TranslateName.game_selctionmenu_controls, 
                self.language, 
                Color.Game.SELECTION_MENU_TEXT
            ), 
            DisplayableTranslatable(
                Vector(
                    Constant.Game.SELECTION_MENU_XPOS, 
                    Constant.Game.STARTING_TEXT_CENTER 
                        + Constant.Game.SELECTION_MENU_SEP 
                        * (GIP.QUIT - (len(GIP) + 1) / 2) 
                ), 
                Alignment(
                    Alignment.Mode.CENTERED, 
                    Alignment.Mode.LEFT, 
                    Alignment.Flag.REFERENCED, 
                    offset=GeneralConstant.SCREEN_OFFSET
                ), 
                Font.Game.SELECTION_MENU_TEXT, 
                TranslateName.game_selctionmenu_quit, 
                self.language, 
                Color.Game.SELECTION_MENU_TEXT
            )
        )
        self.pressed_selection_displays = tuple(
            pressed(display) for display in self.selection_displays
        )
        self.selection_menu_arrow_display = Displayable(
            Texture.SELECTION_MENU_ARROW, 
            BASIC_ALIGNMENT
        )
        self.all_achievement_displays = {
            language: {
                achievement: self.__get_achievement_display(language, achievement)
                for achievement in Achievement if achievement != Achievement._unused
            }
            for language in Language
        }
        self.pause_blackscene = StaticDisplayable(
            Surface(GeneralConstant.DEFAULT_SCREEN_SIZE), 
            Vector.zero, 
            Alignment(Alignment.Mode.DEFAULT, Alignment.Mode.DEFAULT)
        )
        self.pause_blackscene.surface.fill(Color.BLACK)
        self.pause_blackscene.surface.set_alpha(Constant.Game.PAUSE_SCENE_ALPHA)
        self.pause_frame = StaticDisplayable(
            Texture.PAUSE_FRAME, 
            Vector.zero, 
            Alignment(Alignment.Mode.CENTERED, Alignment.Mode.CENTERED)
        )
        self.pause_title = DisplayableTranslatable(
            Constant.Game.PAUSE_TITLE_POS, 
            BASIC_ALIGNMENT, 
            Font.Game.PAUSE_TITLE, 
            TranslateName.game_pause_title, 
            self.language, 
            Color.Game.PAUSE_TEXT
        )
        self.pause_arrow = StaticDisplayable(
            Texture.SELECTION_MENU_ARROW, 
            Vector.zero, 
            BASIC_ALIGNMENT
        )
        self.pause_selection = 0
        self.pause_continue = DisplayableTranslatable(
            Constant.Game.PAUSE_CONTINUE_POS, 
            BASIC_ALIGNMENT, 
            Font.Game.PAUSE_TEXT, 
            TranslateName.game_pause_continue, 
            self.language, 
            Color.Game.PAUSE_TEXT
        )
        self.pause_continue_pressed = DisplayableTranslatable(
            Constant.Game.PAUSE_CONTINUE_POS + Constant.Game.PAUSE_PRESSED_OFFSET, 
            BASIC_ALIGNMENT, 
            Font.Game.PAUSE_TEXT, 
            TranslateName.game_pause_continue, 
            self.language, 
            Color.Game.PAUSE_TEXT_PRESSED
        )
        self.pause_restart = DisplayableTranslatable(
            Constant.Game.PAUSE_RESTART_POS, 
            BASIC_ALIGNMENT, 
            Font.Game.PAUSE_TEXT, 
            TranslateName.game_pause_restart, 
            self.language, 
            Color.Game.PAUSE_TEXT
        )
        self.pause_restart_pressed = DisplayableTranslatable(
            Constant.Game.PAUSE_RESTART_POS + Constant.Game.PAUSE_PRESSED_OFFSET, 
            BASIC_ALIGNMENT, 
            Font.Game.PAUSE_TEXT, 
            TranslateName.game_pause_restart, 
            self.language, 
            Color.Game.PAUSE_TEXT_PRESSED
        )
        self.confirm_selection = 0
        self.pause_confirm_text = DisplayableTranslatable(
            Constant.Game.PAUSE_CONFIRM_TEXT_POS, 
            BASIC_ALIGNMENT, 
            Font.Game.PAUSE_TEXT, 
            TranslateName.game_pause_confirm_text, 
            self.language, 
            Color.Game.PAUSE_TEXT
        )
        self.pause_confirm_no = DisplayableTranslatable(
            Constant.Game.PAUSE_BUTTON_NO_POS, 
            BASIC_ALIGNMENT, 
            Font.Game.PAUSE_TEXT, 
            TranslateName.game_pause_confirm_no, 
            self.language, 
            Color.Game.PAUSE_TEXT
        )
        self.pause_confirm_no_pressed = DisplayableTranslatable(
            Constant.Game.PAUSE_BUTTON_NO_POS + Constant.Game.PAUSE_PRESSED_OFFSET, 
            BASIC_ALIGNMENT, 
            Font.Game.PAUSE_TEXT, 
            TranslateName.game_pause_confirm_no, 
            self.language, 
            Color.Game.PAUSE_TEXT_PRESSED
        )
        self.pause_confirm_yes = DisplayableTranslatable(
            Constant.Game.PAUSE_BUTTON_YES_POS, 
            BASIC_ALIGNMENT, 
            Font.Game.PAUSE_TEXT, 
            TranslateName.game_pause_confirm_yes, 
            self.language, 
            Color.Game.PAUSE_TEXT
        )
        self.pause_confirm_yes_pressed = DisplayableTranslatable(
            Constant.Game.PAUSE_BUTTON_YES_POS + Constant.Game.PAUSE_PRESSED_OFFSET, 
            BASIC_ALIGNMENT, 
            Font.Game.PAUSE_TEXT, 
            TranslateName.game_pause_confirm_yes, 
            self.language, 
            Color.Game.PAUSE_TEXT_PRESSED
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
        self.blackscene_display.surface.set_colorkey(Color.TRANSPARENT_COLORKEY)

    def __tick(self) -> None:
        ticks = int(Constant.Game.INGAME_FPS * self.tick_timer.read())
        self.tick_timer.offset(-ticks * Constant.Game.DT)
        if self.bounce and self.game.ball.entity.bounceable:
            Sound.bounce.play()
        self.game.tick(Constant.Game.DT, self.bounce)
        self.bounce = False
        for _ in range(min(100, ticks - 1)):
            self.game.tick(Constant.Game.DT, False)
        self.height = max(self.height, self.game.ball.entity.position.y)
        if not self.status & (GIS.GAMEOVER | GIS.RESTART_SCREEN) and self.game.gameover:
            self.__handle_event(GIE.GAME_GAMEOVER)
        if (
            GIS.DISPLAY_ACHIEVEMENT not in self.status 
            and (achievement := self.game.read_new_achievement()) is not None
        ):
            self.__add_achievement(achievement)
            self.requests.append(GameRequest.RELOAD_ACHIEVEMENT_INTERFACE)
        self.__read_debug_msg()
        

    def add_event(self, event: pygameEvent) -> None:
        self.__handle_event(self.__event_converter(event))

    def get_request(self) -> Generator[GameRequest, None, None]:
        while self.requests:
            yield self.requests.popleft()

    def __restart(self) -> None:
        self.game.restart()
        self.tick_timer.restart()
        self.height = 0
        self.debug_msgs.clear()
        self.selection = GIP.OPTIONS

    def __revive(self) -> None:
        self.game.revive()
        self.status &= ~(GIS.GAMEOVER | GIS.RESTART_SCREEN)
        self.status |= GIS.STARTED

    def __test(self) -> None:
        pass

    def __handle_event(self, event: Event) -> None:
        match event:
            case GIE.GAME_SPACE if (
                GIS.RESTART_SCREEN in self.status
                and not GIS.RESTARTING in self.status
            ):
                self.__handle_event(GIE.GAME_RESTART)
            case GIE.GAME_SPACE if GIS.STARTED in self.status:
                if not (GIS.PAUSE | GIS.PAUSE_CONFIRM) & self.status:
                    self.bounce = True
            case GIE.GAME_SPACE if (GIS.RELOADING | GIS.LOADED) & self.status:
                self.__handle_event(GIE.CURSOR_ON_EMPTY)
                self.__handle_event(GIE.CLICKRELEASE)
                self.status |= GIS.STARTING | GIS.STARTED
                self.bounce = True
            case GIE.GAME_DEBUG:
                if not (GIS.PAUSE | GIS.PAUSE_CONFIRM) & self.status:
                    self.debugging = not self.debugging
            case GIE.GAME_HIGHSCORE_UPDATE:
                Datas.highscore = HighScore(self.height)
            case GIE.GAME_GAMEOVER:
                self.transform_timer.restart()
                BGM.stop()
                self.status = GIS.GAMEOVER | (self.status & GIS.DISPLAY_ACHIEVEMENT)
            case GIE.GAME_TO_RESTART_SCREEN:
                self.height = int(self.height)
                if self.height > Datas.highscore:
                    self.__handle_event(GIE.GAME_HIGHSCORE_UPDATE)
                    self.new_record = True
                self.transform_timer.restart()
                self.status = GIS.RESTART_SCREEN | (self.status & GIS.DISPLAY_ACHIEVEMENT)
            case GIE.GAME_RESTART:
                BGM.stop()
                self.blackscene_display.surface.fill(Color.BLACK)
                self.blackscene_display.surface = \
                    self.blackscene_display.surface.convert_alpha()
                self.transform_timer.restart()
                self.status |= GIS.RESTARTING
                self.status &= ~(GIS.RELOADING | GIS.PRESSING)
            case GIE.GAME_RELOAD:
                self.__restart()
                self.transform_timer.restart()
                self.blackscene_display.surface.set_colorkey(Color.TRANSPARENT_COLORKEY)
                self.new_record = False
                BGM.play()
                self.status = GIS.RELOADING | (self.status & GIS.DISPLAY_ACHIEVEMENT)
                self.add_event(CURRENT_CURSOR())
            case GIE.GAME_RELOADED:
                self.status |= GIS.LOADED
            case GIE.SELECTION_UP if (
                (GIS.RELOADING | GIS.LOADED) & self.status
                and not GIS.STARTED in self.status
            ):
                if (upper := self.selection.upper()) == self.selection:
                    return
                self.selection = upper
                self.__handle_event(GIE.CLICKRELEASE)
                self.add_event(CURRENT_CURSOR())
            case GIE.SELECTION_UP if GIS.PAUSE in self.status:
                self.pause_selection = 0
                self.__set_pause_arrow_offset(self.pause_continue)
            case GIE.SELECTION_DOWN if (
                (GIS.RELOADING | GIS.LOADED) & self.status
                and not GIS.STARTED in self.status
            ):
                if (lower := self.selection.lower()) == self.selection:
                    return
                self.selection = lower
                self.__handle_event(GIE.CLICKRELEASE)
                self.add_event(CURRENT_CURSOR())
            case GIE.SELECTION_DOWN if GIS.PAUSE in self.status:
                self.pause_selection = 1
                self.__set_pause_arrow_offset(self.pause_restart)
            case GIE.SELECTION_LEFT if (
                GIS.PAUSE_CONFIRM in self.status
                and GIS.RESTARTING not in self.status
            ):
                self.confirm_selection = 0
                self.__set_pause_arrow_offset(self.pause_confirm_no)
            case GIE.SELECTION_RIGHT if (
                GIS.PAUSE_CONFIRM in self.status
                and GIS.RESTARTING not in self.status
            ):
                self.confirm_selection = 1
                self.__set_pause_arrow_offset(self.pause_confirm_yes)
            case GIE.SELECTION_ENTER if (
                (GIS.RELOADING | GIS.LOADED) & self.status
                and not GIS.STARTED in self.status
            ):
                self.status &= ~GIS.PRESSING
                match self.selection:
                    case GIP.OPTIONS:
                        self.requests.append(GameRequest.GOTO_OPTIONS)
                    case GIP.ACHIEVEMENT:
                        self.requests.append(GameRequest.GOTO_ACHIEVEMENT)
                    case GIP.CONTROLS:
                        self.requests.append(GameRequest.GOTO_CONTROLS)
                    case GIP.QUIT:
                        self.requests.append(GameRequest.QUIT)
            case GIE.SELECTION_ENTER if GIS.PAUSE in self.status:
                if self.pause_selection == 0:
                    self.__handle_event(GIE.CONTINUE)
                else:
                    self.__handle_event(GIE.RESTART_CONFIRM)
            case GIE.SELECTION_ENTER if (
                GIS.PAUSE_CONFIRM in self.status
                and GIS.RESTARTING not in self.status
            ):
                if self.confirm_selection == 0:
                    self.__handle_event(GIE.PAUSE)
                else:
                    self.__handle_event(GIE.GAME_RESTART)
            case GIE.PAUSE:
                self.tick_timer.pause()
                self.game.timer.pause()
                self.pause_selection = (0, 1)[GIS.PAUSE_CONFIRM in self.status]
                self.status |= GIS.PAUSE
                self.status &= ~GIS.PAUSE_CONFIRM
                self.pause_continue.language = self.language
                self.pause_restart.language = self.language
                if self.pause_selection == 0:
                    self.__set_pause_arrow_offset(self.pause_continue)
                else:
                    self.__set_pause_arrow_offset(self.pause_restart)
                self.add_event(CURRENT_CURSOR())
            case GIE.CONTINUE:
                self.tick_timer.start()
                self.game.timer.start()
                self.status &= ~(GIS.PAUSE | GIS.PAUSE_CONFIRM | GIS.PRESSING)
            case GIE.RESTART_CONFIRM:
                self.status |= GIS.PAUSE_CONFIRM
                self.status &= ~(GIS.PAUSE | GIS.PRESSING)
                self.confirm_selection = 0
                self.pause_confirm_no.language = self.language
                self.__set_pause_arrow_offset(self.pause_confirm_no)
                self.add_event(CURRENT_CURSOR())
            case GIE.CURSOR_ON_EMPTY:
                for selection_display in self.selection_displays:
                    selection_display.color = Color.Game.SELECTION_MENU_TEXT
                self.pause_continue.color = Color.Game.PAUSE_TEXT
                self.pause_restart.color = Color.Game.PAUSE_TEXT
                self.pause_confirm_no.color = Color.Game.PAUSE_TEXT
                self.pause_confirm_yes.color = Color.Game.PAUSE_TEXT
            case (
                GIE.CURSOR_ON_OPTION | GIE.CURSOR_ON_ACHIEVEMENT 
                | GIE.CURSOR_ON_CONTROL | GIE.CURSOR_ON_QUIT
            ):
                for i, selection_display in enumerate(self.selection_displays):
                    if i == event.value - GIE.CURSOR_ON_OPTION.value:
                        selection_display.color = Color.Game.SELECTION_MENU_TEXT_SELECTING
                    else:
                        selection_display.color = Color.Game.SELECTION_MENU_TEXT
            case GIE.CURSOR_ON_CONTINUE:
                self.pause_continue.color = Color.Game.PAUSE_TEXT_SELECTING
                self.pause_restart.color = Color.Game.PAUSE_TEXT
            case GIE.CURSOR_ON_RESTART:
                self.pause_continue.color = Color.Game.PAUSE_TEXT
                self.pause_restart.color = Color.Game.PAUSE_TEXT_SELECTING
            case GIE.CURSOR_ON_BUTTON_NO:
                self.pause_confirm_no.color = Color.Game.PAUSE_TEXT_SELECTING
                self.pause_confirm_yes.color = Color.Game.PAUSE_TEXT
            case GIE.CURSOR_ON_BUTTON_YES:
                self.pause_confirm_no.color = Color.Game.PAUSE_TEXT
                self.pause_confirm_yes.color = Color.Game.PAUSE_TEXT_SELECTING
            case GIE.CLICK_ON_OPTIONS:
                self.__handle_event(GIE.CURSOR_ON_EMPTY)
                self.status |= GIS.PRESSING_OPTIONS
            case GIE.CLICK_ON_ACHIEVEMENT:
                self.__handle_event(GIE.CURSOR_ON_EMPTY)
                self.status |= GIS.PRESSING_ACHIEVEMENT
            case GIE.CLICK_ON_CONTROL:
                self.__handle_event(GIE.CURSOR_ON_EMPTY)
                self.status |= GIS.PRESSING_CONTROLS
            case GIE.CLICK_ON_QUIT:
                self.__handle_event(GIE.CURSOR_ON_EMPTY)
                self.status |= GIS.PRESSING_QUIT
            case GIE.CLICK_ON_CONTINUE:
                self.__handle_event(GIE.CURSOR_ON_EMPTY)
                self.status |= GIS.PRESSING_CONTINUE
            case GIE.CLICK_ON_RESTART:
                self.__handle_event(GIE.CURSOR_ON_EMPTY)
                self.status |= GIS.PRESSING_RESTART
            case GIE.CLICK_ON_BUTTON_NO:
                self.__handle_event(GIE.CURSOR_ON_EMPTY)
                self.status |= GIS.PRESSING_BUTTON_NO
            case GIE.CLICK_ON_BUTTON_YES:
                self.__handle_event(GIE.CURSOR_ON_EMPTY)
                self.status |= GIS.PRESSING_BUTTON_YES
            case GIE.CLICKRELEASE_ON_OPTIONS:
                if GIS.PRESSING_OPTIONS in self.status:
                    self.selection = GIP.OPTIONS
                    self.requests.append(GameRequest.GOTO_OPTIONS)
                self.__handle_event(GIE.CLICKRELEASE)
            case GIE.CLICKRELEASE_ON_ACHIEVEMENT:
                if GIS.PRESSING_ACHIEVEMENT in self.status:
                    self.selection = GIP.ACHIEVEMENT
                    self.requests.append(GameRequest.GOTO_ACHIEVEMENT)
                self.__handle_event(GIE.CLICKRELEASE)
            case GIE.CLICKRELEASE_ON_CONTROLS:
                if GIS.PRESSING_CONTROLS in self.status:
                    self.selection = GIP.CONTROLS
                    self.requests.append(GameRequest.GOTO_CONTROLS)
                self.__handle_event(GIE.CLICKRELEASE)
            case GIE.CLICKRELEASE_ON_QUIT:
                if GIS.PRESSING_QUIT in self.status:
                    self.selection = GIP.QUIT
                    self.requests.append(GameRequest.QUIT)
                self.__handle_event(GIE.CLICKRELEASE)
            case GIE.CLICKRELEASE_ON_CONTINUE:
                if GIS.PRESSING_CONTINUE in self.status:
                    self.__handle_event(GIE.CONTINUE)
                self.__handle_event(GIE.CLICKRELEASE)
            case GIE.CLICKRELEASE_ON_RESTART:
                if GIS.PRESSING_RESTART in self.status:
                    self.__handle_event(GIE.RESTART_CONFIRM)
                self.__handle_event(GIE.CLICKRELEASE)
            case GIE.CLICKRELEASE_ON_BUTTON_NO:
                if GIS.PRESSING_BUTTON_NO in self.status:
                    self.__handle_event(GIE.PAUSE)
                self.__handle_event(GIE.CLICKRELEASE)
            case GIE.CLICKRELEASE_ON_BUTTON_YES:
                if GIS.PRESSING_BUTTON_YES in self.status:
                    self.__handle_event(GIE.GAME_RESTART)
                self.__handle_event(GIE.CLICKRELEASE)
            case GIE.CLICKRELEASE:
                self.status &= ~GIS.PRESSING
                self.add_event(CURRENT_CURSOR())
            case GIE.TEST:
                self.__test()
            case GIE.QUIT:
                self.requests.append(GameRequest.QUIT)

    def __event_converter(self, event: pygameEvent) -> Event:
        match event.type:
            case pygame.KEYDOWN:
                match event.key:
                    case pygame.K_SPACE:
                        return GIE.GAME_SPACE
                    case pygame.K_d:
                        return GIE.GAME_DEBUG
                    case pygame.K_UP:
                        return GIE.SELECTION_UP
                    case pygame.K_DOWN:
                        return GIE.SELECTION_DOWN
                    case pygame.K_LEFT:
                        return GIE.SELECTION_LEFT
                    case pygame.K_RIGHT:
                        return GIE.SELECTION_RIGHT
                    case pygame.K_t:
                        return GIE.TEST
                    case pygame.K_RETURN:
                        return GIE.SELECTION_ENTER
                    case pygame.K_ESCAPE:
                        if (GIS.PAUSE | GIS.PAUSE_CONFIRM) & self.status:
                            return GIE.CONTINUE
                        if GIS.STARTED in self.status:
                            return GIE.PAUSE
            case pygame.MOUSEBUTTONDOWN if event.button == pygame.BUTTON_LEFT:
                pos = Vector(event.pos)
                if GIS.PAUSE in self.status:
                    if self.pause_continue.contains(MAIN_SCREEN, pos):
                        return GIE.CLICK_ON_CONTINUE
                    if self.pause_restart.contains(MAIN_SCREEN, pos):
                        return GIE.CLICK_ON_RESTART
                elif GIS.PAUSE_CONFIRM in self.status:
                    if GIS.RESTARTING in self.status:
                        return GIE.EMPTY
                    if self.pause_confirm_no.contains(MAIN_SCREEN, pos):
                        return GIE.CLICK_ON_BUTTON_NO
                    if self.pause_confirm_yes.contains(MAIN_SCREEN, pos):
                        return GIE.CLICK_ON_BUTTON_YES
                elif not GIS.STARTED in self.status:
                    for i, selection_display in enumerate(self.selection_displays):
                        if selection_display.contains(MAIN_SCREEN, pos):
                            return GIE(GIE.CLICK_ON_OPTIONS.value + i)
            case pygame.MOUSEBUTTONUP if event.button == pygame.BUTTON_LEFT:
                pos = Vector(event.pos)
                if GIS.PAUSE in self.status:
                    if self.pause_continue.contains(MAIN_SCREEN, pos):
                        return GIE.CLICKRELEASE_ON_CONTINUE
                    if self.pause_restart.contains(MAIN_SCREEN, pos):
                        return GIE.CLICKRELEASE_ON_RESTART
                elif GIS.PAUSE_CONFIRM in self.status:
                    if self.pause_confirm_no.contains(MAIN_SCREEN, pos):
                        return GIE.CLICKRELEASE_ON_BUTTON_NO
                    if self.pause_confirm_yes.contains(MAIN_SCREEN, pos):
                        return GIE.CLICKRELEASE_ON_BUTTON_YES
                elif not GIS.STARTED in self.status:
                    for i, selection_display in enumerate(self.selection_displays):
                        if selection_display.contains(MAIN_SCREEN, pos):
                            return GIE(GIE.CLICKRELEASE_ON_OPTIONS.value + i)
                return GIE.CLICKRELEASE
            case pygame.MOUSEMOTION:
                position = Vector(event.pos)
                if GIS.PAUSE in self.status and not self.status & GIS.PRESSING:
                    if self.pause_continue.contains(MAIN_SCREEN, position):
                        return GIE.CURSOR_ON_CONTINUE
                    if self.pause_restart.contains(MAIN_SCREEN, position):
                        return GIE.CURSOR_ON_RESTART
                elif GIS.PAUSE_CONFIRM in self.status and not self.status & GIS.PRESSING:
                    if GIS.RESTARTING in self.status:
                        return GIE.CURSOR_ON_EMPTY
                    if self.pause_confirm_no.contains(MAIN_SCREEN, position):
                        return GIE.CURSOR_ON_BUTTON_NO
                    if self.pause_confirm_yes.contains(MAIN_SCREEN, position):
                        return GIE.CURSOR_ON_BUTTON_YES
                elif not self.status & (GIS.STARTED | GIS.PRESSING):
                    for i, selection_display in enumerate(self.selection_displays):
                        if selection_display.contains(MAIN_SCREEN, position):
                            return GIE(GIE.CURSOR_ON_OPTION.value + i)
                return GIE.CURSOR_ON_EMPTY
            case pygame.QUIT:
                return GIE.QUIT
        return GIE.EMPTY
    
    def __read_debug_msg(self) -> None:
        self.debug_msgs.extend(
            GI.DebugMsgTimer(
                text, 
                Ticker(Constant.Game.DEBUG_TEXT_LASTING_TIME, start=True)
            ) for text in self.game.ball.entity.debug_msgs
        )
        while self.debug_msgs and self.debug_msgs[0].ticker.tick():
            self.debug_msgs.popleft()

    def display(
            self, 
            main_screen: Surface, 
            center_screen: Surface, 
            set_FPS: int, 
            real_FPS: int
        ) -> None:
        super().display(main_screen, center_screen)
        Interface.BACKGROUND.display(main_screen)
        center_screen.fill(Color.WHITE)
        if not (GIS.PAUSE | GIS.PAUSE_CONFIRM) & self.status:
            self.__tick()
        self.__level_display(center_screen)
        self.game.display(center_screen, self.debugging)
        if self.debugging:
            self.__debug_display(center_screen, set_FPS, real_FPS)
        if (GIS.RELOADING | GIS.LOADED | GIS.STARTING) & self.status:
            self.__starting_display(center_screen)
        if GIS.GAMEOVER in self.status:
            self.__gameover_tick()
        if self.new_record:
            self.__new_record_display(center_screen)
        if GIS.RESTART_SCREEN in self.status:
            self.__restart_screen_display(center_screen)
        self.__scoreboard_display(center_screen)
        if GIS.PAUSE in self.status:
            self.__pause_display(center_screen)
        if GIS.PAUSE_CONFIRM in self.status:
            self.__confirm_display(center_screen)
        if GIS.DISPLAY_ACHIEVEMENT in self.status:
            self.__achievement_display(center_screen)
        if GIS.RESTARTING in self.status:
            self.__restarting_display(center_screen)
        if GIS.RELOADING in self.status:
            self.__reloading_display(center_screen)

    def __starting_display(self, screen: Surface) -> None:
        if (t := self.game.timer.read()) >= 0.619:
            self.status &= ~GIS.STARTING
            return
        self.logo_display.display(
            screen, 
            Vector(
                GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 
                2000 * (t - 0.1) ** 2 + 170
            )
        )
        offset = 2000 * (t - 0.1) ** 2 - 20
        self.start_display.offset = Vector(560, Constant.Game.STARTING_TEXT_CENTER + offset)
        self.start_display.display(screen, self.language)
        for i in range(len(self.selection_displays)):
            if (GIS(GIS.PRESSING_OPTIONS.value << i) in self.status):
                self.pressed_selection_displays[i].display(screen, self.language)
            else:
                self.selection_displays[i].offset = Vector(
                    Constant.Game.SELECTION_MENU_XPOS, 
                    Constant.Game.STARTING_TEXT_CENTER 
                        + Constant.Game.SELECTION_MENU_SEP * (i + 1 - (len(GIP) + 1) / 2) 
                        + offset
                )
                self.selection_displays[i].display(screen, self.language)
        self.selection_menu_arrow_display.display(
            screen, 
            Vector(
                Constant.Game.SELECTION_MENU_ARROW_XPOS, 
                Constant.Game.STARTING_TEXT_CENTER 
                    + Constant.Game.SELECTION_MENU_SEP * (self.selection - (len(GIP) + 1) / 2) 
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
                    offset=GeneralConstant.SCREEN_OFFSET
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
                    offset=GeneralConstant.SCREEN_OFFSET
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
            offset=GeneralConstant.SCREEN_OFFSET
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
            f"{Datas.highscore}", 
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
            f"{get_level(self.game.ball.entity.position.y)}", 
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
            f"{time_string(self.game.timer.read())}", 
            Color.Game.SCOREBOARD_VALUE
        ).display(screen)

    def __pause_display(self, center_screen: Surface) -> None:
        self.pause_blackscene.display(center_screen)
        self.pause_frame.display(center_screen)
        self.pause_title.display(center_screen, self.language)
        if GIS.PRESSING_CONTINUE in self.status:
            self.pause_continue_pressed.display(center_screen, self.language)
            self.pause_restart.display(center_screen, self.language)
        elif GIS.PRESSING_RESTART in self.status:
            self.pause_continue.display(center_screen, self.language)
            self.pause_restart_pressed.display(center_screen, self.language)
        else:
            self.pause_continue.display(center_screen, self.language)
            self.pause_restart.display(center_screen, self.language)
        self.pause_arrow.display(center_screen)

    def __confirm_display(self, center_screen: Surface) -> None:
        self.pause_blackscene.display(center_screen)
        self.pause_frame.display(center_screen)
        self.pause_title.display(center_screen, self.language)
        self.pause_confirm_text.display(center_screen, self.language)
        if GIS.PRESSING_BUTTON_NO in self.status:
            self.pause_confirm_no_pressed.display(center_screen, self.language)
            self.pause_confirm_yes.display(center_screen, self.language)
        elif GIS.PRESSING_BUTTON_YES in self.status:
            self.pause_confirm_no.display(center_screen, self.language)
            self.pause_confirm_yes_pressed.display(center_screen, self.language)
        else:
            self.pause_confirm_no.display(center_screen, self.language)
            self.pause_confirm_yes.display(center_screen, self.language)
        self.pause_arrow.display(center_screen)

    def __achievement_display(self, center_screen: Surface) -> None:
        if self.achievement_state == 1:
            if (t := self.achievement_timer.read()) >= 0.3646:
                self.achievement_frame.offset.y = 60
                self.achievement_frame.display(center_screen)
                self.achievement_state = 2
                self.achievement_timer.restart()
            else:
                self.achievement_frame.offset.y = 70 - 1000 * (t - 0.2646) ** 2
                self.achievement_frame.display(center_screen)
        elif self.achievement_state == 2:
            self.achievement_frame.display(center_screen)
            if self.achievement_timer.read() >= Constant.Game.ACHIEVEMENT_FRAME_LAST_TIME:
                self.achievement_state = 3
                self.achievement_timer.restart()
        elif self.achievement_state == 3:
            if (t := self.achievement_timer.read()) >= 0.3646:
                self.status &= ~GIS.DISPLAY_ACHIEVEMENT
                return
            self.achievement_frame.offset.y = 70 - 1000 * (t - 0.1) ** 2
            self.achievement_frame.display(center_screen)

    @staticmethod
    def __get_achievement_display(
        language: Language, 
        achievement: Achievement
    ) -> StaticDisplayable:
        header = DisplayableTranslatable(
            Vector(0, 16), 
            Alignment(Alignment.Mode.DEFAULT, Alignment.Mode.LEFT), 
            Font.Game.ACHIEVEMENT_FRAME_HEADER, 
            TranslateName.game_achievement_frame_header, 
            language, 
            Color.Game.ACHIEVEMENT_FRAME
        )
        name = DisplayableTranslatable(
            Vector(0, 40), 
            Alignment(Alignment.Mode.DEFAULT, Alignment.Mode.LEFT), 
            Font.Game.ACHIEVEMENT_FRAME_NAME, 
            getattr(TranslateName, f"achievement_name_{achievement.name}"), 
            language, 
            Color.Game.ACHIEVEMENT_FRAME
        )
        center = Surface((max(256, name.surface.get_width()), 60))
        Displayable(
            Texture.ACHIEVEMENT_FRAME_CENTER, 
            Alignment(
                Alignment.Mode.DEFAULT, 
                Alignment.Mode.DEFAULT, 
                Alignment.Flag.FILL, 
                facing=Alignment.Facing.ALL
            )
        ).display(center, Vector.zero)
        header.display(center)
        name.display(center)
        frame = Surface((center.get_width() + 24, 60))
        frame.set_colorkey(Color.TRANSPARENT_COLORKEY)
        frame.fill(Color.TRANSPARENT_COLORKEY)
        Displayable(
            Texture.ACHIEVEMENT_FRAME_LEFT, 
            Alignment(Alignment.Mode.DEFAULT, Alignment.Mode.DEFAULT)
        ).display(frame, Vector.zero)
        Displayable(
            center, 
            Alignment(Alignment.Mode.CENTERED, Alignment.Mode.CENTERED)
        ).display(frame, Vector.zero)
        Displayable(
            Texture.ACHIEVEMENT_FRAME_RIGHT, 
            Alignment(Alignment.Mode.RIGHT, Alignment.Mode.RIGHT)
        ).display(frame, Vector.zero)
        return StaticDisplayable(
            frame.convert_alpha(), 
            Vector(GeneralConstant.DEFAULT_SCREEN_SIZE[0] - frame.get_width() // 2, 0), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.BOTTOM, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )

    def __add_achievement(self, achievement: Achievement) -> None:
        self.status |= GIS.DISPLAY_ACHIEVEMENT
        self.achievement_frame = self.all_achievement_displays[self.language][achievement]
        self.achievement_state = 1
        self.achievement_timer = Timer(True)

    def __debug_display(self, screen: Surface, set_FPS: int, real_FPS: int) -> None:
        base_position = Vector(2, 72)
        unit_offset = Vector(0, Constant.Game.DEBUG_TEXT_SEP)
        text_alignment = Alignment(
            Alignment.Mode.CENTERED, 
            Alignment.Mode.LEFT, 
            Alignment.Flag.REFERENCED, 
            offset=GeneralConstant.SCREEN_OFFSET
        )
        ball_entity = self.game.ball.entity
        debug_texts = [
            f"FPS(setting/real-time): {set_FPS}/{real_FPS}", 
            f"position: {ball_entity.position:.1f}", 
            f"velocity: {ball_entity.velocity:.1f}", 
            f"angle: {ball_entity.deg_angle:.1f} deg / {ball_entity.rad_angle:.2f} rad", 
            f"angular frequency: {ball_entity.angular_frequency:.2f} rad/s", 
            f"ground: {ball_entity.ground_text}", 
            f"bounceable: {("false", "true")[ball_entity.bounceable]}"
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
                Constant.Game.DEBUG_TEXT_ALPHA
            ).display(screen)

    def __gameover_tick(self) -> None:
        if self.transform_timer.read() > 2:
            self.__handle_event(GIE.GAME_TO_RESTART_SCREEN)

    def __new_record_display(self, center_screen: Surface) -> None:
        self.new_record_display.language = self.language
        background = Surface(
            (Vector(self.new_record_display.surface.get_size()) + Vector(10, 10)).inttuple
        )
        background.fill(Color.Game.NEW_RECORD_BACKGROUND)
        background.set_alpha(Constant.Game.NEW_RECORD_ALPHA)
        self.new_record_display.display(background)
        Displayable(background, BASIC_ALIGNMENT).display(
            center_screen, 
            Constant.Game.NEW_RECORD_POS
        )

    def __restart_screen_display(self, center_screen: Surface) -> None:
        if int(self.transform_timer.read() / 0.5) % 2 == 0:
            self.gameover_display.language = self.language
            background = Surface(
                (Vector(self.gameover_display.surface.get_size()) + Vector(10, 10)).inttuple
            )
            background.fill(Color.Game.RESTART_BACKGROUND)
            background.set_alpha(Constant.Game.RESTART_ALPHA)
            self.gameover_display.display(background)
            Displayable(background, BASIC_ALIGNMENT).display(
                center_screen, 
                Constant.Game.GAMEOVER_DISPLAY_POS
            )

    def __restarting_display(self, screen: Surface) -> None:
        if not GIS.PAUSE_CONFIRM in self.status:
            background = Surface(
                (Vector(self.gameover_display.surface.get_size()) + Vector(10, 10)).inttuple
            )
            background.fill(Color.Game.RESTART_BACKGROUND)
            self.gameover_display.display(background, self.language)
            StaticDisplayable(background, Vector(560, 580), BASIC_ALIGNMENT).display(screen)

        self.blackscene_alpha = int(
            self.transform_timer.read() * 255 / Constant.Game.GAMEOVER_FADEOUT_SECOND
        )
        if self.blackscene_alpha < 255:
            self.blackscene_display.surface.set_alpha(self.blackscene_alpha)
            self.blackscene_display.display(screen)
        else:
            self.blackscene_display.surface.set_alpha(255)
            self.blackscene_display.display(screen)
            self.__handle_event(GIE.GAME_RELOAD)

    def __reloading_display(self, screen: Surface) -> None:
        if (ratio := self.transform_timer.read() / Constant.Game.RESTART_SCENE_SECOND) >= 1:
            self.__handle_event(GIE.GAME_RELOADED)
            return
        self.restart_scene_radius = Constant.Game.DEFAULT_SCREEN_DIAGONAL ** ratio
        draw.circle(
            self.blackscene_display.surface, 
            Color.TRANSPARENT_COLORKEY, 
            (Vector(GeneralConstant.DEFAULT_SCREEN_SIZE) // 2).inttuple, 
            self.restart_scene_radius
        )
        self.blackscene_display.display(screen)

    def __set_pause_arrow_offset(self, rel_display: StaticDisplayable) -> None:
        self.pause_arrow.offset = rel_display.offset - Vector(
            rel_display.surface.get_width() // 2 - Constant.Game.PAUSE_ARROW_OFFSET, 
            0
        )


class OptionInterface(Interface):
    class Event(Enum):
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
        RANDOM_VOLUME_CHANGE = auto()
        CHANGE_BGM = auto()
        CHANGE_SE = auto()
        BACK = auto()
        QUIT = auto()

    class Status(Flag):
        EMPTY = 0
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
        ON_EASTER_EGG_EVENT = auto()
    
    class PageSelection(IntEnum):
        LANGUAGE = auto()
        FPS = auto()
        BGM = auto()
        SE = auto()
        BACK = auto()
        def __lshift__(self, one: Literal[1]) -> OptionInterface.PageSelection:
            if self == 1:
                return self
            return OIP(self - 1)
        def __rshift__(self, one: Literal[1]) -> OptionInterface.PageSelection:
            if self == len(OIP):
                return self
            return OIP(self + 1)

    def __init__(self) -> None:
        self.settings = Setting.load()
        self.requests: deque[OptionRequest] = deque()
        self.status = OIS.EMPTY
        self.selection = OIP.LANGUAGE
        self.volume_value = 0
        self.volume_ticker = Ticker(
            Constant.Option.VOLUME_TICKER_TICK, 
            starting_cooldown=Constant.Option.VOLUME_TICKER_STARTCOOLDOWN
        )
        self.title_display = DisplayableTranslatable(
            Constant.Option.TITLE_POS, 
            BASIC_ALIGNMENT, 
            Font.Option.TITLE, 
            TranslateName.option_title, 
            self.settings.language, 
            Color.Option.TITLE
        )
        def pressed(text: DisplayableTranslatable) -> DisplayableTranslatable:
            return DisplayableTranslatable(
                text.offset + Constant.Option.PRESSED_OFFSET, 
                text.alignment, 
                text.font, 
                text.translation, 
                text.language, 
                Color.Option.TEXT_PRESSED
            )
        selections = len(OIP) - 1
        self.language_text = DisplayableTranslatable(
            Vector(
                Constant.Option.TEXT_XPOS, 
                Constant.Option.YCENTER 
                    + (OIP.LANGUAGE - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            ), 
            Font.Option.TEXT, 
            TranslateName.option_language, 
            self.settings.language, 
            Color.Option.TEXT
        )
        self.pressed_language_text = pressed(self.language_text)
        self.FPS_text = DisplayableTranslatable(
            Vector(
                Constant.Option.TEXT_XPOS, 
                Constant.Option.YCENTER 
                    + (OIP.FPS - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            ), 
            Font.Option.TEXT, 
            TranslateName.option_fps, 
            self.settings.language, 
            Color.Option.TEXT
        )
        self.pressed_FPS_text = pressed(self.FPS_text)
        self.BGM_volume_text = DisplayableTranslatable(
            Vector(
                Constant.Option.TEXT_XPOS, 
                Constant.Option.YCENTER 
                    + (OIP.BGM - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            ), 
            Font.Option.TEXT, 
            TranslateName.option_bgm, 
            self.settings.language, 
            Color.Option.TEXT
        )
        self.pressed_BGM_volume_text = pressed(self.BGM_volume_text)
        self.SE_volume_text = DisplayableTranslatable(
            Vector(
                Constant.Option.TEXT_XPOS, 
                Constant.Option.YCENTER 
                    + (OIP.SE - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            ), 
            Font.Option.TEXT, 
            TranslateName.option_se, 
            self.settings.language, 
            Color.Option.TEXT
        )
        self.pressed_SE_volume_text = pressed(self.SE_volume_text)
        self.back_text = DisplayableTranslatable(
            Vector(
                Constant.Option.TEXT_XPOS, 
                Constant.Option.YCENTER 
                    + (OIP.BACK - (selections + 1) / 2 + Constant.Option.BACK_EXTRA_YSEP) 
                    * Constant.Option.YSEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            ), 
            Font.Option.BACKTEXT, 
            TranslateName.option_back, 
            self.settings.language, 
            Color.Option.TEXT
        )
        self.pressed_back_text = pressed(self.back_text)
        self.arrow_display = Displayable(Texture.SELECTION_MENU_ARROW, BASIC_ALIGNMENT)
        self.language_bar = StaticDisplayable(
            Texture.OPTION_SELECTION_BAR, 
            Vector(
                Constant.Option.BARS_XPOS, 
                Constant.Option.YCENTER 
                    + (OIP.LANGUAGE - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            BASIC_ALIGNMENT
        )
        self.language_bar_left_arrow = StaticDisplayable(
            Texture.OPTION_SELECTION_LEFT_ARROW, 
            Vector(
                Constant.Option.BARS_XPOS - Texture.OPTION_SELECTION_BAR.get_size()[0] // 2, 
                Constant.Option.YCENTER 
                    + (OIP.LANGUAGE - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )
        self.language_bar_right_arrow = StaticDisplayable(
            Texture.OPTION_SELECTION_RIGHT_ARROW, 
            Vector(
                Constant.Option.BARS_XPOS + Texture.OPTION_SELECTION_BAR.get_size()[0] // 2, 
                Constant.Option.YCENTER 
                    + (OIP.LANGUAGE - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.RIGHT, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )
        self.language_bar_left_arrow_pressed = StaticDisplayable(
            Texture.OPTION_SELECTION_LEFT_ARROW_PRESSED, 
            Vector(
                Constant.Option.BARS_XPOS - Texture.OPTION_SELECTION_BAR.get_size()[0] // 2, 
                Constant.Option.YCENTER 
                    + (OIP.LANGUAGE - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )
        self.language_bar_right_arrow_pressed = StaticDisplayable(
            Texture.OPTION_SELECTION_RIGHT_ARROW_PRESSED, 
            Vector(
                Constant.Option.BARS_XPOS + Texture.OPTION_SELECTION_BAR.get_size()[0] // 2, 
                Constant.Option.YCENTER 
                    + (OIP.LANGUAGE - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.RIGHT, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )
        self.language_bar_text = DisplayableTranslatable(
            Vector(
                Constant.Option.BARS_XPOS, 
                Constant.Option.YCENTER 
                    + (OIP.LANGUAGE - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            BASIC_ALIGNMENT, 
            Font.Option.BARTEXT, 
            TranslateName.name, 
            self.settings.language, 
            Color.Option.BARTEXT
        )
        self.FPS_bar = StaticDisplayable(
            Texture.OPTION_SELECTION_BAR, 
            Vector(
                Constant.Option.BARS_XPOS, 
                Constant.Option.YCENTER 
                    + (OIP.FPS - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            BASIC_ALIGNMENT
        )
        self.FPS_bar_left_arrow = StaticDisplayable(
            Texture.OPTION_SELECTION_LEFT_ARROW, 
            Vector(
                Constant.Option.BARS_XPOS - Texture.OPTION_SELECTION_BAR.get_size()[0] // 2, 
                Constant.Option.YCENTER 
                    + (OIP.FPS - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )
        self.FPS_bar_right_arrow = StaticDisplayable(
            Texture.OPTION_SELECTION_RIGHT_ARROW, 
            Vector(
                Constant.Option.BARS_XPOS + Texture.OPTION_SELECTION_BAR.get_size()[0] // 2, 
                Constant.Option.YCENTER 
                    + (OIP.FPS - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.RIGHT, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )
        self.FPS_bar_left_arrow_pressed = StaticDisplayable(
            Texture.OPTION_SELECTION_LEFT_ARROW_PRESSED, 
            Vector(
                Constant.Option.BARS_XPOS - Texture.OPTION_SELECTION_BAR.get_size()[0] // 2, 
                Constant.Option.YCENTER 
                    + (OIP.FPS - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )
        self.FPS_bar_right_arrow_pressed = StaticDisplayable(
            Texture.OPTION_SELECTION_RIGHT_ARROW_PRESSED, 
            Vector(
                Constant.Option.BARS_XPOS + Texture.OPTION_SELECTION_BAR.get_size()[0] // 2, 
                Constant.Option.YCENTER 
                    + (OIP.FPS - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.RIGHT, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )
        self.FPS_bar_text = DisplayableText(
            Vector(
                Constant.Option.BARS_XPOS, 
                Constant.Option.YCENTER 
                    + (OIP.FPS - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            BASIC_ALIGNMENT, 
            Font.Option.BARTEXT, 
            str(self.settings.FPS), 
            Color.Option.BARTEXT
        )
        self.BGM_bar = StaticDisplayable(
            Texture.OPTION_VOLUME_BAR, 
            Vector(
                Constant.Option.BARS_XPOS, 
                Constant.Option.YCENTER 
                    + (OIP.BGM - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            BASIC_ALIGNMENT
        )
        self.SE_bar = StaticDisplayable(
            Texture.OPTION_VOLUME_BAR, 
            Vector(
                Constant.Option.BARS_XPOS, 
                Constant.Option.YCENTER 
                    + (OIP.SE - (selections + 1) / 2) * Constant.Option.YSEP
            ), 
            BASIC_ALIGNMENT
        )
        self.Volume_button = DisplayableBall(
            Texture.OPTION_VOLUME_POINT_FRAME, 
            Texture.OPTION_VOLUME_POINT_SURFACE, 
            BASIC_ALIGNMENT
        )
        self.Volume_button_event = DisplayableBall(
            Texture.OPTION_VOLUME_POINT_EVENT_FRAME, 
            Texture.OPTION_VOLUME_POINT_EVENT_SURFACE, 
            BASIC_ALIGNMENT
        )
        self.volume_button_offset = Vector.zero
            
    def save(self) -> None:
        self.settings.save()
    
    def __tick(self) -> None:
        while self.volume_ticker.tick():
            if OIS.KEY_VOLUME_UP in self.status:
                self.__handle_event(OIE.UNIT_VOLUME_UP)
            elif OIS.KEY_VOLUME_DOWN in self.status:
                self.__handle_event(OIE.UNIT_VOLUME_DOWN)

    def display(self, main_screen: Surface, center_screen: Surface) -> None:
        super().display(main_screen, center_screen)
        self.__tick()
        Interface.BACKGROUND.display(main_screen)
        Interface.BACKGROUND.display(center_screen)
        self.title_display.display(center_screen, self.settings.language)
        self.__text_display(center_screen)
        self.__bar_display(center_screen)
        if self.selection == OIP.BACK:
            self.arrow_display.display(
                center_screen, 
                Vector(
                    Constant.Option.ARROW_XPOS, 
                    Constant.Option.YCENTER 
                        + (OIP.BACK - len(OIP) / 2 + Constant.Option.BACK_EXTRA_YSEP) 
                        * Constant.Option.YSEP, 
                )
            )
        else:
            self.arrow_display.display(
                center_screen, 
                Vector(
                    Constant.Option.ARROW_XPOS, 
                    Constant.Option.YCENTER 
                        + Constant.Option.YSEP * (self.selection - len(OIP) / 2) 
                )
            )
    
    def add_event(self, event: pygameEvent) -> None:
        return self.__handle_event(self.__event_converter(event))

    def get_request(self) -> Iterable[Request]:
        while self.requests:
            yield self.requests.popleft()

    def __handle_event(self, event: Event) -> None:
        match event:
            case OIE.SELECTION_UP:
                self.__select_to(self.selection << 1)
            case OIE.SELECTION_DOWN:
                self.__select_to(self.selection >> 1)
            case OIE.CURSOR_ON_EMPTY:
                self.language_text.color = Color.Option.TEXT
                self.FPS_text.color = Color.Option.TEXT
                self.BGM_volume_text.color = Color.Option.TEXT
                self.SE_volume_text.color = Color.Option.TEXT
                self.back_text.color = Color.Option.TEXT
            case OIE.CURSOR_ON_LANGUAGE:
                self.language_text.color = Color.Option.TEXT_SELECTING
                self.FPS_text.color = Color.Option.TEXT
                self.BGM_volume_text.color = Color.Option.TEXT
                self.SE_volume_text.color = Color.Option.TEXT
                self.back_text.color = Color.Option.TEXT
            case OIE.CURSOR_ON_FPS:
                self.language_text.color = Color.Option.TEXT
                self.FPS_text.color = Color.Option.TEXT_SELECTING
                self.BGM_volume_text.color = Color.Option.TEXT
                self.SE_volume_text.color = Color.Option.TEXT
                self.back_text.color = Color.Option.TEXT
            case OIE.CURSOR_ON_BGM:
                self.language_text.color = Color.Option.TEXT
                self.FPS_text.color = Color.Option.TEXT
                self.BGM_volume_text.color = Color.Option.TEXT_SELECTING
                self.SE_volume_text.color = Color.Option.TEXT
                self.back_text.color = Color.Option.TEXT
            case OIE.CURSOR_ON_SE:
                self.language_text.color = Color.Option.TEXT
                self.FPS_text.color = Color.Option.TEXT
                self.BGM_volume_text.color = Color.Option.TEXT
                self.SE_volume_text.color = Color.Option.TEXT_SELECTING
                self.back_text.color = Color.Option.TEXT
            case OIE.CURSOR_ON_BACK:
                self.language_text.color = Color.Option.TEXT
                self.FPS_text.color = Color.Option.TEXT
                self.BGM_volume_text.color = Color.Option.TEXT
                self.SE_volume_text.color = Color.Option.TEXT
                self.back_text.color = Color.Option.TEXT_SELECTING
            case OIE.CLICK_ON_LANGUAGE:
                self.__handle_event(OIE.CURSOR_ON_EMPTY)
                self.status |= OIS.PRESSING_LANGUAGE
            case OIE.CLICK_ON_FPS:
                self.__handle_event(OIE.CURSOR_ON_EMPTY)
                self.status |= OIS.PRESSING_FPS
            case OIE.CLICK_ON_BGM:
                self.__handle_event(OIE.CURSOR_ON_EMPTY)
                self.status |= OIS.PRESSING_BGM
            case OIE.CLICK_ON_SE:
                self.__handle_event(OIE.CURSOR_ON_EMPTY)
                self.status |= OIS.PRESSING_SE
            case OIE.CLICK_ON_BACK:
                self.__handle_event(OIE.CURSOR_ON_EMPTY)
                self.status |= OIS.PRESSING_BACK
            case OIE.CLICK_ON_LANGUAGE_LEFT_ARROW if (
                self.selection == OIP.LANGUAGE and self.settings.language != 1
            ):
                self.status |= OIS.PRESSING_LANGUAGE_LEFT_ARROW
            case OIE.CLICK_ON_LANGUAGE_RIGHT_ARROW if (
                self.selection == OIP.LANGUAGE and self.settings.language != len(Language)
            ):
                self.status |= OIS.PRESSING_LANGUAGE_RIGHT_ARROW
            case OIE.CLICK_ON_FPS_LEFT_ARROW if (
                self.selection == OIP.FPS and not self.settings.isFPSmin
            ):
                self.status |= OIS.PRESSING_FPS_LEFT_ARROW
            case OIE.CLICK_ON_FPS_RIGHT_ARROW if (
                self.selection == OIP.FPS and not self.settings.isFPSmax
            ):
                self.status |= OIS.PRESSING_FPS_RIGHT_ARROW
            case OIE.CLICKRELEASE_ON_LANGUAGE:
                if OIS.PRESSING_LANGUAGE in self.status:
                    self.__select_to(OIP.LANGUAGE)
                self.__handle_event(OIE.CLICKRELEASE)
            case OIE.CLICKRELEASE_ON_FPS:
                if OIS.PRESSING_FPS in self.status:
                    self.__select_to(OIP.FPS)
                self.__handle_event(OIE.CLICKRELEASE)
            case OIE.CLICKRELEASE_ON_BGM:
                if OIS.PRESSING_BGM in self.status:
                    self.__select_to(OIP.BGM)
                self.__handle_event(OIE.CLICKRELEASE)
            case OIE.CLICKRELEASE_ON_SE:
                if OIS.PRESSING_SE in self.status:
                    self.__select_to(OIP.SE)
                self.__handle_event(OIE.CLICKRELEASE)
            case OIE.CLICKRELEASE_ON_BACK:
                if OIS.PRESSING_BACK in self.status:
                    self.__handle_event(OIE.BACK)
                self.__handle_event(OIE.CLICKRELEASE)
            case OIE.CLICKRELEASE_ON_LANGUAGE_LEFT_ARROW:
                if OIS.PRESSING_LANGUAGE_LEFT_ARROW in self.status:
                    self.__handle_event(OIE.LEFT_SWITCH_LANGUAGE)
                self.__handle_event(OIE.CLICKRELEASE)
            case OIE.CLICKRELEASE_ON_LANGUAGE_RIGHT_ARROW:
                if OIS.PRESSING_LANGUAGE_RIGHT_ARROW in self.status:
                    self.__handle_event(OIE.RIGHT_SWITCH_LANGUAGE)
                self.__handle_event(OIE.CLICKRELEASE)
            case OIE.CLICKRELEASE_ON_FPS_LEFT_ARROW:
                if OIS.PRESSING_FPS_LEFT_ARROW in self.status:
                    self.__handle_event(OIE.LEFT_SWITCH_FPS)
                self.__handle_event(OIE.CLICKRELEASE)
            case OIE.CLICKRELEASE_ON_FPS_RIGHT_ARROW:
                if OIS.PRESSING_FPS_RIGHT_ARROW in self.status:
                    self.__handle_event(OIE.RIGHT_SWITCH_FPS)
                self.__handle_event(OIE.CLICKRELEASE)
            case OIE.CLICKRELEASE:
                self.status &= ~OIS.PRESSING
                self.add_event(CURRENT_CURSOR())
            case OIE.LEFT_SWITCH_LANGUAGE:
                self.settings.lshift_language()
                self.__text_language_update()
                self.add_event(CURRENT_CURSOR())
                self.requests.append(OptionRequest.CHANGE_LANGUAGE)
            case OIE.RIGHT_SWITCH_LANGUAGE:
                self.settings.rshift_language()
                self.__text_language_update()
                self.add_event(CURRENT_CURSOR())
                self.requests.append(OptionRequest.CHANGE_LANGUAGE)
            case OIE.LEFT_SWITCH_FPS:
                self.settings.lshift_FPS()
                self.FPS_bar_text.text = str(self.settings.FPS)
                self.requests.append(OptionRequest.CHANGE_FPS)
            case OIE.RIGHT_SWITCH_FPS:
                self.settings.rshift_FPS()
                self.FPS_bar_text.text = str(self.settings.FPS)
                self.requests.append(OptionRequest.CHANGE_FPS)
            case OIE.START_MOUSE_VOLUME_CHANGE:
                self.status |= OIS.MOUSE_VOLUME_CHANGE
            case OIE.STOP_MOUSE_VOLUME_CHANGE:
                self.status &= ~OIS.MOUSE_VOLUME_CHANGE
            case OIE.START_KEY_UP_VOLUME:
                if OIS.ON_EASTER_EGG_EVENT in self.status:
                    return
                self.status &= ~OIS.KEY_VOLUME_DOWN
                self.status |= OIS.KEY_VOLUME_UP
                self.volume_ticker.restart()
                self.__handle_event(OIE.UNIT_VOLUME_UP)
            case OIE.START_KEY_DOWN_VOLUME:
                if OIS.ON_EASTER_EGG_EVENT in self.status:
                    return
                self.status &= ~OIS.KEY_VOLUME_UP
                self.status |= OIS.KEY_VOLUME_DOWN
                self.volume_ticker.restart()
                self.__handle_event(OIE.UNIT_VOLUME_DOWN)
            case OIE.STOP_KEY_VOLUME_CHANGE:
                self.status &= ~OIS.KEY_VOLUME_CHANGE
            case OIE.UNIT_VOLUME_UP:
                if self.volume_value < 100:
                    self.volume_value += 1
                    if self.selection == OIP.BGM:
                        self.__handle_event(OIE.CHANGE_BGM)
                    elif self.selection == OIP.SE:
                        self.__handle_event(OIE.CHANGE_SE)
                    self.volume_button_offset = self.__volume_button_offset()
            case OIE.UNIT_VOLUME_DOWN:
                if self.volume_value > 0:
                    self.volume_value -= 1
                    if self.selection == OIP.BGM:
                        self.__handle_event(OIE.CHANGE_BGM)
                    elif self.selection == OIP.SE:
                        self.__handle_event(OIE.CHANGE_SE)
                    self.volume_button_offset = self.__volume_button_offset()
            case OIE.RANDOM_VOLUME_CHANGE:
                radius = 1 + int(
                    100 * Texture.OPTION_VOLUME_POINT_FRAME.get_width()
                    / Texture.OPTION_VOLUME_BAR.get_width()
                )
                diameter = 2 * radius
                if self.volume_value <= radius:
                    self.volume_value = randint(self.volume_value + radius, 100)
                elif self.volume_value >= 100 - radius:
                    self.volume_value = randint(0, self.volume_value - radius)
                else:
                    value = randint(0, 100 - diameter)
                    if self.volume_value - radius < value < self.volume_value + radius:
                        value += diameter
                    self.volume_value = value
                self.__handle_event(OIE.CHANGE_BGM)
                self.volume_button_offset = self.__volume_button_offset()
            case OIE.CHANGE_BGM:
                self.settings.set_BGM_volume(self.volume_value)
            case OIE.CHANGE_SE:
                self.settings.set_SE_volume(self.volume_value)
            case OIE.BACK:
                self.status = OIS.EMPTY
                self.selection = OIP.LANGUAGE
                self.__handle_event(OIE.CURSOR_ON_EMPTY)
                self.requests.append(OptionRequest.BACK)
            case OIE.QUIT:
                self.requests.append(OptionRequest.QUIT)

    def __event_converter(self, event: pygameEvent) -> Event:
        match event.type:
            case pygame.KEYDOWN:
                match event.key:
                    case pygame.K_UP:
                        return OIE.SELECTION_UP
                    case pygame.K_DOWN:
                        return OIE.SELECTION_DOWN
                    case pygame.K_LEFT:
                        match self.selection:
                            case OIP.LANGUAGE:
                                return OIE.LEFT_SWITCH_LANGUAGE
                            case OIP.FPS:
                                return OIE.LEFT_SWITCH_FPS
                            case OIP.BGM | OIP.SE:
                                return OIE.START_KEY_DOWN_VOLUME
                    case pygame.K_RIGHT:
                        match self.selection:
                            case OIP.LANGUAGE:
                                return OIE.RIGHT_SWITCH_LANGUAGE
                            case OIP.FPS:
                                return OIE.RIGHT_SWITCH_FPS
                            case OIP.BGM | OIP.SE:
                                return OIE.START_KEY_UP_VOLUME
                    case pygame.K_RETURN if self.selection == OIP.BACK:
                        return OIE.BACK
                    case pygame.K_ESCAPE:
                        return OIE.BACK
            case pygame.KEYUP:
                match event.key:
                    case pygame.K_LEFT if OIS.KEY_VOLUME_DOWN in self.status:
                        return OIE.STOP_KEY_VOLUME_CHANGE
                    case pygame.K_RIGHT if OIS.KEY_VOLUME_UP in self.status:
                        return OIE.STOP_KEY_VOLUME_CHANGE
            case pygame.MOUSEBUTTONDOWN if event.button == pygame.BUTTON_LEFT:
                pos = Vector(event.pos)
                if (
                    self.selection == OIP.LANGUAGE 
                    and self.language_bar_left_arrow.contains(MAIN_SCREEN, pos)
                ):
                    return OIE.CLICK_ON_LANGUAGE_LEFT_ARROW
                if (
                    self.selection == OIP.LANGUAGE 
                    and self.language_bar_right_arrow.contains(MAIN_SCREEN, pos)
                ):
                    return OIE.CLICK_ON_LANGUAGE_RIGHT_ARROW
                if (
                    self.selection == OIP.FPS 
                    and self.FPS_bar_left_arrow.contains(MAIN_SCREEN, pos)
                ):
                    return OIE.CLICK_ON_FPS_LEFT_ARROW
                if (
                    self.selection == OIP.FPS 
                    and self.FPS_bar_right_arrow.contains(MAIN_SCREEN, pos)
                ):
                    return OIE.CLICK_ON_FPS_RIGHT_ARROW
                if (
                    (self.selection == OIP.BGM or self.selection == OIP.SE)
                    and self.Volume_button.contains(
                        MAIN_SCREEN, 
                        self.volume_button_offset, 
                        pos
                    )
                ):
                    if OIS.ON_EASTER_EGG_EVENT in self.status:
                        return OIE.RANDOM_VOLUME_CHANGE
                    return OIE.START_MOUSE_VOLUME_CHANGE
                if (
                    self.language_text.contains(MAIN_SCREEN, pos) 
                    and not self.selection == OIP.LANGUAGE
                ):
                    return OIE.CLICK_ON_LANGUAGE
                if (
                    self.FPS_text.contains(MAIN_SCREEN, pos)
                    and not self.selection == OIP.FPS
                ):
                    return OIE.CLICK_ON_FPS
                if (
                    self.BGM_volume_text.contains(MAIN_SCREEN, pos)
                    and not self.selection == OIP.BGM
                ):
                    return OIE.CLICK_ON_BGM
                if (
                    self.SE_volume_text.contains(MAIN_SCREEN, pos)
                    and not self.selection == OIP.SE
                ):
                    return OIE.CLICK_ON_SE
                if self.back_text.contains(MAIN_SCREEN, pos):
                    return OIE.CLICK_ON_BACK
            case pygame.MOUSEBUTTONUP if event.button == pygame.BUTTON_LEFT:
                if OIS.MOUSE_VOLUME_CHANGE in self.status:
                    return OIE.STOP_MOUSE_VOLUME_CHANGE
                pos = Vector(event.pos)
                if self.language_bar_left_arrow.contains(MAIN_SCREEN, pos):
                    return OIE.CLICKRELEASE_ON_LANGUAGE_LEFT_ARROW
                if self.language_bar_right_arrow.contains(MAIN_SCREEN, pos):
                    return OIE.CLICKRELEASE_ON_LANGUAGE_RIGHT_ARROW
                if self.FPS_bar_left_arrow.contains(MAIN_SCREEN, pos):
                    return OIE.CLICKRELEASE_ON_FPS_LEFT_ARROW
                if self.FPS_bar_right_arrow.contains(MAIN_SCREEN, pos):
                    return OIE.CLICKRELEASE_ON_FPS_RIGHT_ARROW
                if self.language_text.contains(MAIN_SCREEN, pos):
                    return OIE.CLICKRELEASE_ON_LANGUAGE
                if self.FPS_text.contains(MAIN_SCREEN, pos):
                    return OIE.CLICKRELEASE_ON_FPS
                if self.BGM_volume_text.contains(MAIN_SCREEN, pos):
                    return OIE.CLICKRELEASE_ON_BGM
                if self.SE_volume_text.contains(MAIN_SCREEN, pos):
                    return OIE.CLICKRELEASE_ON_SE
                if self.back_text.contains(MAIN_SCREEN, pos):
                    return OIE.CLICKRELEASE_ON_BACK
                return OIE.CLICKRELEASE
            case pygame.MOUSEMOTION if self.status & OIS.MOUSE_VOLUME_CHANGE:
                position_x = event.pos[0] - MAIN_SCREEN.get_size()[0] // 2 \
                    - GeneralConstant.SCREEN_OFFSET.x
                barsize = Texture.OPTION_VOLUME_BAR.get_size()[0]
                x_range = (
                    Constant.Option.BARS_XPOS - barsize / 2, 
                    Constant.Option.BARS_XPOS + barsize / 2
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
                if self.selection == OIP.BGM:
                    return OIE.CHANGE_BGM
                elif self.selection == OIP.SE:
                    return OIE.CHANGE_SE
            case pygame.MOUSEMOTION if not self.status & OIS.PRESSING:
                position = Vector(event.pos)
                if (
                    self.language_text.contains(MAIN_SCREEN, position) 
                    and self.selection != OIP.LANGUAGE
                ):
                    return OIE.CURSOR_ON_LANGUAGE
                elif (
                    self.FPS_text.contains(MAIN_SCREEN, position)
                    and self.selection != OIP.FPS
                ):
                    return OIE.CURSOR_ON_FPS
                elif (
                    self.BGM_volume_text.contains(MAIN_SCREEN, position)
                    and self.selection != OIP.BGM
                ):
                    return OIE.CURSOR_ON_BGM
                elif (
                    self.SE_volume_text.contains(MAIN_SCREEN, position)
                    and self.selection != OIP.SE
                ):
                    return OIE.CURSOR_ON_SE
                elif self.back_text.contains(MAIN_SCREEN, position):
                    return OIE.CURSOR_ON_BACK
                else:
                    return OIE.CURSOR_ON_EMPTY
            case pygame.QUIT:
                return OIE.QUIT
        return OIE.EMPTY

    def __text_display(self, screen: Surface) -> None:        
        if OIS.PRESSING_LANGUAGE in self.status:
            self.pressed_language_text.display(screen, self.settings.language)
            self.language_text.language = self.settings.language
        else:
            self.language_text.display(screen, self.settings.language)
            self.pressed_language_text.language = self.settings.language
        
        if OIS.PRESSING_FPS in self.status:
            self.pressed_FPS_text.display(screen, self.settings.language)
            self.FPS_text.language = self.settings.language
        else:
            self.FPS_text.display(screen, self.settings.language)
            self.pressed_FPS_text.language = self.settings.language
        
        if OIS.PRESSING_BGM in self.status:
            self.pressed_BGM_volume_text.display(screen, self.settings.language)
            self.BGM_volume_text.language = self.settings.language
        else:
            self.BGM_volume_text.display(screen, self.settings.language)
            self.pressed_BGM_volume_text.language = self.settings.language
        
        if OIS.PRESSING_SE in self.status:
            self.pressed_SE_volume_text.display(screen, self.settings.language)
            self.SE_volume_text.language = self.settings.language
        else:
            self.SE_volume_text.display(screen, self.settings.language)
            self.pressed_SE_volume_text.language = self.settings.language

        if OIS.PRESSING_BACK in self.status:
            self.pressed_back_text.display(screen, self.settings.language)
            self.back_text.language = self.settings.language
        else:
            self.back_text.display(screen, self.settings.language)
            self.pressed_back_text.language = self.settings.language

    def __bar_display(self, screen: Surface) -> None:
        match self.selection:
            case OIP.LANGUAGE:
                self.language_bar.display(screen)
                self.language_bar_text.display(screen, self.settings.language)
                if not self.settings.language == 1:
                    if OIS.PRESSING_LANGUAGE_LEFT_ARROW in self.status:
                        self.language_bar_left_arrow_pressed.display(screen)
                    else:
                        self.language_bar_left_arrow.display(screen)
                if not self.settings.language == len(Language):
                    if OIS.PRESSING_LANGUAGE_RIGHT_ARROW in self.status:
                        self.language_bar_right_arrow_pressed.display(screen)
                    else:
                        self.language_bar_right_arrow.display(screen)
            case OIP.FPS:
                self.FPS_bar.display(screen)
                self.FPS_bar_text.display(screen)
                if not self.settings.isFPSmin:
                    if OIS.PRESSING_FPS_LEFT_ARROW in self.status:
                        self.FPS_bar_left_arrow_pressed.display(screen)
                    else:
                        self.FPS_bar_left_arrow.display(screen)
                if not self.settings.isFPSmax:
                    if OIS.PRESSING_FPS_RIGHT_ARROW in self.status:
                        self.FPS_bar_right_arrow_pressed.display(screen)
                    else:
                        self.FPS_bar_right_arrow.display(screen)
            case OIP.BGM:
                self.BGM_bar.display(screen)
                if OIS.ON_EASTER_EGG_EVENT in self.status:
                    self.Volume_button_event.display(
                        screen, 
                        self.volume_button_offset, 
                        self.volume_button_angle
                    )
                else:
                    self.Volume_button.display(
                        screen, 
                        self.volume_button_offset, 
                        self.volume_button_angle
                    )
            case OIP.SE:
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
        if selection == OIP.BGM:
            if Chance(Constant.Option.EASTER_EGG_PROBABILITY):
                self.status |= OIS.ON_EASTER_EGG_EVENT
            else:
                self.status &= ~OIS.ON_EASTER_EGG_EVENT
            self.volume_value = self.settings.BGM_Volume
            self.volume_button_offset = self.__volume_button_offset()
        elif selection == OIP.SE:
            self.status &= ~OIS.ON_EASTER_EGG_EVENT
            self.volume_value = self.settings.SE_Volume
            self.volume_button_offset = self.__volume_button_offset()
        else:
            self.status &= ~OIS.ON_EASTER_EGG_EVENT
        self.__handle_event(OIE.STOP_KEY_VOLUME_CHANGE)
        self.__handle_event(OIE.STOP_MOUSE_VOLUME_CHANGE)
        self.__handle_event(OIE.CLICKRELEASE)
        self.add_event(CURRENT_CURSOR())

    def __text_language_update(self) -> None:
        language = self.settings.language
        self.title_display.language = language
        self.language_text.language = language
        self.FPS_text.language = language
        self.BGM_volume_text.language = language
        self.SE_volume_text.language = language
        self.back_text.language = language
        self.pressed_language_text.language = language
        self.pressed_FPS_text.language = language
        self.pressed_BGM_volume_text.language = language
        self.pressed_SE_volume_text.language = language
        self.pressed_back_text.language = language

    def __volume_button_offset(self) -> Vector:
        if self.selection == OIP.BGM:
            return Vector(
                Constant.Option.BARS_XPOS 
                    + Texture.OPTION_VOLUME_BAR.get_size()[0] 
                    * (self.volume_value - 50) / 100, 
                Constant.Option.YCENTER 
                    + (OIP.BGM - len(OIP) / 2) * Constant.Option.YSEP
            )
        if self.selection == OIP.SE:
            return Vector(
                Constant.Option.BARS_XPOS 
                    + Texture.OPTION_VOLUME_BAR.get_size()[0] 
                    * (self.volume_value - 50) / 100, 
                Constant.Option.YCENTER 
                    + (OIP.SE - len(OIP) / 2) * Constant.Option.YSEP
            )
        return Vector.zero
    
    @property
    def volume_button_angle(self) -> NumberType:
        reference = Constant.Option.BARS_XPOS + Texture.OPTION_VOLUME_BAR.get_size()[0] / 2
        return _to_degree(
            (self.volume_button_offset.x - reference) / Constant.Option.VOLUME_BUTTON_RADIUS
        )
    

class AchievementInterface(Interface):
    class Event(Enum):
        EMPTY = auto()
        CURSOR_ON_SLIDER = auto()
        CURSOR_ON_BACK = auto()
        CURSOR_ON_EMPTY = auto()
        CLICK_ON_SLIDER = auto()
        CLICK_ON_BACK = auto()
        CLICKRELEASE_ON_SLIDER = auto()
        CLICKRELEASE_ON_BACK = auto()
        CLICKRELEASE = auto()
        SLIDER_MOVE = auto()
        START_PAGE_UP = auto()
        START_PAGE_DOWN = auto()
        STOP_PAGE_UP = auto()
        STOP_PAGE_DOWN = auto()
        UNIT_PAGE_UP = auto()
        UNIT_PAGE_DOWN = auto()
        PAGE_TOP = auto()
        PAGE_BOTTOM = auto()
        BACK = auto()
        QUIT = auto()

    class Status(Flag):
        EMPTY = 0
        PRESSING_SLIDER = auto()
        PRESSING_BACK = auto()
        PRESSING = PRESSING_SLIDER | PRESSING_BACK
        PAGE_UP = auto()
        PAGE_DOWN = auto()

    def __init__(self, language: Language) -> None:
        self.status = AIS.EMPTY
        self.title = DisplayableTranslatable(
            Constant.Achievement.TITLE_POS, 
            BASIC_ALIGNMENT, 
            Font.Achievement.TITLE, 
            TranslateName.achievement_title, 
            language, 
            Color.Achievement.TITLE
        )
        self.back_button = DisplayableTranslatable(
            Constant.Achievement.BACK_TEXT_POS, 
            BASIC_ALIGNMENT, 
            Font.Achievement.BACKTEXT, 
            TranslateName.achievement_back, 
            language, 
            Color.Achievement.BACK_TEXT
        )
        self.pressed_back_button = DisplayableTranslatable(
            Constant.Achievement.BACK_TEXT_POS + Constant.Achievement.PRESSED_OFFSET,  
            BASIC_ALIGNMENT, 
            Font.Achievement.BACKTEXT, 
            TranslateName.achievement_back, 
            language, 
            Color.Achievement.TEXT_PRESSED
        )
        self.arrow_display = StaticDisplayable(
            Texture.SELECTION_MENU_ARROW, 
            Constant.Achievement.BACK_TEXT_POS 
                - Vector(self.back_button.surface.get_size()[0] // 2, 0)
                + Constant.Achievement.ARROW_OFFSET, 
            BASIC_ALIGNMENT
        )
        self.inner_screen = StaticDisplayable(
            Surface(Constant.Achievement.INNER_SCREEN_SIZE), 
            Constant.Achievement.INNER_SCREEN_TOP, 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.TOP, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )
        self.inner_screen.surface.set_colorkey(Color.TRANSPARENT_COLORKEY)
        self.locked_achievement_display = self.text_surface("???", "???")
        self.set_language(language)
        self.page_ticker = Ticker(
            Constant.Achievement.PAGE_TICKER_TICK, 
            starting_cooldown=Constant.Achievement.PAGE_TICKER_STARTCOOLDOWN
        )
        self.requests: deque[AchievementRequest] = deque()

    def add_event(self, event: pygameEvent) -> None:
        self.__handle_event(self.__event_converter(event))
    
    def __handle_event(self, event: Event) -> None:
        match event:
            case AIE.CURSOR_ON_SLIDER:
                self.back_button.color = Color.Achievement.BACK_TEXT
                if not self.hide_slider:
                    self.side_slider = self.side_slider_selecting
            case AIE.CURSOR_ON_BACK:
                self.back_button.color = Color.Achievement.TEXT_SELECTING
                if not self.hide_slider:
                    self.side_slider = self.side_slider_normal
            case AIE.CURSOR_ON_EMPTY:
                self.back_button.color = Color.Achievement.BACK_TEXT
                if not self.hide_slider:
                    self.side_slider = self.side_slider_normal
            case AIE.CLICK_ON_SLIDER:
                self.__handle_event(AIE.STOP_PAGE_UP)
                self.__handle_event(AIE.STOP_PAGE_DOWN)
                self.slider_ref = self.slider_offset.y - pygame.mouse.get_pos()[1]
                self.status |= AIS.PRESSING_SLIDER
            case AIE.CLICK_ON_BACK:
                self.__handle_event(AIE.CURSOR_ON_EMPTY)
                self.status |= AIS.PRESSING_BACK
            case AIE.CLICKRELEASE_ON_SLIDER:
                self.__handle_event(AIE.CURSOR_ON_SLIDER)
                self.status &= ~AIS.PRESSING
            case AIE.CLICKRELEASE_ON_BACK:
                if AIS.PRESSING_BACK in self.status:
                    self.__handle_event(AIE.BACK)
                else:
                    self.__handle_event(AIE.CURSOR_ON_BACK)
                self.status &= ~AIS.PRESSING
            case AIE.CLICKRELEASE:
                self.__handle_event(AIE.CURSOR_ON_EMPTY)
                self.status &= ~AIS.PRESSING
            case AIE.SLIDER_MOVE:
                self.set_by_slider(pygame.mouse.get_pos()[1] + self.slider_ref)
            case AIE.START_PAGE_UP:
                self.page_ticker.restart()
                self.status &= ~AIS.PAGE_DOWN
                self.status |= AIS.PAGE_UP
                self.__handle_event(AIE.UNIT_PAGE_UP)
            case AIE.START_PAGE_DOWN:
                self.page_ticker.restart()
                self.status &= ~AIS.PAGE_UP
                self.status |= AIS.PAGE_DOWN
                self.__handle_event(AIE.UNIT_PAGE_DOWN)
            case AIE.STOP_PAGE_UP:
                self.page_ticker.stop()
                self.status &= ~AIS.PAGE_UP
            case AIE.STOP_PAGE_DOWN:
                self.page_ticker.stop()
                self.status &= ~AIS.PAGE_DOWN
            case AIE.UNIT_PAGE_UP:
                self.set_by_increment(-Constant.Achievement.UNIT_INCREMENT)
                self.add_event(CURRENT_CURSOR())
            case AIE.UNIT_PAGE_DOWN:
                self.set_by_increment(Constant.Achievement.UNIT_INCREMENT)
                self.add_event(CURRENT_CURSOR())
            case AIE.PAGE_TOP:
                self.set_by_slider(self.slider_top)
                self.add_event(CURRENT_CURSOR())
            case AIE.PAGE_BOTTOM:
                self.set_by_slider(self.slider_bottom)
                self.add_event(CURRENT_CURSOR())
            case AIE.BACK:
                self.status = AIS.EMPTY
                self.__handle_event(AIE.CURSOR_ON_EMPTY)
                self.__handle_event(AIE.STOP_PAGE_UP)
                self.__handle_event(AIE.STOP_PAGE_DOWN)
                if not self.hide_slider:
                    self.set_by_slider(self.slider_top)
                self.requests.append(AchievementRequest.BACK)
            case AIE.QUIT:
                self.requests.append(AchievementRequest.QUIT)

    def __event_converter(self, event: pygameEvent) -> Event:
        match event.type:
            case pygame.KEYDOWN:
                match event.key:
                    case pygame.K_RETURN | pygame.K_ESCAPE:
                        return AIE.BACK
                    case pygame.K_UP if (
                        not self.hide_slider
                        and AIS.PRESSING_SLIDER not in self.status
                    ):
                        return AIE.START_PAGE_UP
                    case pygame.K_DOWN if (
                        not self.hide_slider
                        and AIS.PRESSING_SLIDER not in self.status
                    ):
                        return AIE.START_PAGE_DOWN
                    case pygame.K_PAGEUP if (
                        not self.hide_slider
                        and AIS.PRESSING_SLIDER not in self.status
                    ):
                        return AIE.PAGE_TOP
                    case pygame.K_PAGEDOWN if (
                        not self.hide_slider
                        and AIS.PRESSING_SLIDER not in self.status
                    ):
                        return AIE.PAGE_BOTTOM
            case pygame.KEYUP:
                if self.hide_slider or AIS.PRESSING_SLIDER in self.status:
                    return AIE.EMPTY
                match event.key:
                    case pygame.K_UP if AIS.PAGE_UP in self.status:
                        return AIE.STOP_PAGE_UP
                    case pygame.K_DOWN if AIS.PAGE_DOWN in self.status:
                        return AIE.STOP_PAGE_DOWN
            case pygame.MOUSEWHEEL:
                if self.hide_slider or AIS.PRESSING_SLIDER in self.status:
                    return AIE.EMPTY
                if event.y == 1:
                    return AIE.UNIT_PAGE_UP
                if event.y == -1:
                    return AIE.UNIT_PAGE_DOWN
            case pygame.MOUSEBUTTONDOWN if event.button == pygame.BUTTON_LEFT:
                pos = Vector(event.pos)
                if self.back_button.contains(MAIN_SCREEN, pos):
                    return AIE.CLICK_ON_BACK
                if not self.hide_slider and self.side_slider.contains(
                    MAIN_SCREEN, 
                    self.slider_offset, 
                    pos
                ):
                    return AIE.CLICK_ON_SLIDER
            case pygame.MOUSEBUTTONUP if event.button == pygame.BUTTON_LEFT:
                pos = Vector(event.pos)
                if self.back_button.contains(MAIN_SCREEN, pos):
                    return AIE.CLICKRELEASE_ON_BACK
                if not self.hide_slider and self.side_slider.contains(
                    MAIN_SCREEN, 
                    self.slider_offset, 
                    pos
                ):
                    return AIE.CLICKRELEASE_ON_SLIDER
                return AIE.CLICKRELEASE
            case pygame.MOUSEMOTION if AIS.PRESSING_SLIDER in self.status:
                return AIE.SLIDER_MOVE
            case pygame.MOUSEMOTION if not self.status & AIS.PRESSING:
                pos = Vector(event.pos)
                if self.back_button.contains(MAIN_SCREEN, pos):
                    return AIE.CURSOR_ON_BACK
                if not self.hide_slider and self.side_slider.contains(
                    MAIN_SCREEN, 
                    self.slider_offset, 
                    pos
                ):
                    return AIE.CURSOR_ON_SLIDER
                return AIE.CURSOR_ON_EMPTY
                
    def __tick(self) -> None:
        while self.page_ticker.tick():
            if AIS.PAGE_UP in self.status:
                self.__handle_event(AIE.UNIT_PAGE_UP)
            elif AIS.PAGE_DOWN in self.status:
                self.__handle_event(AIE.UNIT_PAGE_DOWN)

    def display(self, main_screen: Surface, center_screen: Surface) -> None:
        super().display(main_screen, center_screen)
        self.__tick()
        Interface.BACKGROUND.display(main_screen)
        Interface.BACKGROUND.display(center_screen)
        self.title.display(center_screen)
        self.inner_screen.display(center_screen)
        if not self.hide_slider:
            if AIS.PRESSING_SLIDER in self.status:
                self.side_slider_pressed.display(center_screen, self.slider_offset)
            else:
                self.side_slider.display(center_screen, self.slider_offset)
        if AIS.PRESSING_BACK in self.status:
            self.pressed_back_button.display(center_screen)
        else:
            self.back_button.display(center_screen)
        self.arrow_display.display(center_screen)

    def get_request(self) -> Iterable[AchievementRequest]:
        while self.requests:
            yield self.requests.popleft()

    @staticmethod
    def text_surface(name: str, description: str) -> Surface:
        name_render = DisplayableText(
            Constant.Achievement.NAME_TEXT_OFFSET, 
            Alignment(Alignment.Mode.CENTERED, Alignment.Mode.CENTERED), 
            Font.Achievement.NAME, 
            name, 
            Color.Achievement.TEXT
        )
        name_center = Surface((name_render.surface.get_width() + 6, 24))
        Displayable(
            Texture.ACHIEVEMENT_NAME_FILL, 
            Alignment(
                Alignment.Mode.DEFAULT, 
                Alignment.Mode.DEFAULT, 
                Alignment.Flag.FILL, 
                facing=Alignment.Facing.ALL
            )
        ).display(name_center, Vector.zero)
        name_render.display(name_center)
        name_surface = Surface((name_center.get_width() + 24, 24))
        name_surface.fill(Color.TRANSPARENT_COLORKEY)
        Displayable(
            Texture.ACHIEVEMENT_NAME_LEFT, 
            Alignment(Alignment.Mode.LEFT, Alignment.Mode.LEFT)
        ).display(name_surface, Vector.zero)
        Displayable(
            Texture.ACHIEVEMENT_NAME_RIGHT, 
            Alignment(Alignment.Mode.RIGHT, Alignment.Mode.RIGHT)
        ).display(name_surface, Vector.zero)
        Displayable(
            name_center, 
            Alignment(Alignment.Mode.CENTERED, Alignment.Mode.CENTERED)
        ).display(name_surface, Vector.zero)
        description_surface = Texture.ACHIEVEMENT_DESCRIPTION.copy()
        DisplayableText(
            Constant.Achievement.DESCRIPTION_TEXT_OFFSET, 
            Alignment(Alignment.Mode.LEFT, Alignment.Mode.LEFT), 
            Font.Achievement.DESCRIPTION, 
            description, 
            Color.Achievement.TEXT
        ).display(description_surface)
        surface = Surface((720, 60))
        surface.fill(Color.TRANSPARENT_COLORKEY)
        surface.set_colorkey(Color.TRANSPARENT_COLORKEY)
        Displayable(
            name_surface, 
            Alignment(Alignment.Mode.DEFAULT, Alignment.Mode.DEFAULT)
        ).display(surface, Vector.zero)
        Displayable(
            description_surface, 
            Alignment(Alignment.Mode.BOTTOM, Alignment.Mode.BOTTOM)
        ).display(surface, Vector.zero)
        return surface.convert_alpha()

    @staticmethod
    def achievement_surface(achievement: Achievement, language: Language) -> Surface:
        name = Translatable(
            getattr(TranslateName, f"achievement_name_{achievement.name}"), 
            language
        ).text
        description = Translatable(
            getattr(TranslateName, f"achievement_description_{achievement.name}"), 
            language
        ).text
        return AI.text_surface(name, description)
    
    def add_achievements(self, achievements: Iterable[Achievement]) -> None:
        raise NotImplementedError
        def index(achievement: Achievement) -> int:
            return achievement.value.bit_length() - Achievement._unused.value.bit_length() + 1
        for achievement in achievements:
            self.achievement_displays[index(achievement)].surface = self.achievement_surface(
                achievement, 
                self.language
            )

    def set_language(self, language: Language) -> None:
        self.language = language
        self.title.language = language
        self.back_button.language = language
        self.pressed_back_button.language = language
        self.arrow_display.offset = (
            Constant.Achievement.BACK_TEXT_POS 
                - Vector(self.back_button.surface.get_size()[0] // 2, 0)
                + Constant.Achievement.ARROW_OFFSET
        )
        achievement_displays = []
        offset = Vector.zero
        unit_sep = 60 + Constant.Achievement.YSEP
        achievements = Datas.achievement
        for achievement in Achievement:
            if achievement == Achievement._unused:
                continue
            if achievement in achievements:
                achievement_displays.append(
                    StaticDisplayable(
                        self.achievement_surface(achievement, language), 
                        offset, 
                        Alignment(Alignment.Mode.DEFAULT, Alignment.Mode.DEFAULT)
                    )
                )
            else:
                achievement_displays.append(
                    StaticDisplayable(
                        self.locked_achievement_display, 
                        offset, 
                        Alignment(Alignment.Mode.DEFAULT, Alignment.Mode.DEFAULT)
                    )
                )
            offset += Vector(0, unit_sep)
        self.surface_height = max(
            len(achievement_displays) * unit_sep - Constant.Achievement.YSEP, 
            0
        )
        inner_surface = Surface((720, self.surface_height))
        inner_surface.fill(Color.TRANSPARENT_COLORKEY)
        inner_surface.set_colorkey(Color.TRANSPARENT_COLORKEY)
        for achievement_display in achievement_displays:
            achievement_display.display(inner_surface)
        self.inner_surface = inner_surface.convert_alpha()
        self.inner_surface_top = self.inner_surface_pos = 0
        self.inner_surface_bottom = (
            inner_surface.get_height() - Constant.Achievement.INNER_SCREEN_SIZE[1]
        )
        if self.surface_height <= Constant.Achievement.INNER_SCREEN_SIZE[1]:
            self.hide_slider = True
            self.inner_screen.surface = self.inner_surface
        else:
            self.hide_slider = False
            self.set_side_slider()
            self.set_inner_screen()

    def set_side_slider(self) -> None:
        screen_height = Constant.Achievement.INNER_SCREEN_SIZE[1]
        slider_length = screen_height * screen_height // self.surface_height
        slider_size = (Constant.Achievement.SLIDER_WIDTH, slider_length)
        self.slider_top: int = Constant.Achievement.INNER_SCREEN_TOP.y
        self.slider_bottom: int = self.slider_top + screen_height - slider_length
        self.slider_offset = Vector(Constant.Achievement.SLIDER_X, self.slider_top)
        self.to_surface_pos = LinearRange(
            self.slider_top, 
            self.slider_bottom, 
            self.inner_surface_top, 
            self.inner_surface_bottom
        )
        self.to_slider_pos = LinearRange(
            self.inner_surface_top, 
            self.inner_surface_bottom, 
            self.slider_top, 
            self.slider_bottom
        )
        self.side_slider_normal = Displayable(
            Surface(slider_size), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.TOP, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )
        self.side_slider_normal.surface.fill(Color.Achievement.SLIDER_NORMAL)
        self.side_slider_selecting = Displayable(
            Surface(slider_size), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.TOP, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )
        self.side_slider_selecting.surface.fill(Color.Achievement.SLIDER_SELECTING)
        self.side_slider_pressed = Displayable(
            Surface(slider_size), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.TOP, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )
        self.side_slider_pressed.surface.fill(Color.Achievement.SLIDER_PRESSED)
        self.side_slider = self.side_slider_normal

    def set_inner_screen(self) -> None:
        self.inner_screen.surface = self.inner_surface.subsurface(
            (0, self.inner_surface_pos), 
            Constant.Achievement.INNER_SCREEN_SIZE
        )

    def set_by_slider(self, slider_pos: int) -> None:
        if slider_pos <= self.slider_top:
            self.inner_surface_pos = self.inner_surface_top
            self.slider_offset.y = self.slider_top
        elif slider_pos >= self.slider_bottom:
            self.inner_surface_pos = self.inner_surface_bottom
            self.slider_offset.y = self.slider_bottom
        else:
            self.inner_surface_pos = int(self.to_surface_pos.get_value(slider_pos))
            self.slider_offset.y = slider_pos
        self.set_inner_screen()

    def set_by_increment(self, increment: int) -> None:
        self.inner_surface_pos += increment
        if self.inner_surface_pos <= self.inner_surface_top:
            self.inner_surface_pos = self.inner_surface_top
            self.slider_offset.y = self.slider_top
        elif self.inner_surface_pos >= self.inner_surface_bottom:
            self.inner_surface_pos = self.inner_surface_bottom
            self.slider_offset.y = self.slider_bottom
        else:
            self.slider_offset.y = self.to_slider_pos.get_value(self.inner_surface_pos)
        self.set_inner_screen()


class ControlInterface(Interface):
    class Event(Enum):
        CURSOR_ON_BACK = auto()
        CURSOR_ON_EMPTY = auto()
        CLICK_ON_BACK = auto()
        CLICKRELEASE_ON_BACK = auto()
        CLICKRELEASE = auto()
        BACK = auto()
        QUIT = auto()

    class Status(Flag):
        EMPTY = 0
        PRESSING_BACK = auto()

    def __init__(self, language: Language) -> None:
        self.status = CIS.EMPTY
        self.requests: deque[ControlRequest] = deque()
        self.title_display = DisplayableTranslatable(
            Constant.Control.TITLE_POS, 
            BASIC_ALIGNMENT, 
            Font.Control.TITLE, 
            TranslateName.control_title, 
            language, 
            Color.Control.TITLE
        )
        self.back_button = DisplayableTranslatable(
            Constant.Control.BACK_TEXT_POS, 
            BASIC_ALIGNMENT, 
            Font.Control.BACKTEXT, 
            TranslateName.control_back, 
            language, 
            Color.Control.TEXT
        )
        self.pressed_back_button = DisplayableTranslatable(
            Constant.Control.BACK_TEXT_POS + Constant.Control.PRESSED_OFFSET,  
            BASIC_ALIGNMENT, 
            Font.Control.BACKTEXT, 
            TranslateName.control_back, 
            language, 
            Color.Control.TEXT_PRESSED
        )
        self.arrow_display = StaticDisplayable(
            Texture.SELECTION_MENU_ARROW, 
            Constant.Control.BACK_TEXT_POS 
                - Vector(self.back_button.surface.get_size()[0] // 2, 0)
                + Constant.Control.ARROW_OFFSET, 
            BASIC_ALIGNMENT
        )
        self.set_texts(language)

    def set_language(self, language: Language) -> None:
        self.title_display.language = language
        self.back_button.language = language
        self.pressed_back_button.language = language
        self.arrow_display.offset = (
            Constant.Control.BACK_TEXT_POS 
                - Vector(self.back_button.surface.get_size()[0] // 2, 0)
                + Constant.Control.ARROW_OFFSET
        )
        self.set_texts(language)

    def set_texts(self, language: Language) -> None:
        self.D_text = DisplayableTranslatable(
            Vector.zero, 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            ), 
            Font.Control.TEXT, 
            TranslateName.control_debug, 
            language, 
            Color.Control.TEXT
        )
        ICON_SIZE = Texture.CONTROL_KEY_D.get_size()[0]
        TEXT_SIZE = self.D_text.surface.get_size()[0]
        X_CENTER = GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2
        ICON_XPOS = X_CENTER - Constant.Control.ICON_TEXT_HORIZONTAL_SEP // 2 - TEXT_SIZE // 2
        TEXT_XPOS = (
            X_CENTER + ICON_SIZE // 2 
                + Constant.Control.ICON_TEXT_HORIZONTAL_SEP // 2 - TEXT_SIZE // 2
        )
        self.space_icon = StaticDisplayable(
            Texture.CONTROL_KEY_SPACE, 
            Vector(ICON_XPOS, Constant.Control.ICON_TEXT_YPOS), 
            BASIC_ALIGNMENT
        )
        self.space_text = DisplayableTranslatable(
            Vector(TEXT_XPOS, Constant.Control.ICON_TEXT_YPOS), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            ), 
            Font.Control.TEXT, 
            TranslateName.control_bounce, 
            language, 
            Color.Control.TEXT
        )
        self.escape_icon = StaticDisplayable(
            Texture.CONTROL_KEY_ESC, 
            Vector(
                ICON_XPOS, 
                Constant.Control.ICON_TEXT_YPOS + Constant.Control.ICON_TEXT_VERTICAL_SEP
            ), 
            BASIC_ALIGNMENT
        )
        self.escape_text = DisplayableTranslatable(
            Vector(
                TEXT_XPOS, 
                Constant.Control.ICON_TEXT_YPOS + Constant.Control.ICON_TEXT_VERTICAL_SEP
            ), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.LEFT, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            ), 
            Font.Control.TEXT, 
            TranslateName.control_pause, 
            language, 
            Color.Control.TEXT
        )
        self.D_icon = StaticDisplayable(
            Texture.CONTROL_KEY_D, 
            Vector(
                ICON_XPOS, 
                Constant.Control.ICON_TEXT_YPOS + 2 * Constant.Control.ICON_TEXT_VERTICAL_SEP
            ), 
            BASIC_ALIGNMENT
        )
        self.D_text.offset = Vector(
            TEXT_XPOS, 
            Constant.Control.ICON_TEXT_YPOS + 2 * Constant.Control.ICON_TEXT_VERTICAL_SEP
        )

    def display(self, main_screen: Surface, center_screen: Surface) -> None:
        super().display(main_screen, center_screen)
        Interface.BACKGROUND.display(main_screen)
        Interface.BACKGROUND.display(center_screen)
        self.title_display.display(center_screen)
        if CIS.PRESSING_BACK in self.status:
            self.pressed_back_button.display(center_screen)
        else:
            self.back_button.display(center_screen)
        self.arrow_display.display(center_screen)
        self.space_icon.display(center_screen)
        self.space_text.display(center_screen)
        self.escape_icon.display(center_screen)
        self.escape_text.display(center_screen)
        self.D_icon.display(center_screen)
        self.D_text.display(center_screen)

    def add_event(self, event: pygameEvent) -> None:
        self.__handle_event(self.__event_converter(event))

    def get_request(self) -> Generator[ControlRequest, None, None]:
        while self.requests:
            yield self.requests.popleft()

    def __handle_event(self, event: Event) -> None:
        match event:
            case CIE.CURSOR_ON_BACK:
                self.back_button.color = Color.Control.TEXT_SELECTING
            case CIE.CURSOR_ON_EMPTY:
                self.back_button.color = Color.Control.TEXT
            case CIE.CLICK_ON_BACK:
                self.status = CIS.PRESSING_BACK
                self.__handle_event(CIE.CURSOR_ON_EMPTY)
            case CIE.CLICKRELEASE_ON_BACK:
                if self.status == CIS.PRESSING_BACK:
                    self.__handle_event(CIE.BACK)
                self.status = CIS.EMPTY
            case CIE.CLICKRELEASE:
                self.status = CIS.EMPTY
            case CIE.BACK:
                self.requests.append(ControlRequest.BACK)
                self.__handle_event(CIE.CURSOR_ON_EMPTY)
                self.__handle_event(CIE.CLICKRELEASE)
            case CIE.QUIT:
                self.requests.append(ControlRequest.QUIT)

    def __event_converter(self, event: pygameEvent) -> None:
        match event.type:
            case pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    return CIE.BACK
            case pygame.MOUSEBUTTONDOWN if event.button == pygame.BUTTON_LEFT:
                if self.back_button.contains(MAIN_SCREEN, Vector(event.pos)):
                    return CIE.CLICK_ON_BACK
            case pygame.MOUSEBUTTONUP if event.button == pygame.BUTTON_LEFT:
                if self.back_button.contains(MAIN_SCREEN, Vector(event.pos)):
                    return CIE.CLICKRELEASE_ON_BACK
                return CIE.CLICKRELEASE
            case pygame.MOUSEMOTION if not CIS.PRESSING_BACK in self.status:
                if self.back_button.contains(MAIN_SCREEN, Vector(event.pos)):
                    return CIE.CURSOR_ON_BACK
                return CIE.CURSOR_ON_EMPTY
            case pygame.QUIT:
                return CIE.QUIT

                
GI = GameInterface
GIE = GameInterface.Event
GIS = GameInterface.Status
GIP = GameInterface.PageSelection

OI = OptionInterface
OIE = OptionInterface.Event
OIS = OptionInterface.Status
OIP = OptionInterface.PageSelection

AI = AchievementInterface
AIE = AchievementInterface.Event
AIS = AchievementInterface.Status

CI = ControlInterface
CIE = ControlInterface.Event
CIS = ControlInterface.Status

BGM.play()