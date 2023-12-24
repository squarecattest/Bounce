from vector import *
from typing import Literal as _Literal, Iterable as _Iterable
from itertools import product as _product
from math import pi as _pi

_RAD_INV = 180 / _pi

# Constant Settings
_GRAVITY = Vector(0, 960)
_BOUNCE_VELOCITY = Vector(0, -640)
_COLLISION_SCALE, _COLLISION_OFFSET = 0.6, 20
_SLIDING_F_SCALE, _SLIDING_F_OFFSET = 0.92, 0.01
_ROLLING_R_SCALE, _ROLLING_R_OFFSET = 0.99, 0.1
_WALL_REFLECT_CONSTANT = 2
_WALL_REFLECT_ALLOWED_DISTANCE = 0 #1 ?
_HANDLING_TIMES_ONCOLLISION = 3


def sign(number: NumberType) -> _Literal[-1, 0, 1]:
    '''
    Mathematical sign function.
    '''
    if number > 0: return 1
    if number < 0: return -1
    return 0

def to_degree(radian: float) -> float:
    '''
    Convert an angle from radian to degree.
    '''
    return radian * _RAD_INV

def linear_contraction(original: Vector, center: Vector, scale: float, offset: float) -> Vector:
    '''
    Map the distance between original and center by:

    distance -> scale * distance - offset

    Parameters
    ----------
    original: :class:`Vector`
        The vector to be mapped.
    center: :class:`Vector`
        The center of contraction.
    scale: :class:`float`
        The multiplier in contraction. Should be a number between 0 and 1.
    offset: :class:`float`
        The subtraction constant in contraction. Should be a positive number.
    '''
    difference = original - center
    if difference.is_zerovec:
        return center.copy()
    unit, mag = difference.unit, difference.magnitude
    mag *= scale
    if mag < offset:
        return center.copy()
    return center + unit * (mag - offset)

def wall_reflect_velocity(distance: NumberType) -> NumberType:
    '''
    Get the reflection velocity for a ball stuck in a wall. The formula is given by:

    velocity = c * (distance ** 2)

    Parameters
    ----------
    distance: :class:`NumberType`
        The distance to the wall surface.
    '''
    if distance < _WALL_REFLECT_ALLOWED_DISTANCE:
        return 0
    return _WALL_REFLECT_CONSTANT * (distance ** 2)
    
class PhysicsGround:
    '''
    The class representing physical interaction of a flat ground.

    Parameters
    ----------
    y_top: :class:`NumberType`
        The y coordinate of the surface.
    '''
    __y_top: NumberType

    def __init__(self, y_top: NumberType) -> None:
        self.__y_top = y_top

    def check_collision(self, ball: "PhysicsBall") -> Vector | None:
        '''
        Check if colliding with the ball. If the objects are colliding, return the normal 
        vector of the contact point. Return ``None`` if not colliding.
        '''
        if self.__y_top <= ball.pos_y + ball.radius:
            return Vector(0, -1)
        return None

    def check_onground(self, ball: "PhysicsBall") -> bool:
        '''
        Check if the grounded ball is still on the ground.
        '''
        return True
    
    def get_normal_vector(self, ball: "PhysicsBall") -> Vector:
        return Vector(0, -1)
    
    @property
    def position(self): return Vector(0, self.__y_top)
    @property
    def surface_y(self): return self.__y_top
    @property
    def position_y_top(self): return self.__y_top
    @property
    def position_y_top_int(self): return int(self.__y_top)
    @property
    def velocity(self): return Vector.zero


class PhysicsWall:
    '''
    The class representing physical interaction of a flat ground.

    Parameters
    ----------
    x_side: :class:`NumberType`
        The x coordinate of the surface.
    facing: ``PhysicsWall.FACING_LEFT`` or ``PhysicsWall.FACING_RIGHT``
        The facing of the wall.
    '''
    __x_side: NumberType
    __facing: bool

    def __init__(self, x_side: NumberType, facing: bool):
        self.__x_side = x_side
        self.__facing = facing

    def check_collision(self, ball: "PhysicsBall") -> Vector | None:
        '''
        Check if colliding with the ball. If the objects are colliding, return the normal 
        vector of the contact point. Return ``None`` if not colliding.
        '''
        if self.__facing == PhysicsWall.FACING_RIGHT \
            and ball.pos_x - ball.radius <= self.__x_side:
            return Vector(1, 0)
        if self.__facing == PhysicsWall.FACING_LEFT \
            and ball.pos_x + ball.radius >= self.__x_side:
            return Vector(-1, 0)
        return None
    
    def get_normal_vector(self, ball: "PhysicsBall") -> Vector:
        if self.__facing == PhysicsWall.FACING_RIGHT:
            return Vector(1, 0)
        if self.__facing == PhysicsWall.FACING_LEFT:
            return Vector(-1, 0)

    @classmethod
    @property
    def FACING_LEFT(cls):
        return False
    @classmethod
    @property
    def FACING_RIGHT(cls):
        return True
    
    @property
    def surface_x(self): return self.__x_side
    @property
    def facing(self): return self.__facing
    @property
    def velocity(self): return Vector.zero


class PhysicsSlab:
    '''
    The class representing physical interaction of a floating slab.

    Parameters
    ----------
    position: :class:`VectorType`
        The vector pointing to its initial position of center.
    size: :class:`SizeType`
        The size of the slab, in the form of an iterator of `(length, width)`.
    velocity_x: :class:`NumberType`
        The constant horizontal velocity of the slab.
    '''
    __pos: Vector
    __v: Vector
    __size: SizeType

    def __init__(self, position: VectorType, size: SizeType, velocity_x: NumberType) -> None:
        self.__pos = Vector(position)
        self.__size = tuple(size)
        self.__v = Vector(velocity_x, 0)

    def tick(self, dt: float) -> None:
        '''
        Change the position and velocity of the slab with respect to time interval `dt`. 
        Velocity is constant for a slab.
        '''
        self.__pos += self.__v * dt

    def check_collision(self, ball: "PhysicsBall") -> Vector | None:
        '''
        Check if colliding with the ball. If the objects are colliding, return the normal 
        vector of the contact point. Return ``None`` if not colliding.
        '''
        x_range = self.__pos.x - self.__size[0] // 2, self.__pos.x + self.__size[0] // 2
        y_range = self.__pos.y - self.__size[1] // 2, self.__pos.y + self.__size[1] // 2

        # Check sides
        if x_range[0] <= ball.pos_x <= x_range[1]:
            if y_range[0] <= ball.pos_y + ball.radius <= y_range[1]:
                return Vector(0, -1)
            if y_range[0] <= ball.pos_y - ball.radius <= y_range[1]:
                return Vector(0, 1)
        if y_range[0] <= ball.pos_y <= y_range[1]:
            if x_range[0] <= ball.pos_x + ball.radius <= x_range[1]:
                return Vector(-1, 0)
            if x_range[0] <= ball.pos_x - ball.radius <= x_range[1]:
                return Vector(1, 0)

        # Check corners
        ball_pos = ball.position
        for x, y in _product(x_range, y_range):
            if (vec := ball_pos - Vector(x, y)).magnitude <= ball.radius:
                return vec

        # Not colliding
        return None
    
    def check_onground(self, ball: "PhysicsBall") -> bool:
        '''
        Check if the grounded ball is still on the ground.
        '''
        return self.__pos.x - self.__size[0] // 2 <= ball.pos_x \
            <= self.__pos.x + self.__size[0] // 2
    
    def get_normal_vector(self, ball: "PhysicsBall") -> Vector:
        '''
        To be documented
        '''
        return Vector(0, -1)

    @property
    def position(self): return self.__pos.copy()
    @property
    def surface_y(self): return self.__pos.y - self.__size[1] // 2
    @property
    def size(self): return self.__size
    @property
    def velocity(self): return self.__v.copy()


class PhysicsBall:
    '''
    The class represents physical interaction of a ball.

    Parameters
    ----------
    position: :class:`VectorType`
        The vector pointing to its initial position of center.
    radius: :class:`LengthType`
        The radius of the ball.
    '''
    __pos: Vector
    __angle: NumberType
    __v: Vector
    __w: NumberType # angular velocity
    __radius: LengthType
    __onground: bool
    __ground: PhysicsGround | PhysicsSlab | None

    def __init__(self, position: VectorType, radius: LengthType) -> None:
        assert isVector(position)
        assert isPosNumber(radius)
        self.__pos = Vector(position)
        self.__angle = 0
        self.__v = Vector.zero
        self.__w = 0
        self.__radius = radius
        self.__onground = False
        self.__ground = None

    def tick(
            self, 
            dt: float, 
            objs: _Iterable[PhysicsGround | PhysicsSlab], 
            *, 
            bounce: bool
        ) -> None:
        '''
        To be documented
        '''
        self.__pos += self.__v * dt
        self.__angle += self.__w * dt
        obj_exceptions = []
        if not self.__onground:
            self.__v += _GRAVITY * dt
        elif not self.__ground.check_onground(self):
            self.__v += _GRAVITY * dt
            self.__onground = False
            self.__ground = None
        else:
            obj_exceptions.append(self.__ground)
            self.handle_friction()
            if bounce:
                self.bounce()
        self.detect_collision(objs, obj_exceptions)

    def bounce(self) -> None:
        '''
        Apply a bounce on the ball. If the ball is not on ground, there will be no effect.
        '''
        if not self.__onground:
            return
        self.__v += _BOUNCE_VELOCITY
        self.__onground = False
        self.__ground = None

    def detect_collision(
            self, 
            objs: _Iterable[PhysicsGround | PhysicsSlab], 
            obj_exceptions: _Iterable[PhysicsGround | PhysicsSlab]
        ) -> None:
        '''
        To be documented
        '''
        for obj in objs:
            if obj in obj_exceptions:
                continue
            if (collision_vector := obj.check_collision(self)) is not None:
                self.collide(obj.velocity, collision_vector, obj)
                self.handle_friction(
                    obj.velocity, 
                    collision_vector, 
                    times=_HANDLING_TIMES_ONCOLLISION
                )

    def collide(
            self, 
            surface_velocity: Vector, 
            surface_normal: Vector, 
            surface: PhysicsGround | PhysicsSlab
        ) -> None:
        '''
        Apply the given collision to the ball.
    
        surface_velocity: :class:`Vector`
            The velocity of the surface which the ball collides with.
        surface_normal: :class:`Vector`
            The normal vector of the surface at the contact point. Should be pointing outward.
        surface: :class:`PhysicsGround | PhysicsSlab`
            The object which the ball collides with. Used as a possible ground for the ball.
        '''
        rel_velocity = self.__v - surface_velocity
        rel_normal_velocity = rel_velocity.project_on(surface_normal)
        rel_tangent_velocity = rel_velocity - rel_normal_velocity

        if rel_normal_velocity * surface_normal > 0:
            return
        rel_normal_velocity = linear_contraction(
            -rel_normal_velocity, Vector.zero, _COLLISION_SCALE, _COLLISION_OFFSET
        )
        if rel_normal_velocity.is_zerovec and surface_normal == (0, -1):
            self.__onground = True
            self.__ground = surface
            self.__pos.y = surface.surface_y - self.__radius
        self.__v = surface_velocity + rel_tangent_velocity + rel_normal_velocity
        if isinstance(surface, PhysicsWall):
            self.wall_stuck_removal(surface)

    def wall_stuck_removal(self, wall: PhysicsWall):
        if self.__onground:
            if wall.facing == PhysicsWall.FACING_RIGHT:
                self.__pos.x = wall.surface_x + self.__radius
            else:
                self.__pos.x = wall.surface_x - self.__radius
            return
        if wall.facing == PhysicsWall.FACING_RIGHT:
            self.__v.x = max(
                self.__v.x,
                wall_reflect_velocity(wall.surface_x - self.__pos.x + self.__radius)
            )
        else:
            self.__v.x = min(
                self.__v.x,
                -wall_reflect_velocity(wall.surface_x - self.__pos.x - self.__radius)
            )

    def handle_friction(
            self, 
            surface_velocity: Vector = None, 
            surface_normal: Vector = None, 
            *, 
            times: int = 1
        ) -> None:
        '''
        Apply the simulated friction within a tick to the ball. If the ball is on the ground, 
        the surface parameters need not be passed.
    
        surface_velocity: :class:`Vector`
            The velocity of the surface.
        surface_normal: :class:`Vector`
            The normal vector of the surface at the contact point. Should be pointing outward.
        times: :class:`int`
            The times of sliding friction applied.
        '''
        if self.__onground:
            surface_velocity = self.__ground.velocity
            surface_normal = self.__ground.get_normal_vector(self)
        
        surface_tangent = Vector(-surface_normal[1], surface_normal[0]).unit
        surface_projected_velocity = surface_velocity.project_on(surface_tangent)
        projected_velocity = self.__v.project_on(surface_tangent)
        normal_velocity = self.__v - projected_velocity

        # Change to relative inertial frame of reference
        rel_linear_velocity = surface_projected_velocity - projected_velocity
        rel_rolling_velocity = surface_tangent * self.__w * self.__radius
        rel_average_velocity = (rel_linear_velocity + rel_rolling_velocity) / 2

        # Sliding friction
        for _ in range(times):
            rel_linear_velocity = linear_contraction(
                rel_linear_velocity, rel_average_velocity, _SLIDING_F_SCALE, _SLIDING_F_OFFSET
            )
            rel_rolling_velocity = linear_contraction(
                rel_rolling_velocity, rel_average_velocity, _SLIDING_F_SCALE, _SLIDING_F_OFFSET
            )
        
        # Rolling friction / Rolling resistence
        rel_linear_velocity = linear_contraction(
            rel_linear_velocity, Vector.zero, _ROLLING_R_SCALE, _ROLLING_R_OFFSET
        )
        rel_rolling_velocity = linear_contraction(
            rel_rolling_velocity, Vector.zero, _ROLLING_R_SCALE, _ROLLING_R_OFFSET
        )

        # Change back to the normal frame of reference
        self.__v = surface_projected_velocity - rel_linear_velocity + normal_velocity
        self.__w = rel_rolling_velocity.magnitude * sign(rel_rolling_velocity * surface_tangent) \
            / self.radius
        
    def temp(self, surface: PhysicsGround):
        self.__onground = True
        self.__ground = surface
    def vel(self, v, w):
        self.__v = Vector(v, 0)
        self.__w = w

    @property
    def position(self): return self.__pos.copy()
    @property
    def position_int(self): return IntVector(self.__pos)
    @property
    def pos_x(self): return self.__pos.x
    @property
    def pos_y(self): return self.__pos.y
    @property
    def angle(self): return self.__angle
    @property
    def radius(self): return self.__radius