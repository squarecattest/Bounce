from pygame import Surface as _Surface
from game import Game, get_level
from display import Alignment, Displayable, DisplayableText, DisplayableBall, StaticDisplayable
from resources import *
from vector import Vector
from utils import Timer
from abc import ABC as _ABC
from collections import deque as _deque
from enum import Enum as _Enum, auto as _auto
from typing import NamedTuple as _NamedTuple

_SCREEN_OFFSET = Vector(-560, -315)
_INGAME_FPS = 240
_DT = 1 / _INGAME_FPS
_DEBUG_TEXT_SEP = 20
_DEBUG_TEXT_ALPHA = 150
_DEBUG_TEXT_LAST_TIME = 0.5
_FPS_COUNTS = 30

class DebugMsgTimer(_NamedTuple):
    msg: str
    timer: Timer

class Interface(_ABC):
    pass

class GameInterface(Interface):
    class Event(_Enum):
        pass

    def __init__(self, level_filepath: str) -> None:
        self.timer = Timer(start=True)
        self.game = Game(level_filepath)
        self.debugging = True
        self.record_height = 0
        self.height = 0
        self.debug_msgs: _deque[DebugMsgTimer] = _deque()
        self.ball_display = DisplayableBall(Texture.BALL, Alignment(
            Alignment.Mode.CENTERED, 
            Alignment.Mode.CENTERED, 
            Alignment.Flag.REFERENCED, 
            offset=_SCREEN_OFFSET
        ))
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
        self.scoreboard_bg = StaticDisplayable(Texture.SCOREBOARD, Vector(560, 0), Alignment(
            Alignment.Mode.CENTERED, 
            Alignment.Mode.TOP, 
            Alignment.Flag.FILL, 
            Alignment.Flag.REFERENCED, 
            facing=Alignment.Facing.UP, 
            offset=_SCREEN_OFFSET
        ))

    def tick(self, bounce: bool) -> None:
        ticks = int(_INGAME_FPS * self.timer.read())
        self.timer.offset(-ticks * _DT)
        self.game.tick(_DT, bounce)
        for _ in range(ticks - 1):
            self.game.tick(_DT, False)
        self.height = max(self.height, self.game.ball.pos_y)

    def display(self, screen: _Surface) -> None:
        self.ball_display.display(
            screen, 
            self.game.position_map(self.game.ball.position), 
            self.game.ball.deg_angle
        )
        self.ground_display.display(
            screen, 
            self.game.position_map(self.game.ground.position)
        )
        for slab in self.game.slabs:
            self.slab_display.display(
                screen, 
                self.game.position_map(slab.position)
            )
        self.__scoreboard_display(screen)
        if self.debugging:
            self.__debug_display(screen)

    def __scoreboard_display(self, screen: _Surface) -> None:
        self.scoreboard_bg.display(screen)
        scoreboard_alignment = Alignment(
            Alignment.Mode.CENTERED, 
            Alignment.Mode.LEFT, 
            Alignment.Flag.REFERENCED, 
            offset=_SCREEN_OFFSET
        )
        DisplayableText(
            Vector(6, 10), 
            scoreboard_alignment, 
            Font.SCOREBOARD_TITLE, 
            "Record Height", 
            Color.SCOREBOARD_TITLE
        ).display(screen)
        DisplayableText(
            Vector(6, 34), 
            scoreboard_alignment, 
            Font.SCOREBOARD_VALUE, 
            f"{self.record_height}", 
            Color.SCOREBOARD_VALUE
        ).display(screen)
        DisplayableText(
            Vector(379, 10), 
            scoreboard_alignment, 
            Font.SCOREBOARD_TITLE, 
            "Height", 
            Color.SCOREBOARD_TITLE
        ).display(screen)
        DisplayableText(
            Vector(379, 34), 
            scoreboard_alignment, 
            Font.SCOREBOARD_VALUE, 
            f"{int(self.height)}", 
            Color.SCOREBOARD_VALUE
        ).display(screen)
        DisplayableText(
            Vector(752, 10), 
            scoreboard_alignment, 
            Font.SCOREBOARD_TITLE, 
            "Level", 
            Color.SCOREBOARD_TITLE
        ).display(screen)
        DisplayableText(
            Vector(752, 34), 
            scoreboard_alignment, 
            Font.SCOREBOARD_VALUE, 
            f"{get_level(self.game.ball.pos_y)}", 
            Color.SCOREBOARD_VALUE
        ).display(screen)

    def __debug_display(self, screen: _Surface) -> None:
        base_position = Vector(2, 72)
        unit_offset = Vector(0, _DEBUG_TEXT_SEP)
        text_alignment = Alignment(
            Alignment.Mode.CENTERED, 
            Alignment.Mode.LEFT, 
            Alignment.Flag.REFERENCED, 
            offset=_SCREEN_OFFSET
        )
        self.debug_msgs.extend(
            (DebugMsgTimer(text, Timer(start=True)) for text in self.game.ball.debug_msgs)
        )
        while self.debug_msgs and self.debug_msgs[0].timer.read() > _DEBUG_TEXT_LAST_TIME:
            self.debug_msgs.popleft()
        debug_texts = [
            f"FPS(setting/real-time): {'--'}/{'--'}", 
            f"position: {self.game.ball.position:.2f}", 
            f"velocity: {self.game.ball.velocity:.2f}", 
            f"angle: {self.game.ball.deg_angle:.2f} deg / {self.game.ball.rad_angle:.2f} rad", 
            f"angular frequency: {self.game.ball.angular_frequency:.2f} rad/s", 
            f"ground: {self.game.ball.ground_text}", 
            f"bounceable: {("false", "true")[self.game.ball.bounceable]}"
        ]
        debug_texts.extend(debug_msg.msg for debug_msg in self.debug_msgs)
        for i, debug_text in enumerate(debug_texts):
            DisplayableText(
                base_position + unit_offset * i, 
                text_alignment, 
                Font.DEBUG_TEXT, 
                debug_text, 
                Color.DEBUG_TEXT, 
                Color.DEBUG_BACKGROUND, 
                _DEBUG_TEXT_ALPHA
            ).display(screen)