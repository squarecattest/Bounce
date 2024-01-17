from pygame import Surface
from physics import (
    PhysicsGround, 
    PhysicsWall, 
    PhysicsSlab, 
    PhysicsRocket, 
    PhysicsBall, 
    PhysicsParticle, 
    PhysicsObject
)
from vector import _isNumber, NumberType, VectorType, Vector
from display import (
    Alignment, 
    Displayable, 
    DisplayableBall, 
    DisplayableSlab, 
    DisplayableParticle
)
from errorlog import Log
from constants import GeneralConstant, GameConstant as Constant, InterfaceConstant
from resources import Texture, Path
from utils import Direction, LinkedList
from abc import ABC, abstractmethod
from collections import deque
from itertools import product
from random import uniform
from json import load as jsonload, dump as jsondump
from string import ascii_letters
from random import randint, choice
from threading import Thread
from typing import NamedTuple, Callable, Iterable, Iterator, Generator

def get_level(height: NumberType) -> int:
    return int(height) // Constant.SLAB_GAP + 1

def get_height(level: int) -> int:
    return level * Constant.SLAB_GAP - Constant.SLAB_GAP // 2 - GeneralConstant.BALL_RADIUS


class GameObject(ABC):
    entity: PhysicsObject
    displayable: Displayable
    
    @abstractmethod
    def tick(self, dt: float, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def display(self, center_screen: Surface, position_map: Callable[[Vector], Vector]) -> None:
        pass


class Particle(GameObject):
    entity: PhysicsParticle
    displayable: DisplayableParticle

    def __init__(
        self, 
        position: VectorType, 
        velocity: VectorType, 
        initial_angle: NumberType, 
        angular_frequency: NumberType, 
        surface: Surface
    ) -> None:
        self.entity = PhysicsParticle(position, velocity, initial_angle, angular_frequency)
        self.displayable = DisplayableParticle(
            surface, 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )
        self.largerside = max(surface.get_size())

    def tick(self, dt: float) -> None:
        self.entity.tick(dt)

    def display(self, center_screen: Surface, position_map: Callable[[Vector], Vector]) -> None:
        self.displayable.display(
            center_screen, 
            position_map(self.entity.position), 
            self.entity.deg_angle
        )

    def check_removal(self, bottom_y: NumberType) -> bool:
        position = self.entity.position
        return (
            position.y + self.largerside <= bottom_y
            or position.x + self.largerside <= 0
            or position.x - self.largerside >= GeneralConstant.DEFAULT_SCREEN_SIZE[0]
        )
    

class ParticleGroup(LinkedList[Particle]):
    def tick(self, dt: float, bottom_y: NumberType) -> None:
        for node in self.node_iter:
            node.data.tick(dt)
            if node.data.check_removal(bottom_y):
                self.pop(node)

    def display(self, center_screen: Surface, position_map: Callable[[Vector], Vector]) -> None:
        for particle in self.data_iter:
            particle.display(center_screen, position_map)


class Slab(GameObject):
    entity: PhysicsSlab
    displayable: DisplayableSlab

    def __init__(
        self, 
        position: VectorType, 
        length: int, 
        width: int, 
        velocity_x: NumberType
    ) -> None:
        self.entity = PhysicsSlab(position, (length, width), velocity_x)
        self.displayable = DisplayableSlab(
            Texture.SLAB_FRAME, 
            Texture.SLAB_SURFACE, 
            length, 
            width, 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )

    def tick(self, dt: float) -> None:
        self.entity.tick(dt)

    def display(self, center_screen: Surface, position_map: Callable[[Vector], Vector]) -> None:
        self.displayable.display(center_screen, position_map(self.entity.position))

    def check_rocket_collision(
        self, 
        rocket: PhysicsRocket, 
        particle_group: ParticleGroup
    ) -> None:
        direction, length = self.entity.get_shrink_parameter(rocket)
        if length == 0:
            return
        if direction == Direction.LEFT:
            particle_group.extend(
                self.generate_particle(
                    self.entity.active_length_range[0] - length, 
                    rocket.position + Vector(rocket.halfsize.x, 0), 
                    self.displayable.shrink_fromleft(length)
                )
            )
        elif direction == Direction.RIGHT:
            surface = self.displayable.shrink_fromright(length)
            particle_group.extend(
                self.generate_particle(
                    self.entity.active_length_range[1], 
                    rocket.position - Vector(rocket.halfsize.x, 0), 
                    surface
                )
            )

    def generate_particle(
            self, 
            range_left: int, 
            rocket_head: Vector, 
            surface: Surface
        ) -> list[Particle]:
        unit_range = (
            (surface.get_size()[0] - 1) // Constant.UNIT_PARTICLE_SIZE + 1, 
            (surface.get_size()[1] - 1) // Constant.UNIT_PARTICLE_SIZE + 1
        )
        surface_size = (
            Constant.UNIT_PARTICLE_SIZE * unit_range[0], 
            Constant.UNIT_PARTICLE_SIZE * unit_range[1]
        )
        new_surface = Surface(surface_size)
        new_surface.blit(surface, (0, 0))
        reference = (
            self.entity.position + Vector(-self.entity.size[0], self.entity.size[1]) / 2
            + Vector(range_left + 0.5, -0.5)
        )
        particles = []
        unit_offset = Vector(Constant.UNIT_PARTICLE_SIZE, Constant.UNIT_PARTICLE_SIZE) / 2
        for x, y in product(range(unit_range[0]), range(unit_range[1])):
            position = reference + Vector(x, -y) * Constant.UNIT_PARTICLE_SIZE + unit_offset
            particles.append(
                Particle(
                    position, 
                    (position - rocket_head) * Constant.PARTICLE_OFFSET_SPEED_CONSTANT
                    + Vector(
                        uniform(
                            -Constant.PARTICLE_RANDOM_SPEED, 
                            Constant.PARTICLE_RANDOM_SPEED
                        ), 
                        uniform(
                            -Constant.PARTICLE_RANDOM_SPEED, 
                            Constant.PARTICLE_RANDOM_SPEED
                        )
                    ), 
                    0, 
                    uniform(
                        -Constant.PARTICLE_RANDOM_ANGULAR_FREQUENCY, 
                        Constant.PARTICLE_RANDOM_ANGULAR_FREQUENCY
                    ), 
                    new_surface.subsurface(
                        (x * Constant.UNIT_PARTICLE_SIZE, y * Constant.UNIT_PARTICLE_SIZE), 
                        (Constant.UNIT_PARTICLE_SIZE, Constant.UNIT_PARTICLE_SIZE)
                    )
                )
            )
        return particles


class Rocket(GameObject):
    entity: PhysicsRocket
    displayable: Displayable
    __left_displayable = Displayable(
        Texture.ROCKET_FACING_LEFT, 
        Alignment(
            Alignment.Mode.CENTERED, 
            Alignment.Mode.CENTERED, 
            Alignment.Flag.REFERENCED, 
            offset=GeneralConstant.SCREEN_OFFSET
        )
    )
    __right_displayable = Displayable(
        Texture.ROCKET_FACING_RIGHT, 
        Alignment(
            Alignment.Mode.CENTERED, 
            Alignment.Mode.CENTERED, 
            Alignment.Flag.REFERENCED, 
            offset=InterfaceConstant.SCREEN_OFFSET
        )
    )

    def __init__(self, position: Vector, velocity_x: NumberType) -> None:
        self.entity = PhysicsRocket(position, velocity_x)
        self.displayable = (
            Rocket.__left_displayable 
            if self.entity.facing == Direction.LEFT
            else Rocket.__right_displayable
        )

    def tick(self, dt: float) -> None:
        self.entity.tick(dt)
    
    def display(self, center_screen: Surface, position_map: Callable[[Vector], Vector]) -> None:
        self.displayable.display(center_screen, position_map(self.entity.position))


class RocketGroup(LinkedList[Rocket]):
    def tick(self, dt: float) -> None:
        for node in self.node_iter:
            node.data.tick(dt)
            if node.data.entity.remove:
                self.pop(node)
    
    def display(self, center_screen: Surface, position_map: Callable[[Vector], Vector]) -> None:
        for rocket in self.data_iter:
            rocket.display(center_screen, position_map)


class Ball(GameObject):
    entity: PhysicsBall
    displayable: DisplayableBall
    remove: bool

    def __init__(self, position: Vector) -> None:
        self.entity = PhysicsBall(position, GeneralConstant.BALL_RADIUS)
        self.displayable = DisplayableBall(
            Texture.BALL_FRAME, 
            Texture.BALL_SURFACE, 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.CENTERED, 
                Alignment.Flag.REFERENCED, 
                GeneralConstant.SCREEN_OFFSET
            )
        )
        self.remove = False

    def tick(
        self, 
        dt: float, 
        bounce: bool, 
        *objs: Iterable[PhysicsObject], 
        particle_group: ParticleGroup
    ) -> None:
        self.entity.tick(dt, bounce, *objs)
        if self.entity.crash_on_rocket:
            particle_group.extend(self.generate_particle())
            self.remove = True

    def display(self, center_screen: Vector, position_map: Callable[[Vector], Vector]) -> None:
        self.displayable.display(
            center_screen, 
            position_map(self.entity.position), 
            self.entity.deg_angle
        )

    def check_removal(self, bottom_y: NumberType) -> bool:
        return self.remove or self.entity.position.y + self.entity.radius <= bottom_y

    def generate_particle(self) -> list[Particle]:
        surface = self.displayable.surface
        original_surface_size = surface.get_size()
        unit_range = (
            (original_surface_size[0] - 1) // Constant.UNIT_PARTICLE_SIZE + 1, 
            (original_surface_size[1] - 1) // Constant.UNIT_PARTICLE_SIZE + 1
        )
        surface_size = (
            Constant.UNIT_PARTICLE_SIZE * unit_range[0], 
            Constant.UNIT_PARTICLE_SIZE * unit_range[1]
        )
        new_surface = Surface(surface_size)
        new_surface.blit(surface, (0, 0))
        reference = (
            self.entity.position 
            + Vector(-original_surface_size[0], original_surface_size[1]) / 2 
            + Vector(0.5, -0.5)
        )
        particles = []
        unit_offset = Vector(Constant.UNIT_PARTICLE_SIZE, Constant.UNIT_PARTICLE_SIZE) / 2
        for x, y in product(range(unit_range[0]), range(unit_range[1])):
            position = reference + Vector(x, -y) * Constant.UNIT_PARTICLE_SIZE + unit_offset
            particles.append(
                Particle(
                    position, 
                    position * Constant.PARTICLE_OFFSET_SPEED_CONSTANT
                    + Vector(
                        uniform(
                            -Constant.PARTICLE_RANDOM_SPEED, 
                            Constant.PARTICLE_RANDOM_SPEED
                        ), 
                        uniform(
                            -Constant.PARTICLE_RANDOM_SPEED, 
                            Constant.PARTICLE_RANDOM_SPEED
                        )
                    ), 
                    0, 
                    uniform(
                        -Constant.PARTICLE_RANDOM_ANGULAR_FREQUENCY, 
                        Constant.PARTICLE_RANDOM_ANGULAR_FREQUENCY
                    ), 
                    new_surface.subsurface(
                        (x * Constant.UNIT_PARTICLE_SIZE, y * Constant.UNIT_PARTICLE_SIZE), 
                        (Constant.UNIT_PARTICLE_SIZE, Constant.UNIT_PARTICLE_SIZE)
                    )
                )
            )
        return particles
    

class BallGroup(LinkedList[Ball]):
    def tick(
        self, 
        dt: float, 
        *objs: Iterable[PhysicsObject], 
        particle_group: ParticleGroup, 
        bottom_y: NumberType
    ) -> None:
        for node in self.node_iter:
            node.data.tick(dt, False, *objs, particle_group=particle_group)
            if node.data.check_removal(bottom_y):
                self.pop(node)

    def display(self, center_screen: Surface, position_map: Callable[[Vector], Vector]) -> None:
        for ball in self.data_iter:
            ball.display(center_screen, position_map)


class Level(NamedTuple):
    length: int
    width: int
    separation: int
    velocity: NumberType


class LevelGenerator:
    class ParserError(Exception):
        pass

    __levels: list[Level]
    __current: int
    __length: int
    __repeat_from: int | None

    def set_default(self) -> None:
        self.__levels = [Level(**Constant.DEFAULT_LEVEL)]
        self.__current = 0
        self.__length = 1
        self.__repeat_from = None

    def __init__(self, level_filepath: str) -> None:
        default = Level(**Constant.DEFAULT_LEVEL)
        def parse(level, index: int) -> Level:
            match level:
                case {
                    "length": int(length), 
                    "width": int(width), 
                    "separation": int(separation),
                    "velocity": velocity, 
                    **rest
                } if (
                    length >= 4
                    and 4 <= width <= 50
                    and separation >= 0 
                    and _isNumber(velocity)
                ):
                    if rest.get("repeat_from_here") is True:
                        self.__repeat_from = index
                    return Level(length, width, separation, velocity)
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

    def generate(self) -> Level | None:
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
    level_info: Level | None
    __slabs: deque[Slab]
    __recycle: Callable[[], None]

    def __init__(self, level_generator: LevelGenerator) -> None:
        level = self.level_info = level_generator.generate()
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
                Slab(
                    (unit_length * i + level.length // 2, SlabLevel.GENERATE_HEIGHT), 
                    level.length, 
                    level.width, 
                    level.velocity
                )
            )

        # Set recycle condition
        if level.velocity > 0:
            boundary = GeneralConstant.DEFAULT_SCREEN_SIZE[0] + level.length // 2
            def recycle():
                if (slab := self.__slabs[-1]).entity.position.x >= boundary:
                    slab.entity.position.x -= cycle_length
                    slab.entity.reload()
                    slab.displayable.reload()
                    self.__slabs.appendleft(self.__slabs.pop())
            self.__recycle = recycle
        elif level.velocity < 0:
            boundary = - (level.length // 2)
            def recycle():
                if (slab := self.__slabs[0]).entity.position.x <= boundary:
                    slab.entity.position.x += cycle_length
                    slab.entity.reload()
                    slab.displayable.reload()
                    self.__slabs.append(self.__slabs.popleft())
            self.__recycle = recycle
        else:
            self.__recycle = lambda: None

        # Clean up
        SlabLevel.GENERATE_HEIGHT += Constant.SLAB_GAP

    def __iter__(self) -> Iterator[Slab]:
        return iter(self.__slabs)

    def tick(self, dt: float) -> None:
        for slab in self.__slabs:
            slab.entity.tick(dt)
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
    rockets: list[PhysicsRocket]
    particles: list[Particle]

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
        self.wall_left = PhysicsWall(0, Direction.RIGHT)
        self.wall_right = PhysicsWall(GeneralConstant.DEFAULT_SCREEN_SIZE[0], Direction.LEFT)
        self.slab_levels = deque()
        while SlabLevel.GENERATE_HEIGHT <= Constant.UPPER_SLAB_BOUNDARY:
            self.slab_levels.append(SlabLevel(self.__level_generator))
        self.rockets = []
        self.particles = []

    def tick(self, dt: float, bounce: bool) -> None:
        for slab_level in self.slab_levels:
            slab_level.tick(dt)
        rockets = []
        for rocket in self.rockets:
            rocket.tick(dt)
            for slab in self.slabs:
                direction, length = slab.entity.get_shrink_parameter(rocket)
                if length == 0:
                    continue
                if direction == Direction.LEFT:
                    self.particles += slab.generate_particle(
                        slab.entity.active_length_range[0] - length, 
                        rocket.position + Vector(rocket.halfsize.x, 0), 
                        slab.displayable.shrink_fromleft(length)
                    )
                elif direction == Direction.RIGHT:
                    surface = slab.displayable.shrink_fromright(length)
                    self.particles += slab.generate_particle(
                        slab.entity.active_length_range[1], 
                        rocket.position - Vector(rocket.halfsize.x, 0), 
                        surface
                    )
            if not rocket.remove:
                rockets.append(rocket)
        self.rockets = rockets
        particles = []
        bottom_y = Constant.SCREEN_BOTTOM_Y + self.reference
        for particle in self.particles:
            particle.entity.tick(dt)
            if not particle.check_removal(bottom_y):
                particles.append(particle)
        self.particles = particles
        if self.gameover:
            return
        
        self.ball.tick(
            dt,
            bounce, 
            self.objects
        )
        if self.ball.crash_on_rocket:
            self.gameover = True
            return
        if (pos_y := self.ball.position.y) + self.ball.radius <= bottom_y:
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
        self.rockets = []
        self.particles = []
        self.slab_levels = deque()
        while SlabLevel.GENERATE_HEIGHT <= Constant.UPPER_SLAB_BOUNDARY:
            self.slab_levels.append(SlabLevel(self.__level_generator))

    def generate_rocket(self, issuper: bool = False) -> None:
        level = get_level(self.ball.position.y) + (self.ball.velocity.y > 0)
        for slab_level in self.slab_levels:
            if slab_level.level == level and slab_level.level_info is not None:
                rocket_facing_left = slab_level.level_info.velocity > 0
                break
        else:
            if not self.slab_levels or (slab_level := self.slab_levels[-1]).level_info is None:
                return
            level = slab_level.level
            rocket_facing_left = slab_level.level_info.velocity > 0
        height = (level - 1) * Constant.SLAB_GAP - GeneralConstant.BALL_RADIUS
        if rocket_facing_left:
            position = (
                GeneralConstant.DEFAULT_SCREEN_SIZE[0] + Constant.ROCKET_HALFSIZE[0], 
                height
            )
            velocity_x = -Constant.SUPER_ROCKET_SPEED if issuper else -Constant.ROCKET_SPEED
        else:
            position = (-Constant.ROCKET_HALFSIZE[0], height)
            velocity_x = Constant.SUPER_ROCKET_SPEED if issuper else Constant.ROCKET_SPEED
        self.rockets.append(PhysicsRocket(position, velocity_x))
        
    def position_map(self, position: Vector) -> Vector:
        return Vector(position.x, Constant.ORIGINAL_TOP_HEIGHT + self.reference - position.y)
    
    @property
    def slabs(self) -> Generator[Slab, None, None]:
        for slab_level in self.slab_levels:
            for slab in slab_level:
                yield slab

    @property
    def objects(self) -> Generator[PhysicsObject, None, None]:
        yield self.ground
        yield self.wall_left
        yield self.wall_right
        for rocket in self.rockets:
            yield rocket
        for slab in self.slabs:
            yield slab.entity


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