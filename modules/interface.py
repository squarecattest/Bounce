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
from resources import Font, Texture, Color
from vector import Vector
from language import Language
from utils import Timer, time_string
from constants import GeneralConstant, InterfaceConstant as Constant
from collections import deque
from enum import Enum, Flag, auto
from abc import ABC
from typing import NamedTuple


class Request:
    pass


class GameRequest(Request, Enum):
    QUIT = auto()


class Interface(ABC):
    pass


class GameInterface:
    class GameEvent(Enum):
        EMPTY = auto()
        START = SPACE = auto()
        GAMEOVER = auto()
        RESTART = auto()
        RELOAD = auto()
        RELOADED = auto()
        DEBUG = auto()
        QUIT = auto()

    class GameStatus(Flag):
        LOADED = auto()
        STARTING = auto()
        STARTED = auto()
        GAMEOVER = auto()
        RESTARTING = auto()
        RELOADING = auto()

    GE = GameEvent
    GS = GameStatus

    class DebugMsgTimer(NamedTuple):
        msg: str
        timer: Timer

    def __init__(self, level_filepath: str, language: Language) -> None:
        self.game = Game(level_filepath)
        self.language = language
        self.ingame_timer = Timer()
        self.tick_timer = Timer(start=True)
        self.transform_timer = Timer()
        self.status = GI.GS.LOADED
        self.bounce = False
        self.debugging = False
        self.record_height = 0
        self.height = 0
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

    def __restart(self) -> None:
        self.game.restart()
        self.ingame_timer.stop()
        self.tick_timer.restart()
        self.height = 0
        self.debug_msgs.clear()

    def tick(self) -> None:
        ticks = int(Constant.INGAME_FPS * self.tick_timer.read())
        self.tick_timer.offset(-ticks * Constant.DT)
        self.game.tick(Constant.DT, self.bounce)
        self.bounce = False
        for _ in range(ticks - 1):
            self.game.tick(Constant.DT, False)
        self.height = max(self.height, self.game.ball.pos_y)
        if not GI.GameStatus.GAMEOVER in self.status and self.game.gameover:
            self.__handle_event(GI.GE.GAMEOVER)
        self.__read_debug_msg()

    def add_event(self, event: Event) -> None:
        self.__handle_event(self.__event_converter(event))

    def __handle_event(self, event: GameEvent) -> None:
        match event:
            case GI.GE.SPACE if GI.GS.GAMEOVER in self.status \
                and not GI.GS.RESTARTING in self.status:
                if self.transform_timer.read() > 2:
                    self.__handle_event(GI.GE.RESTART)
            case GI.GE.SPACE if (GI.GS.RELOADING | GI.GS.LOADED) & self.status:
                self.ingame_timer.start()
                self.status |= GI.GS.STARTING | GI.GS.STARTED
                self.bounce = True
            case GI.GE.SPACE if (GI.GS.STARTING | GI.GS.STARTED) & self.status:
                self.bounce = True
            case GI.GE.DEBUG:
                self.debugging = not self.debugging
            case GI.GE.GAMEOVER:
                self.ingame_timer.pause()
                self.transform_timer.restart()
                self.status = GI.GS.GAMEOVER
            case GI.GE.RESTART:
                self.blackscene_display.surface.fill(Color.BLACK)
                self.transform_timer.restart()
                self.status |= GI.GS.RESTARTING
            case GI.GE.RELOAD:
                self.__restart()
                self.transform_timer.restart()
                self.status = GI.GS.RELOADING
            case GI.GE.RELOADED:
                self.status |= GI.GS.LOADED

    def __event_converter(self, event: Event) -> GameEvent:
        match event.type:
            case pygame.KEYDOWN:
                match event.__dict__.get("key"):
                    case pygame.K_SPACE:
                        return GI.GE.SPACE
                    case pygame.K_d:
                        return GI.GE.DEBUG
            case pygame.QUIT:
                return GI.GE.QUIT
        return GI.GE.EMPTY
    
    def __read_debug_msg(self) -> None:
        self.debug_msgs.extend(
            GI.DebugMsgTimer(text, Timer(start=True)) for text in self.game.ball.debug_msgs
        )
        while self.debug_msgs \
            and self.debug_msgs[0].timer.read() > Constant.DEBUG_TEXT_LASTING_TIME:
            self.debug_msgs.popleft()

    def display(self, screen: Surface, set_FPS: int, real_FPS: int) -> None:
        self.ground_display.display(
            screen, 
            self.game.position_map(self.game.ground.position)
        )
        for slab in self.game.slabs:
            self.slab_display.display(
                screen, 
                self.game.position_map(slab.position)
            )
        self.__level_display(screen)
        self.ball_display.display(
            screen, 
            self.game.position_map(self.game.ball.position), 
            self.game.ball.deg_angle
        )
        if self.debugging:
            self.__debug_display(screen, set_FPS, real_FPS)
        if (GI.GS.RELOADING | GI.GS.LOADED | GI.GS.STARTING) & self.status:
            self.__starting_display(screen)
        if GI.GS.GAMEOVER in self.status:
            self.__gameover_display(screen)
        self.__scoreboard_display(screen)
        if GI.GS.RESTARTING in self.status:
            self.__restarting_display(screen)
        if GI.GS.RELOADING in self.status:
            self.__reloading_display(screen)

    def __starting_display(self, screen: Surface) -> None:
        self.start_display.offset = \
            Vector(560, 1000 * (self.ingame_timer.read() - 0.1)**2 + 565)
        if self.start_display.offset.y > 650:
            self.status &= ~GI.GS.STARTING
        self.start_display.display(screen, self.language)

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
            background = Surface(
                (Vector(self.gameover_display.surface.get_size()) + Vector(10, 10)).inttuple
            )
            background.fill(Color.Game.RESTART_BACKGROUND)
            self.gameover_display.display(background, self.language)
            background.set_alpha(Constant.RESTART_TEXT_ALPHA)
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
        self.__handle_event(GI.GE.RELOAD)

    def __reloading_display(self, screen: Surface) -> None:
        if (ratio := self.transform_timer.read() / Constant.RESTART_SCENE_SECOND) >= 1:
            self.__handle_event(GI.GE.RELOADED)
            return
        self.restart_scene_radius = Constant.DEFAULT_SCREEN_DIAGONAL ** ratio
        draw.circle(
            self.blackscene_display.surface, 
            Color.Game.RESTART_COLORKEY, 
            (Vector(GeneralConstant.DEFAULT_SCREEN_SIZE) // 2).inttuple, 
            self.restart_scene_radius
        )
        self.blackscene_display.display(screen)

GI = GameInterface