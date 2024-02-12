from __future__ import annotations
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
from data import Achievement, Datas
from errorlog import log
from constants import GeneralConstant, GameConstant as Constant, DataConstant
from resources import Texture, Color
from utils import Direction, LinkedList, Timer, Ticker, Chance, LinearRange
from abc import ABC, abstractmethod
from collections import deque
from itertools import product
from random import uniform
from json import load as jsonload
from typing import Literal, NamedTuple, Callable, Iterable, Iterator, Generator

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
    
def entity_converter(
    object_group: LinkedList[GameObject]
) -> Generator[PhysicsObject, None, None]:
    for object in object_group.data_iter:
        yield object.entity


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


class Ground(GameObject):
    entity: PhysicsGround
    displayable: Displayable

    def __init__(self) -> None:
        self.entity = PhysicsGround(Constant.GROUND_Y)
        self.displayable = Displayable(
            Texture.GROUND, 
            Alignment(
                Alignment.Mode.CENTERED, 
                Alignment.Mode.TOP, 
                Alignment.Flag.FILL, 
                Alignment.Flag.REFERENCED, 
                facing=Alignment.Facing.DOWN, 
                offset=GeneralConstant.SCREEN_OFFSET
            )
        )

    def tick(self, dt: float) -> None:
        pass

    def display(self, center_screen: Surface, position_map: Callable[[Vector], Vector]) -> None:
        self.displayable.display(center_screen, position_map(self.entity.position))


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
        rocket: "Rocket", 
        particle_group: ParticleGroup
    ) -> None:
        direction, length = self.entity.get_shrink_parameter(rocket_entity := rocket.entity)
        if length == 0:
            return
        if direction == Direction.LEFT:
            particle_group.extend(
                self.generate_particle(
                    self.entity.active_length_range[0] - length, 
                    rocket_entity.position + Vector(rocket_entity.halfsize.x, 0), 
                    self.displayable.shrink_fromleft(length)
                )
            )
        elif direction == Direction.RIGHT:
            surface = self.displayable.shrink_fromright(length)
            particle_group.extend(
                self.generate_particle(
                    self.entity.active_length_range[1], 
                    rocket_entity.position - Vector(rocket_entity.halfsize.x, 0), 
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
        new_surface.fill(Color.TRANSPARENT_COLORKEY)
        new_surface.set_colorkey(Color.TRANSPARENT_COLORKEY)
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
                    (position - rocket_head) * Constant.SLAB_PARTICLE_OFFSET_SPEED
                    + Vector(
                        uniform(
                            -Constant.SLAB_PARTICLE_RANDOM_SPEED, 
                            Constant.SLAB_PARTICLE_RANDOM_SPEED
                        ), 
                        uniform(
                            -Constant.SLAB_PARTICLE_RANDOM_SPEED, 
                            Constant.SLAB_PARTICLE_RANDOM_SPEED
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
            offset=GeneralConstant.SCREEN_OFFSET
        )
    )

    def __init__(self, position: Vector, velocity_x: NumberType, issuper: bool) -> None:
        self.entity = PhysicsRocket(position, velocity_x)
        self.displayable = (
            Rocket.__left_displayable 
            if self.entity.facing == Direction.LEFT
            else Rocket.__right_displayable
        )
        self.issuper = issuper

    def tick(self, dt: float) -> None:
        self.entity.tick(dt)
    
    def display(self, center_screen: Surface, position_map: Callable[[Vector], Vector]) -> None:
        self.displayable.display(center_screen, position_map(self.entity.position))


class RocketGroup(LinkedList[Rocket]):
    def tick(self, dt: float) -> Rocket | None:
        removed = None
        for node in self.node_iter:
            node.data.tick(dt)
            if node.data.entity.remove:
                if node.data.issuper:
                    removed = node.data
                self.pop(node)
        return removed
    
    def display(self, center_screen: Surface, position_map: Callable[[Vector], Vector]) -> None:
        for rocket in self.data_iter:
            rocket.display(center_screen, position_map)


class Ball(GameObject):
    entity: PhysicsBall
    displayable: DisplayableBall
    remove: bool

    def __init__(
        self, 
        position: VectorType, 
        type: Literal["normal", "unbounceable", "event"]
    ) -> None:
        self.entity = PhysicsBall(position, GeneralConstant.BALL_RADIUS)
        if type == "normal":
            self.displayable = DisplayableBall(
                Texture.BALL_FRAME, 
                Texture.BALL_SURFACE, 
                Alignment(
                    Alignment.Mode.CENTERED, 
                    Alignment.Mode.CENTERED, 
                    Alignment.Flag.REFERENCED, 
                    offset=GeneralConstant.SCREEN_OFFSET
                )
            )
        elif type == "unbounceable":
            self.displayable = DisplayableBall(
                Texture.BALL_FRAME_UNBOUNCEABLE, 
                Texture.BALL_SURFACE, 
                Alignment(
                    Alignment.Mode.CENTERED, 
                    Alignment.Mode.CENTERED, 
                    Alignment.Flag.REFERENCED, 
                    offset=GeneralConstant.SCREEN_OFFSET
                )
            )
        else:
            self.displayable = DisplayableBall(
                Texture.BALL_FRAME_EVENT, 
                Texture.BALL_SURFACE_EVENT, 
                Alignment(
                    Alignment.Mode.CENTERED, 
                    Alignment.Mode.CENTERED, 
                    Alignment.Flag.REFERENCED, 
                    offset=GeneralConstant.SCREEN_OFFSET
                )
            )
        self.remove = False

    def tick(
        self, 
        dt: float, 
        bounce: bool, 
        *objs: Iterable[PhysicsObject], 
        particle_group: ParticleGroup
    ) -> bool:
        collided = self.entity.tick(dt, bounce, *objs)
        if self.entity.crash_on_rocket:
            particle_group.extend(self.generate_particle())
            self.remove = True
        return collided

    def display(self, center_screen: Vector, position_map: Callable[[Vector], Vector]) -> None:
        self.displayable.display(
            center_screen, 
            position_map(self.entity.position), 
            self.entity.deg_angle
        )

    def check_removal(self, bottom_y: NumberType) -> bool:
        return self.remove or self.entity.position.y + self.entity.radius <= bottom_y

    def generate_particle(self) -> list[Particle]:
        original_surface_size = self.displayable.surface.get_size()
        unit_range = (
            (original_surface_size[0] - 1) // Constant.UNIT_PARTICLE_SIZE + 1, 
            (original_surface_size[1] - 1) // Constant.UNIT_PARTICLE_SIZE + 1
        )
        surface_size = (
            Constant.UNIT_PARTICLE_SIZE * unit_range[0], 
            Constant.UNIT_PARTICLE_SIZE * unit_range[1]
        )
        new_surface = Surface(surface_size)
        new_surface.fill(Color.TRANSPARENT_COLORKEY)
        new_surface.set_colorkey(Color.TRANSPARENT_COLORKEY)
        new_surface.blit(self.displayable.surface, (0, 0))
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
                    (position - self.entity.position) * Constant.BALL_PARTICLE_OFFSET_SPEED
                    + Vector(
                        uniform(
                            -Constant.BALL_PARTICLE_RANDOM_SPEED, 
                            Constant.BALL_PARTICLE_RANDOM_SPEED
                        ), 
                        uniform(
                            -Constant.BALL_PARTICLE_RANDOM_SPEED, 
                            Constant.BALL_PARTICLE_RANDOM_SPEED
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
            log(e)
            return
        if not isinstance(levels, list):
            self.set_default()
            log(LevelGenerator.ParserError("Expected an array for the level file"))
            return
        for level in levels:
            self.__levels.append(parse(level, length))
            length += 1
        self.__length = length
        if error_args:
            log(LevelGenerator.ParserError("".join(error_args)))

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


class BallStatus(NamedTuple):
    time: float
    position: Vector
    velocity: Vector
    angular_frequency: NumberType
    level: int
    ground: PhysicsObject | None
    bounceable: bool

    @classmethod
    def record(cls, game: Game) -> BallStatus:
        return cls(
            time=game.timer.read(), 
            position=game.ball.entity.position, 
            velocity=game.ball.entity.velocity, 
            angular_frequency=game.ball.entity.angular_frequency, 
            level=get_level(game.ball.entity.position.y), 
            ground=game.ball.entity.ground, 
            bounceable=game.ball.entity.bounceable
        )
        

class Game:
    class RocketEvent:
        def __init__(self, game: Game) -> None:
            self.game = game
            self.ticker = Ticker(
                Constant.EVENT_ROCKET_TICK, 
                False, 
                Constant.EVENT_ROCKET_COOLDOWNS[0]
            )
            self.chance_generator = LinearRange(
                Constant.EVENT_ROCKET_LEVELS[0], 
                Constant.EVENT_ROCKET_LEVELS[1], 
                Constant.EVENT_ROCKET_CHANCES[0], 
                Constant.EVENT_ROCKET_CHANCES[1]
            )
            self.cooldown_generator = LinearRange(
                Constant.EVENT_ROCKET_LEVELS[0], 
                Constant.EVENT_ROCKET_LEVELS[1], 
                Constant.EVENT_ROCKET_COOLDOWNS[0], 
                Constant.EVENT_ROCKET_COOLDOWNS[1]
            )

        def start(self) -> None:
            self.ticker.skip_cooldown()

        def reload(self) -> None:
            self.ticker = Ticker(
                Constant.EVENT_ROCKET_TICK, 
                False, 
                Constant.EVENT_ROCKET_COOLDOWNS[0]
            )

        def tick(self) -> None:
            if self.ticker.tick() and Chance(self.chance_generator.get_value(self.game.level)):
                self.generate(
                    self.game.level >= Constant.EVENT_ROCKET_LEVELS[1]
                    and Chance(Constant.EVENT_SUPERROCKET_CHANCE)
                )
                self.ticker = Ticker(
                    Constant.EVENT_ROCKET_TICK, 
                    True, 
                    self.cooldown_generator.get_value(self.game.level)
                )

        def force_tick(self) -> None:
            self.generate(
                self.game.level >= Constant.EVENT_ROCKET_LEVELS[1]
                and bool(Chance(Constant.EVENT_SUPERROCKET_CHANCE))
            )
            self.ticker = Ticker(
                Constant.EVENT_ROCKET_TICK, 
                True, 
                self.cooldown_generator.get_value(self.game.level)
            )

        def generate(self, issuper: bool) -> None:
            level = self.game.level + (self.game.ball.entity.velocity.y > 0)
            for slab_level in self.game.slab_levels:
                if slab_level.level == level and slab_level.level_info is not None:
                    rocket_facing_left = slab_level.level_info.velocity > 0
                    break
            else:
                if (
                    not self.game.slab_levels 
                    or (slab_level := self.game.slab_levels[-1]).level_info is None
                ):
                    return
                level = slab_level.level
                rocket_facing_left = slab_level.level_info.velocity > 0
            height = (level - 1) * Constant.SLAB_GAP + Constant.GROUND_Y
            if rocket_facing_left:
                position = (
                    GeneralConstant.DEFAULT_SCREEN_SIZE[0] + Constant.ROCKET_HALFSIZE[0], 
                    height
                )
                velocity_x = -Constant.SUPER_ROCKET_SPEED if issuper else -Constant.ROCKET_SPEED
            else:
                position = (-Constant.ROCKET_HALFSIZE[0], height)
                velocity_x = Constant.SUPER_ROCKET_SPEED if issuper else Constant.ROCKET_SPEED
            self.game.rockets.append(Rocket(position, velocity_x, issuper))

        @property
        def active(self) -> bool:
            return self.ticker.running
        
    class FallingBallEvent:
        def __init__(self, game: Game) -> None:
            self.game = game
            self.ticker = Ticker(
                Constant.EVENT_FALLING_BALL_TICK, 
                False, 
                Constant.EVENT_FALLING_BALL_COOLDOWN
            )
            self.chance_generator = LinearRange(
                Constant.EVENT_FALLING_BALL_LEVELS[0], 
                Constant.EVENT_FALLING_BALL_LEVELS[1], 
                Constant.EVENT_FALLING_BALL_CHANCES[0], 
                Constant.EVENT_FALLING_BALL_CHANCES[1]
            )

        def start(self) -> None:
            self.ticker.skip_cooldown()

        def reload(self) -> None:
            self.ticker.stop()

        def tick(self) -> None:
            if self.ticker.tick() and Chance(self.chance_generator.get_value(self.game.level)):
                self.generate()
                self.ticker.restart()
                if (
                    not self.game.rocket_event.ticker.in_cooldown 
                    and Chance(Constant.EVENT_UNION_SPAWN_CHANCE)
                ):
                    self.game.rocket_event.force_tick()

        def generate(self) -> None:
            y = self.game.reference + Constant.ORIGINAL_TOP_HEIGHT
            for i in range(1, Constant.FALLING_BALLS + 1):
                self.game.event_balls.append(
                    Ball(Vector(i * Constant.FALLING_BALL_SEP, y), "event")
                )

        @property
        def active(self) -> bool:
            return self.ticker.running
    
    class AchievementTracer:
        def __init__(self, game: Game) -> None:
            self.game = game
            self.current = None
            self.max_height = None
            self.last_bounce = None
            self.last_collision = None
            self.last_bounceable = None
            self.continuous_bounce = None
            self.long_stay = None
            self.high_speed_rocket_height: NumberType | None = None

        def record(self, bounce: bool, collided: bool) -> None:
            self.current = status = BallStatus.record(self.game)
            if self.max_height is None or self.max_height.position.y < status.position.y:
                self.max_height = status
            if bounce:
                if (
                    self.last_bounce is None
                    or status.level <= self.last_bounce.level
                ):
                    self.continuous_bounce = status
                self.last_bounce = status
            if collided:
                self.last_collision = status
            if status.bounceable:
                self.last_bounceable = status
            if (
                status.level != 1
                and (self.long_stay is None or status.level != self.long_stay.level)
            ):
                self.long_stay = status
            elif status.level == 1:
                self.long_stay = None

        def reload(self) -> None:
            self.__init__(self.game)

        def check_achievements(self) -> list[Achievement]:
            def add(achievement: Achievement) -> None:
                Datas.achievement |= achievement
                achievements.append(achievement)
            
            achievements = []
            if (
                Achievement.low_onground not in Datas.achievement
                and isinstance(self.current.ground, PhysicsSlab)
                and self.max_height.position.y - GeneralConstant.BALL_RADIUS <= 
                    self.current.ground.y_top + 10
            ):
                add(Achievement.low_onground)
            if (
                Achievement.continuous_bounce not in Datas.achievement
                and self.continuous_bounce is not None
                and self.current.level - self.continuous_bounce.level 
                    >= DataConstant.Achievement.CONTINUOUS_BOUNCE_LEVELS
            ):
                add(Achievement.continuous_bounce)
            if (
                Achievement.long_stay not in Datas.achievement
                and self.long_stay is not None
                and self.current.time - self.long_stay.time >=
                    DataConstant.Achievement.LONG_STAY_SECONDS
            ):
                add(Achievement.long_stay)
            if (
                Achievement.fast_rotation not in Datas.achievement
                and abs(self.current.angular_frequency) >= 
                    DataConstant.Achievement.FAST_ROTATION_FREQUENCY
            ):
                add(Achievement.fast_rotation)
            if (
                Achievement.free_fall not in Datas.achievement
                and self.game.gameover
                and self.last_bounceable is not None
                and self.last_bounceable.level - self.current.level >=
                    DataConstant.Achievement.FREE_FALL_LEVELS
            ):
                add(Achievement.free_fall)
            if (
                Achievement.bounce_high not in Datas.achievement
                and self.current.position.y >= DataConstant.Achievement.BOUNCE_HIGH_HEIGHT
            ):
                add(Achievement.bounce_high)
            if (
                Achievement.avoid_high_speed_rocket not in Datas.achievement
                and not self.game.gameover
                and self.high_speed_rocket_height is not None
                and self.current.position.y >= self.high_speed_rocket_height
            ):
                add(Achievement.avoid_high_speed_rocket)
            self.high_speed_rocket_height = None
            return achievements
    
    timer: Timer
    reference: NumberType
    max_height: NumberType
    gameover: bool
    ball: Ball
    ball_unbounceable: Ball
    ground: Ground
    wall_left: PhysicsWall
    wall_right: PhysicsWall
    slab_levels: deque[SlabLevel]
    event_balls: BallGroup
    rockets: RocketGroup
    particles: ParticleGroup
    new_achievements: deque[Achievement]

    def __init__(self, level_filepath: str) -> None:
        self.__level_generator = LevelGenerator(level_filepath)
        self.timer = Timer()
        self.reference = 0
        self.level = 1
        self.max_height = 0
        self.gameover = False
        self.ball = Ball((GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 0), "normal")
        self.ball_unbounceable = Ball((0, 0), "unbounceable")
        self.ball_unbounceable.entity = self.ball.entity
        self.ground = Ground()
        self.wall_left = PhysicsWall(0, Direction.RIGHT)
        self.wall_right = PhysicsWall(GeneralConstant.DEFAULT_SCREEN_SIZE[0], Direction.LEFT)
        self.slab_levels = deque()
        while SlabLevel.GENERATE_HEIGHT <= Constant.UPPER_SLAB_BOUNDARY:
            self.slab_levels.append(SlabLevel(self.__level_generator))
        self.event_balls = BallGroup()
        self.rockets = RocketGroup()
        self.particles = ParticleGroup()
        self.rocket_event = Game.RocketEvent(self)
        self.falling_ball_event = Game.FallingBallEvent(self)
        self.achievement_tracer = Game.AchievementTracer(self)
        self.new_achievements = deque()

    def tick(self, dt: float, bounce: bool) -> None:
        if bounce:
            self.timer.start()
        bottom_y = Constant.SCREEN_BOTTOM_Y + self.reference
        for slab_level in self.slab_levels:
            slab_level.tick(dt)
        if (removed_super_rocket := self.rockets.tick(dt)) is not None:
            self.achievement_tracer.high_speed_rocket_height = \
                removed_super_rocket.entity.position.y
        self.particles.tick(dt, bottom_y)
        self.event_balls.tick(
            dt, 
            (self.ground.entity, self.wall_left, self.wall_right, self.ball.entity), 
            tuple(self.physics_slabs), 
            tuple(entity_converter(self.rockets)), 
            tuple(entity_converter(self.event_balls)), 
            particle_group=self.particles, 
            bottom_y=bottom_y
        )
        for slab in self.slabs:
            for rocket in self.rockets.data_iter:
                slab.check_rocket_collision(rocket, self.particles)
        if not self.gameover:
            collided = self.ball.tick(
                dt, 
                bounce, 
                (self.ground.entity, self.wall_left, self.wall_right), 
                self.physics_slabs, 
                entity_converter(self.rockets), 
                entity_converter(self.event_balls), 
                particle_group=self.particles
            )
            self.achievement_tracer.record(bounce, collided)
            if self.ball.check_removal(bottom_y):
                self.gameover = True
                self.timer.pause()
            self.level = get_level(self.ball.entity.position.y)
            if self.level >= Constant.EVENT_ROCKET_LEVELS[0]:
                if not self.rocket_event.active:
                    self.rocket_event.start()
                else:
                    self.rocket_event.tick()
            if self.level >= Constant.EVENT_FALLING_BALL_LEVELS[0]:
                if not self.falling_ball_event.active:
                    self.falling_ball_event.start()
                else:
                    self.falling_ball_event.tick()

        self.new_achievements.extend(self.achievement_tracer.check_achievements())
        if self.gameover:
            return
        if (pos_y := self.ball.entity.position.y) + self.ball.entity.radius <= bottom_y:
            self.gameover = True
            return
        if (pos_y := self.ball.entity.position.y) > self.max_height:
            self.max_height = pos_y
        if (reference := pos_y - Constant.TRACE_HEIGHT) > self.reference:
            self.reference = reference
            while (
                self.slab_levels
                and self.slab_levels[0].height <= reference + Constant.LOWER_SLAB_BOUNDARY
            ):
                self.slab_levels.popleft()
            while SlabLevel.GENERATE_HEIGHT <= reference + Constant.UPPER_SLAB_BOUNDARY:
                self.slab_levels.append(SlabLevel(self.__level_generator))

    def display(self, center_screen: Surface, debugging: bool) -> None:
        self.ground.display(center_screen, self.position_map)
        for slab in self.slabs:
            slab.display(center_screen, self.position_map)
        self.rockets.display(center_screen, self.position_map)
        self.event_balls.display(center_screen, self.position_map)
        if not self.gameover:
            if debugging and not self.ball.entity.bounceable:
                self.ball_unbounceable.display(center_screen, self.position_map)
            else:
                self.ball.display(center_screen, self.position_map)
        self.particles.display(center_screen, self.position_map)

    def restart(self) -> None:
        self.__level_generator.reload()
        SlabLevel.reload()
        self.timer.stop()
        self.reference = 0
        self.max_height = 0
        self.level = 1
        self.gameover = False
        self.ball = Ball((GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 0), "normal")
        self.ball_unbounceable = Ball((0, 0), "unbounceable")
        self.ball_unbounceable.entity = self.ball.entity
        self.event_balls = BallGroup()
        self.rockets = RocketGroup()
        self.particles = ParticleGroup()
        self.slab_levels = deque()
        while SlabLevel.GENERATE_HEIGHT <= Constant.UPPER_SLAB_BOUNDARY:
            self.slab_levels.append(SlabLevel(self.__level_generator))
        self.rocket_event.reload()
        self.falling_ball_event.reload()
        self.achievement_tracer.reload()

    def revive(self) -> None:
        self.gameover = False
        self.ball.remove = False
        self.ball.entity.position.x = GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2
        self.ball.entity.position.y = self.reference + Constant.TRACE_HEIGHT
        self.ball.entity.velocity.x = 0
        self.ball.entity.velocity.y = 0
        self.ball.entity.set_onground(False)
        self.timer.start()

    def read_new_achievement(self) -> Achievement | None:
        if self.new_achievements:
            return self.new_achievements.popleft()
        return None
        
    def position_map(self, position: Vector) -> Vector:
        return Vector(position.x, Constant.ORIGINAL_TOP_HEIGHT + self.reference - position.y)
    
    @property
    def slabs(self) -> Generator[Slab, None, None]:
        for slab_level in self.slab_levels:
            for slab in slab_level:
                yield slab
    
    @property
    def physics_slabs(self) -> Generator[PhysicsSlab, None, None]:
        for slab_level in self.slab_levels:
            for slab in slab_level:
                yield slab.entity