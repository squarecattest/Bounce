from physics import PhysicsBall, PhysicsGround, PhysicsSlab, PhysicsWall, PhysicsObject
from vector import _isNumber, NumberType, Vector
from collections import deque as _deque
from functools import reduce as _reduce
from json import load as _load
from typing import (
    NamedTuple as _NamedTuple, 
    Callable as _Callable, 
    Iterator as _Iterator, 
    Generator as _Generator
)

_BALL_RADIUS = 20
_SLAB_GAP = 100
_DEFAULT_SCREEN_SIZE = 1120, 630
_TRACE_HEIGHT = 250
_ORIGINAL_TOP_HEIGHT = 500

_GROUND_Y = -_BALL_RADIUS
_GAMEOVER_HEIGHT = _ORIGINAL_TOP_HEIGHT - _DEFAULT_SCREEN_SIZE[1] - _BALL_RADIUS
_UPPER_SLAB_BOUNDARY = _ORIGINAL_TOP_HEIGHT + _SLAB_GAP
_LOWER_SLAB_BOUNDARY = _ORIGINAL_TOP_HEIGHT - _DEFAULT_SCREEN_SIZE[1] - _SLAB_GAP

def get_level(height: NumberType) -> int:
    return int(height) // _SLAB_GAP + 1

def get_height(level: int) -> int:
    return level * _SLAB_GAP - _SLAB_GAP // 2 - _BALL_RADIUS

class _Level(_NamedTuple):
    length: int
    width: int
    separation: int
    velocity: NumberType

class LevelGenerator:
    class ParserError(Exception):
        pass

    __levels: list[_Level]
    __current: int
    __length: int
    __repeat_from: int | None
    __error = ParserError("Failed to parse the level file")

    def __init__(self, level_filepath: str) -> None:
        def parse(level, index: int) -> _Level:
            match level:
                case {
                    "length": int(length), 
                    "width": int(width), 
                    "separation": int(separation),
                    "velocity": velocity, 
                    **rest
                } if length > 0 and width > 0 and separation >= 0 and _isNumber(velocity):
                    if rest.get("repeat_from_here") is True:
                        self.__repeat_from = index
                    return _Level(length, width, separation, velocity)
            raise LevelGenerator.__error

        self.__levels = []
        self.__current = 0
        length = 0
        self.__repeat_from = None
        with open(level_filepath, "r") as file:
            levels = _load(file)
        if not isinstance(levels, list):
            raise LevelGenerator.__error
        for level in levels:
            self.__levels.append(parse(level, length))
            length += 1
        self.__length = length

    def generate(self) -> _Level | None:
        '''
        To be documented
        '''
        if self.__current < self.__length:
            level = self.__levels[self.__current]
            self.__current += 1
            return level
        if self.__repeat_from is not None:
            level = self.__levels[self.__repeat_from]
            self.__current = self.__repeat_from + 1
            return level
        return None
    
    def reload(self) -> None:
        '''
        To be documented
        '''
        self.__current = 0
            

class SlabLevel:
    GENERATE_HEIGHT: int = _GROUND_Y + _SLAB_GAP
    LEVEL: int = 2
    height: int
    level: int
    __slabs: _deque[PhysicsSlab]
    __recycle: _Callable[[], None]

    def __init__(self, level_generator: LevelGenerator) -> None:
        level = level_generator.generate()
        self.__slabs = _deque()
        self.height = SlabLevel.GENERATE_HEIGHT
        self.level = SlabLevel.LEVEL
        SlabLevel.LEVEL += 1
        if level is None:
            self.__recycle = lambda: None
            SlabLevel.GENERATE_HEIGHT += _SLAB_GAP
            return
        
        # Generate
        unit_length = level.length + level.separation
        generate_sets = 1 + (_DEFAULT_SCREEN_SIZE[0] + level.length - 1) // unit_length
        cycle_length = generate_sets * unit_length

        for i in range(generate_sets):
            self.__slabs.append(PhysicsSlab(
                (unit_length * i + level.length // 2, SlabLevel.GENERATE_HEIGHT), 
                (level.length, level.width), 
                level.velocity
            ))

        # Set recycle condition
        if level.velocity > 0:
            boundary = _DEFAULT_SCREEN_SIZE[0] + level.length // 2
            def recycle():
                if (pos := self.__slabs[-1].position).x >= boundary:
                    pos.x -= cycle_length
                    self.__slabs.appendleft(self.__slabs.pop())
            self.__recycle = recycle
        elif level.velocity < 0:
            boundary = - (level.length // 2)
            def recycle():
                if (pos := self.__slabs[0].position).x <= boundary:
                    pos.x += cycle_length
                    self.__slabs.append(self.__slabs.popleft())
            self.__recycle = recycle
        else:
            self.__recycle = lambda: None

        # Clean up
        SlabLevel.GENERATE_HEIGHT += _SLAB_GAP

    def __iter__(self) -> _Iterator[PhysicsSlab]:
        return iter(self.__slabs)

    def tick(self, dt: float) -> None:
        for slab in self.__slabs:
            slab.tick(dt)
        self.__recycle()

    @classmethod
    def reload(cls) -> None:
        cls.GENERATE_HEIGHT = _GROUND_Y + _SLAB_GAP
        cls.LEVEL = 2
        

class Game:
    reference: NumberType
    max_height: NumberType
    gameover: bool
    ball: PhysicsBall
    ground: PhysicsGround
    wall_left: PhysicsWall
    wall_right: PhysicsWall
    slab_levels: _deque[SlabLevel]
    def __init__(self, level_filepath: str) -> None:
        self.__level_generator = LevelGenerator(level_filepath)
        self.reference = 0
        self.max_height = 0
        self.gameover = False
        self.ball = PhysicsBall((_DEFAULT_SCREEN_SIZE[0] // 2, 0), _BALL_RADIUS)
        self.ground = PhysicsGround(_GROUND_Y)
        self.wall_left = PhysicsWall(0, PhysicsWall.FACING_RIGHT)
        self.wall_right = PhysicsWall(_DEFAULT_SCREEN_SIZE[0], PhysicsWall.FACING_LEFT)
        self.slab_levels = _deque()
        while SlabLevel.GENERATE_HEIGHT <= _UPPER_SLAB_BOUNDARY:
            self.slab_levels.append(SlabLevel(self.__level_generator))

    def tick(self, dt: float, bounce: bool) -> None:
        for slab_level in self.slab_levels:
            slab_level.tick(dt)
        if self.gameover:
            return
        self.ball.tick(
            dt, 
            self.objects,
            bounce
        )
        if (pos_y := self.ball.position.y) + self.ball.radius \
            <= _GAMEOVER_HEIGHT + self.reference:
            self.gameover = True
            return
        if pos_y > self.max_height:
            self.max_height = pos_y
        if (reference := pos_y - _TRACE_HEIGHT) > self.reference:
            self.reference = reference
            while self.slab_levels \
                and self.slab_levels[0].height <= reference + _LOWER_SLAB_BOUNDARY:
                self.slab_levels.popleft()
            while SlabLevel.GENERATE_HEIGHT <= reference + _UPPER_SLAB_BOUNDARY:
                self.slab_levels.append(SlabLevel(self.__level_generator))

    def restart(self) -> None:
        self.__level_generator.reload()
        SlabLevel.reload()
        self.reference = 0
        self.max_height = 0
        self.gameover = False
        self.ball = PhysicsBall((_DEFAULT_SCREEN_SIZE[0] // 2, 0), _BALL_RADIUS)
        self.slab_levels = _deque()
        while SlabLevel.GENERATE_HEIGHT <= _UPPER_SLAB_BOUNDARY:
            self.slab_levels.append(SlabLevel(self.__level_generator))
        
    def position_map(self, position: Vector) -> Vector:
        return Vector(position.x, _ORIGINAL_TOP_HEIGHT + self.reference - position.y)
    
    @property
    def slabs(self) -> _Generator[PhysicsSlab, None, None]:
        for slab_level in self.slab_levels:
            for slab in slab_level:
                yield slab

    @property
    def objects(self) -> _Generator[PhysicsObject, None, None]:
        yield self.ground
        yield self.wall_left
        yield self.wall_right
        for slab in self.slabs:
            yield slab