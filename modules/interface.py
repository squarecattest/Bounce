import pygame
from pygame import Surface as _Surface
from pygame.event import Event
from game import Game, get_level, get_height
from display import *
from resources import *
from vector import Vector
from language import Language
from utils import Timer, time_string
from collections import deque as _deque
from dataclasses import dataclass
from enum import Enum as _Enum, auto as _auto
from typing import NamedTuple as _NamedTuple

_SCREEN_OFFSET = Vector(-560, -315)
_INGAME_FPS = 360
_DT = 1 / _INGAME_FPS
_DEBUG_TEXT_SEP = 20
_DEBUG_TEXT_ALPHA = 150
_DEBUG_TEXT_LASTING_TIME = 0.5

class GameInterface:
    class GameEvent(_Enum):
        EMPTY = _auto()
        START = BOUNCE = _auto()
        GAMEOVER = _auto()
        RESTART = _auto()
        DEBUG = _auto()
        QUIT = _auto()

    @dataclass
    class GameStatus:
        started: bool
        starting: bool
        gameover: bool
        restarting: bool

    class DebugMsgTimer(_NamedTuple):
        msg: str
        timer: Timer

    def __restart(self) -> None:
        pass
    def __init__(self, level_filepath: str, language: Language) -> None:
        self.game = Game(level_filepath)
        self.language = language
        self.ingame_timer = Timer()
        self.tick_timer = Timer(start=True)
        self.status = GI.GameStatus(False, False, False, False)
        self.bounce = False
        self.debugging = False
        self.record_height = 0
        self.height = 0
        self.debug_msgs: _deque[GI.DebugMsgTimer] = _deque()
        self.ball_display = DisplayableBall(
            Texture.BALL_FRAME, 
            Texture.BALL_SURFACE, 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=_SCREEN_OFFSET
            )
        )
        self.ground_display = Displayable(Texture.GROUND, Alignment(
            Alignment.Mode.CENTERED, 
            Alignment.Mode.TOP, 
            Alignment.Flag.FILL, 
            Alignment.Flag.REFERENCED, 
            facing=Alignment.Facing.DOWN, 
            offset=_SCREEN_OFFSET
        ))
        self.slab_display = Displayable(Texture.SLAB, Alignment(
            Alignment.Mode.CENTERED, 
            Alignment.Mode.CENTERED, 
            Alignment.Flag.REFERENCED,
            offset=_SCREEN_OFFSET
        ))
        self.scoreboard_bg = StaticDisplayable(
            Texture.SCOREBOARD, 
            Vector(560, 0), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.TOP, 
                Alignment.Flag.FILL, 
                Alignment.Flag.REFERENCED, 
                facing=Alignment.Facing.UP, 
                offset=_SCREEN_OFFSET
            )
        )
        self.start_display = DisplayableTranslatable(
            Vector(560, 580), 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=_SCREEN_OFFSET
            ), 
            Font.Game.START_TEXT, 
            TranslateName.game_start_text, 
            language, 
            Color.Game.START_TEXT
        )

    def tick(self) -> None:
        ticks = int(_INGAME_FPS * self.tick_timer.read())
        self.tick_timer.offset(-ticks * _DT)
        self.game.tick(_DT, self.bounce)
        self.bounce = False
        for _ in range(ticks - 1):
            self.game.tick(_DT, False)
        self.height = max(self.height, self.game.ball.pos_y)
        if not self.status.gameover and self.game.gameover:
            self.__handle_event(GI.GameEvent.GAMEOVER)
        self.__read_debug_msg()

    def add_event(self, event: Event) -> None:
        self.__handle_event(self.__event_converter(event))

    def __handle_event(self, event: GameEvent) -> None:
        match event:
            case GI.GameEvent.BOUNCE if self.status.gameover:
                if self.gameover_timer.read() > 2:
                    self.__handle_event(GI.GameEvent.RESTART)
            case GI.GameEvent.BOUNCE:
                if not self.status.started:
                    self.status.started = self.status.starting = True
                    self.ingame_timer.start()
                self.bounce = True
            case GI.GameEvent.DEBUG:
                self.debugging = not self.debugging
            case GI.GameEvent.GAMEOVER:
                self.status.gameover = True
                self.ingame_timer.pause()
                self.gameover_timer = Timer(start=True)
            case GI.GameEvent.RESTART:
                pass

    def __event_converter(self, event: Event) -> GameEvent:
        match event.type:
            case pygame.KEYDOWN:
                match event.__dict__.get("key"):
                    case pygame.K_SPACE:
                        return GI.GameEvent.BOUNCE
                    case pygame.K_d:
                        return GI.GameEvent.DEBUG
            case pygame.QUIT:
                return GI.GameEvent.QUIT
        return GI.GameEvent.EMPTY
    
    def __read_debug_msg(self) -> None:
        self.debug_msgs.extend(
            (GI.DebugMsgTimer(text, Timer(start=True)) for text in self.game.ball.debug_msgs)
        )
        while self.debug_msgs and self.debug_msgs[0].timer.read() > _DEBUG_TEXT_LASTING_TIME:
            self.debug_msgs.popleft()

    def display(self, screen: _Surface, set_FPS: int, real_FPS: int) -> None:
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
        if not self.status.started or self.status.starting:
            self.__starting_display(screen)
        if self.status.gameover:
            self.__gameover_display(screen)
        self.__scoreboard_display(screen)
        if self.debugging:
            self.__debug_display(screen, set_FPS, real_FPS)

    def __starting_display(self, screen: _Surface) -> None:
        self.start_display.offset = \
            Vector(560, 1000 * (self.ingame_timer.read() - 0.1)**2 + 565)
        if self.start_display.offset.y > 650:
            self.status.starting = False
        self.start_display.display(screen, self.language)

    def __level_display(self, screen: _Surface) -> None:
        def at_level(level: int) -> None:
            DisplayableText(
                self.game.position_map(Vector(7, get_height(level)) + Vector(2, -2)), 
                Alignment(
                    Alignment.Mode.CENTERED, 
                    Alignment.Mode.LEFT, 
                    Alignment.Flag.REFERENCED, 
                    offset=_SCREEN_OFFSET
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
                    offset=_SCREEN_OFFSET
                ), 
                Font.Game.LEVEL_TEXT, 
                str(level), 
                Color.Game.LEVEL_TEXT
            ).display(screen)
        at_level(1)
        for slab_level in self.game.slab_levels:
            at_level(slab_level.level)

    def __scoreboard_display(self, screen: _Surface) -> None:
        self.scoreboard_bg.display(screen)
        scoreboard_alignment = Alignment(
            Alignment.Mode.CENTERED, 
            Alignment.Mode.LEFT, 
            Alignment.Flag.REFERENCED, 
            offset=_SCREEN_OFFSET
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

    def __debug_display(self, screen: _Surface, set_FPS: int, real_FPS: int) -> None:
        base_position = Vector(2, 72)
        unit_offset = Vector(0, _DEBUG_TEXT_SEP)
        text_alignment = Alignment(
            Alignment.Mode.CENTERED, 
            Alignment.Mode.LEFT, 
            Alignment.Flag.REFERENCED, 
            offset=_SCREEN_OFFSET
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
                _DEBUG_TEXT_ALPHA
            ).display(screen)

    def __gameover_display(self, screen: _Surface) -> None:
        if (t := self.gameover_timer.read()) > 2 and int(2 * t) % 2 == 0:
            print(t)
            DisplayableTranslatable(
                Vector.zero, 
                Alignment(
                    Alignment.Mode.CENTERED, 
                    Alignment.Mode.CENTERED
                ), 
                Font.Game.RESTART_TEXT, 
                TranslateName.game_restart_text, 
                self.language, 
                Color.Game.RESTART_TEXT, 
                Color.Game.RESTART_BACKGROUND
            ).display(screen)

GI = GameInterface