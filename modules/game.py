from physics import PhysicsBall, PhysicsGround, PhysicsSlab, PhysicsWall, PhysicsObject
from vector import _isNumber, NumberType, Vector
from errorlog import Log
from constants import GeneralConstant, GameConstant as Constant
from resources import Path
from collections import deque
from json import load as jsonload, dump as jsondump
from string import ascii_letters
from random import randint, choice
from threading import Thread
from typing import NamedTuple,  Callable, Iterator, Generator

def get_level(height: NumberType) -> int:
    return int(height) // Constant.SLAB_GAP + 1

def get_height(level: int) -> int:
    return level * Constant.SLAB_GAP - Constant.SLAB_GAP // 2 - GeneralConstant.BALL_RADIUS


class _Level(NamedTuple):
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

    def set_default(self) -> None:
        self.__levels = [_Level(**Constant.DEFAULT_LEVEL)]
        self.__current = 0
        self.__length = 1
        self.__repeat_from = None

    def __init__(self, level_filepath: str) -> None:
        default = _Level(**Constant.DEFAULT_LEVEL)
        def parse(level, index: int) -> _Level:
            match level:
                case {
                    "length": int(length), 
                    "width": int(width), 
                    "separation": int(separation),
                    "velocity": velocity, 
                    **rest
                } if (
                    length >= 2
                    and 2 <= width <= 50
                    and separation >= 0 
                    and _isNumber(velocity)
                ):
                    if rest.get("repeat_from_here") is True:
                        self.__repeat_from = index
                    return _Level(length, width, separation, velocity)
            error_args.append(f"\nInvalid level argument at level {index + 1}: {level}")
            return default

        self.__levels = []
        self.__current = 0
        length = 0
        self.__repeat_from = None
        error_args = []
        try:
            with open(level_filepath, "r") as file:
                levels = jsonload(file)
        except BaseException as e:
            self.set_default()
            Log.log(e)
            return
        if not isinstance(levels, list):
            self.set_default()
            Log.log(LevelGenerator.ParserError("Expected an array for the level file"))
            return
        for level in levels:
            self.__levels.append(parse(level, length))
            length += 1
        self.__length = length
        if error_args:
            Log.log(LevelGenerator.ParserError("".join(error_args)))

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
    GENERATE_HEIGHT: int = Constant.GROUND_Y + Constant.SLAB_GAP
    LEVEL: int = 2
    height: int
    level: int
    __slabs: deque[PhysicsSlab]
    __recycle: Callable[[], None]

    def __init__(self, level_generator: LevelGenerator) -> None:
        level = level_generator.generate()
        self.__slabs = deque()
        self.height = SlabLevel.GENERATE_HEIGHT
        self.level = SlabLevel.LEVEL
        SlabLevel.LEVEL += 1
        if level is None:
            self.__recycle = lambda: None
            SlabLevel.GENERATE_HEIGHT += Constant.SLAB_GAP
            return
        
        # Generate
        unit_length = level.length + level.separation
        generate_sets = \
            1 + (GeneralConstant.DEFAULT_SCREEN_SIZE[0] + level.length - 1) // unit_length
        cycle_length = generate_sets * unit_length

        for i in range(generate_sets):
            self.__slabs.append(
                PhysicsSlab(
                    (unit_length * i + level.length // 2, SlabLevel.GENERATE_HEIGHT), 
                    (level.length, level.width), 
                    level.velocity
                )
            )

        # Set recycle condition
        if level.velocity > 0:
            boundary = GeneralConstant.DEFAULT_SCREEN_SIZE[0] + level.length // 2
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
        SlabLevel.GENERATE_HEIGHT += Constant.SLAB_GAP

    def __iter__(self) -> Iterator[PhysicsSlab]:
        return iter(self.__slabs)

    def tick(self, dt: float) -> None:
        for slab in self.__slabs:
            slab.tick(dt)
        self.__recycle()

    @classmethod
    def reload(cls) -> None:
        cls.GENERATE_HEIGHT = Constant.GROUND_Y + Constant.SLAB_GAP
        cls.LEVEL = 2
        

class Game:
    reference: NumberType
    max_height: NumberType
    gameover: bool
    ball: PhysicsBall
    ground: PhysicsGround
    wall_left: PhysicsWall
    wall_right: PhysicsWall
    slab_levels: deque[SlabLevel]
    def __init__(self, level_filepath: str) -> None:
        self.__level_generator = LevelGenerator(level_filepath)
        self.reference = 0
        self.max_height = 0
        self.gameover = False
        self.ball = PhysicsBall(
            (GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 0), 
            GeneralConstant.BALL_RADIUS
        )
        self.ground = PhysicsGround(Constant.GROUND_Y)
        self.wall_left = PhysicsWall(0, PhysicsWall.FACING_RIGHT)
        self.wall_right = PhysicsWall(
            GeneralConstant.DEFAULT_SCREEN_SIZE[0], 
            PhysicsWall.FACING_LEFT
        )
        self.slab_levels = deque()
        while SlabLevel.GENERATE_HEIGHT <= Constant.UPPER_SLAB_BOUNDARY:
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
            <= Constant.GAMEOVER_HEIGHT + self.reference:
            self.gameover = True
            return
        if pos_y > self.max_height:
            self.max_height = pos_y
        if (reference := pos_y - Constant.TRACE_HEIGHT) > self.reference:
            self.reference = reference
            while self.slab_levels \
                and self.slab_levels[0].height <= reference + Constant.LOWER_SLAB_BOUNDARY:
                self.slab_levels.popleft()
            while SlabLevel.GENERATE_HEIGHT <= reference + Constant.UPPER_SLAB_BOUNDARY:
                self.slab_levels.append(SlabLevel(self.__level_generator))

    def restart(self) -> None:
        self.__level_generator.reload()
        SlabLevel.reload()
        self.reference = 0
        self.max_height = 0
        self.gameover = False
        self.ball = PhysicsBall(
            (GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 0), 
            GeneralConstant.BALL_RADIUS
        )
        self.slab_levels = deque()
        while SlabLevel.GENERATE_HEIGHT <= Constant.UPPER_SLAB_BOUNDARY:
            self.slab_levels.append(SlabLevel(self.__level_generator))
        
    def position_map(self, position: Vector) -> Vector:
        return Vector(position.x, Constant.ORIGINAL_TOP_HEIGHT + self.reference - position.y)
    
    @property
    def slabs(self) -> Generator[PhysicsSlab, None, None]:
        for slab_level in self.slab_levels:
            for slab in slab_level:
                yield slab

    @property
    def objects(self) -> Generator[PhysicsObject, None, None]:
        yield self.ground
        yield self.wall_left
        yield self.wall_right
        for slab in self.slabs:
            yield slab


class HighScore:
    BITLENGTH_ZERO = "aBcDeFgHiJlLm"
    BITLENGTH_ONE = "NoPqRsTuVwXyZ"
    BITLENGTH_END = "x"
    BITLENGTH_RANDOM = "".join(
        set(ascii_letters).difference(BITLENGTH_ZERO, BITLENGTH_ONE, BITLENGTH_END)
    )
    SCORE_ZERO = "AbCdEfGhIjKlM"
    SCORE_ONE = "nOpQrStUvWxYz"
    SCORE_RANDOM = "".join(set(ascii_letters).difference(SCORE_ZERO, SCORE_ONE))

    @classmethod
    def encode(cls, score: int) -> str:
        string = ""
        bits = score.bit_length()
        bits_bits = bits.bit_length()
        bit_randoms = max(
            randint(
                int(bits_bits * Constant.HIGHSCORE_BITRANDOM_MULTIPLIER[0]), 
                int(bits_bits * Constant.HIGHSCORE_BITRANDOM_MULTIPLIER[1])
            ), 
            Constant.HIGHSCORE_BITRANDOM_MINIMUM
        )
        score_randoms = max(
            randint(
                int(bits * Constant.HIGHSCORE_SCORERANDOM_MULTIPLIER[0]), 
                int(bits * Constant.HIGHSCORE_SCORERANDOM_MULTIPLIER[1])
            ), 
            Constant.HIGHSCORE_SCORERANDOM_MINIMUM
        )
        bit_totals = bits_bits + bit_randoms
        score_totals = bits + score_randoms

        while bit_totals:
            if randint(1, bit_totals) <= bit_randoms:
                string += choice(cls.BITLENGTH_RANDOM)
                bit_randoms -= 1
            elif bits % 2 == 0:
                string += choice(cls.BITLENGTH_ZERO)
                bits //= 2
            else:
                string += choice(cls.BITLENGTH_ONE)
                bits //= 2
            bit_totals -= 1
        
        string += cls.BITLENGTH_END

        while score_totals:
            if randint(1, score_totals) <= score_randoms:
                string += choice(cls.SCORE_RANDOM)
                score_randoms -= 1
            elif score % 2 == 0:
                string += choice(cls.SCORE_ZERO)
                score //= 2
            else:
                string += choice(cls.SCORE_ONE)
                score //= 2
            score_totals -= 1
        
        return string

    @classmethod
    def decode(cls, string: str) -> int:
        default = 0
        bits = 0
        bitpos = 0
        for i, c in enumerate(string):
            if c in cls.BITLENGTH_ZERO:
                bitpos += 1
            elif c in cls.BITLENGTH_ONE:
                bits += 1 << bitpos
                bitpos += 1
            elif c == cls.BITLENGTH_END:
                break
        else:
            return default
        bitpos = 0
        score = 0
        for c in string[i + 1:]:
            if c in cls.SCORE_ZERO:
                bitpos += 1
                bits -= 1
            elif c in cls.SCORE_ONE:
                score += 1 << bitpos
                bitpos += 1
                bits -= 1
        if bits != 0:
            return default
        return score
    
    @classmethod
    def load(cls) -> int:
        default = 0
        try:
            with open(Path.HIGHSCORE, "r") as file:
                raw_score = jsonload(file)
            match raw_score:
                case {"highscore": str(s)}:
                    return cls.decode(s)
                case _:
                    return default
        except FileNotFoundError:
            return default
        except BaseException as e:
            Log.log(e)
            return default
        
    @classmethod
    def save(cls, score: int) -> None:
        def thread_save() -> None:
            try:
                with open(Path.HIGHSCORE, "w") as file:
                    jsondump({"highscore": cls.encode(score)}, file, indent=4)
            except BaseException as e:
                Log.log(e)
        Thread(target=thread_save).start()