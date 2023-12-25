from vector import *
from abc import ABC as _ABC, abstractmethod as _abstractmethod
from typing import Literal as _Literal, Iterable as _Iterable
from itertools import product as _product
from math import pi as _pi

_RAD_INV = 180 / _pi

# Constant Settings
_GRAVITY = Vector(0, 1960)
_BOUNCE_VELOCITY = -960
_COLLISION_SCALE, _COLLISION_OFFSET = 0.6, 20
_SLIDING_F_SCALE, _SLIDING_F_OFFSET = 0.92, 0.01
_ROLLING_R_SCALE, _ROLLING_R_OFFSET = 0.99, 0.1
_WALL_REFLECT_VELOCITY_CONSTANT = 2
_WALL_REFLECT_ALLOWED_DISTANCE = 0 #1 ?
_MAX_BOUNCABLE_DISTANCE = 20
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
    return _WALL_REFLECT_VELOCITY_CONSTANT * (distance ** 2)


class PhysicsObject(_ABC):
    '''
    The meta class representing physical interaction of an object.
    '''
    @_abstractmethod
    def check_collision(self, ball: "PhysicsBall") -> Vector | None:
        '''
        Check if colliding with the ball.

        Parameters
        ----------
        ball: :class:`PhysicsBall`
            The ball to be checked.

        Returns
        -------
        Optional[:class:`Vector`]
            The normal vector of the contact point. Returns ``None`` if not colliding.
        '''
        pass
    
    @_abstractmethod
    def update_onground(self, ball: "PhysicsBall") -> bool:
        '''
        Check if the on-ground ball is still on this object. Notice that a bounce will 
        automatically remove the on-ground property, so this method only need to check about 
        falling.

        Parameters
        ----------
        ball: :class:`PhysicsBall`
            The ball to be checked.
        '''
        pass
    
    @_abstractmethod
    def get_normal_vector(self, ball: "PhysicsBall") -> Vector:
        '''
        Get the normal vector of the contact point.

        Parameters
        ----------
        ball: :class:`PhysicsBall`
            The contacting ball on this object.

        Returns
        -------
        :class:`Vector`
            The normal vector of the contact point.
        '''
        pass
    
    @property
    @_abstractmethod
    def velocity(self) -> Vector:
        pass


class PhysicsGround(PhysicsObject):
    '''
    The class representing physical interaction of a flat ground.
    '''
    __y_top: NumberType

    def __init__(self, y_top: NumberType) -> None:
        '''
        Parameters
        ----------
        y_top: :class:`NumberType`
            The y coordinate of the surface.
        '''
        self.__y_top = y_top

    def check_collision(self, ball: "PhysicsBall") -> Vector | None:
        if self.__y_top <= ball.pos_y + ball.radius:
            return Vector.unit_upward
        return None

    def update_onground(self, ball: "PhysicsBall") -> bool:
        return True
    
    def get_normal_vector(self, ball: "PhysicsBall") -> Vector:
        return Vector.unit_upward

    @property
    def y_top(self) -> NumberType:
        '''
        (Read-only) The y coordinate of the surface.
        '''
        return self.__y_top
    
    @property
    def velocity(self) -> Vector:
        '''
        (Read-only) The velocity of the ground. Always a zero vector.
        '''
        return Vector.zero


class PhysicsWall(PhysicsObject):
    '''
    The class representing physical interaction of a flat ground.
    '''
    __x_side: NumberType
    __facing: bool

    @classmethod
    @property
    def FACING_LEFT(cls):
        return False
    @classmethod
    @property
    def FACING_RIGHT(cls):
        return True
    
    def __init__(self, x_side: NumberType, facing: bool):
        '''
        Parameters
        ----------
        x_side: :class:`NumberType`
            The x coordinate of the surface.
        facing: ``PhysicsWall.FACING_LEFT`` or ``PhysicsWall.FACING_RIGHT``
            The facing of the wall.
        '''
        self.__x_side = x_side
        self.__facing = facing

    def check_collision(self, ball: "PhysicsBall") -> Vector | None:
        if self.__facing == PhysicsWall.FACING_RIGHT \
            and ball.pos_x - ball.radius <= self.__x_side:
            return Vector.unit_rightward
        if self.__facing == PhysicsWall.FACING_LEFT \
            and ball.pos_x + ball.radius >= self.__x_side:
            return Vector.unit_leftward
        return None
    
    def get_normal_vector(self, ball: "PhysicsBall") -> Vector:
        if self.__facing == PhysicsWall.FACING_RIGHT:
            return Vector.unit_rightward
        if self.__facing == PhysicsWall.FACING_LEFT:
            return Vector.unit_leftward
    
    @property
    def x_side(self) -> NumberType:
        '''
        (Read-only) The x coordinate of the surface.
        '''
        return self.__x_side
    
    @property
    def facing(self) -> bool:
        '''
        (Read-only) The facing of the wall.
        '''
        return self.__facing
    
    @property
    def velocity(self) -> Vector:
        '''
        (Read-only) The velocity of the wall. Always a zero vector.
        '''
        return Vector.zero


class PhysicsSlab(PhysicsObject):
    '''
    The class representing physical interaction of a floating slab.
    '''
    __pos: Vector
    __v: Vector
    __size: tuple[int, int]

    def __init__(self, position: VectorType, size: SizeType, velocity_x: NumberType) -> None:
        '''
        Parameters
        ----------
        position: :class:`VectorType`
            The vector-like initial position of its center.
        size: :class:`SizeType`
            The size of the slab, in the form of an iterator of `(length, width)`.
        velocity_x: :class:`NumberType`
            The constant horizontal velocity of the slab.
        '''
        self.__pos = Vector(position)
        self.__v = Vector(velocity_x, 0)
        self.__size = tuple(size)

    def tick(self, dt: float) -> None:
        '''
        Change the position and velocity of the slab with respect to time interval `dt`. 
        Velocity is constant for a slab.
        '''
        self.__pos += self.__v * dt

    def check_collision(self, ball: "PhysicsBall") -> Vector | None:
        x_range = self.__pos.x - self.__size[0] // 2, self.__pos.x + self.__size[0] // 2
        y_range = self.__pos.y - self.__size[1] // 2, self.__pos.y + self.__size[1] // 2

        # Check sides
        if x_range[0] <= ball.pos_x <= x_range[1]:
            if y_range[0] <= ball.pos_y + ball.radius <= y_range[1]:
                return Vector.unit_upward
            if y_range[0] <= ball.pos_y - ball.radius <= y_range[1]:
                return Vector.unit_downward
        if y_range[0] <= ball.pos_y <= y_range[1]:
            if x_range[0] <= ball.pos_x + ball.radius <= x_range[1]:
                return Vector.unit_leftward
            if x_range[0] <= ball.pos_x - ball.radius <= x_range[1]:
                return Vector.unit_rightward

        # Check corners
        ball_pos = ball.position
        for x, y in _product(x_range, y_range):
            if (vec := ball_pos - Vector(x, y)).magnitude <= ball.radius:
                return vec

        # Not colliding
        return None
    
    def update_onground(self, ball: "PhysicsBall") -> bool:
        return self.__pos.x - self.__size[0] // 2 <= ball.pos_x \
            <= self.__pos.x + self.__size[0] // 2
    
    def get_normal_vector(self, ball: "PhysicsBall") -> Vector:
        return Vector(0, -1)

    @property
    def position(self) -> Vector: 
        '''
        (Read-only) The position vector of the slab.
        '''
        return self.__pos.copy()

    @property
    def y_top(self) -> NumberType:
        '''
        (Read-only) The y coordinate of the top-side surface.
        '''
        return self.__pos.y - self.__size[1] // 2
    
    @property
    def size(self) -> tuple[int, int]:
        '''
        (Read-only) The size of the slab.
        '''
        return self.__size
    
    @property
    def velocity(self):
        '''
        (Read-only) The velocity of the slab.
        '''
        return self.__v.copy()


class PhysicsBall(PhysicsObject):
    '''
    The class represents physical interaction of a ball.
    '''
    __pos: Vector
    __angle: NumberType
    __v: Vector
    __w: NumberType # angular velocity
    __radius: LengthType
    __onground: bool
    __ground: PhysicsObject
    __bounceable: bool
    __path_length: LengthType

    def __init__(self, position: VectorType, radius: LengthType) -> None:
        '''
        Parameters
        ----------
        position: :class:`VectorType`
            The vector-like initial position of its center.
        radius: :class:`LengthType`
            The radius of the ball.
        '''
        self.__pos = Vector(position)
        self.__angle = 0
        self.__v = Vector.zero
        self.__w = 0
        self.__radius = radius
        self.__onground = False
        self.__ground = None
        self.__bounceable = False
        self.__path_length = 0

    def tick(self, dt: float, objs: _Iterable[PhysicsObject], *, bounce: bool = False) -> None:
        '''
        To be documented
        '''
        self.__pos += self.__v * dt
        self.__angle += self.__w * dt
        self.update_onground()
        self.update_bounceability(self.__v.magnitude * dt)
        if not self.__onground:
            self.__v += _GRAVITY * dt
            exception = None
        else:
            exception = self.__ground
            self.handle_friction()
        if bounce:
            self.bounce()
        for obj in objs:
            self.handle_collision(obj, exception)

    def bounce(self) -> None:
        '''
        Apply a bounce on the ball. If the ball is not bounceable, there will be no effect.
        '''
        if not self.__bounceable:
            return
        self.__v.y = max(_BOUNCE_VELOCITY, self.__v.y + _BOUNCE_VELOCITY)
        self.set_onground(False)
        self.set_bounceability(False)

    def handle_collision(self, obj: PhysicsObject, exception: PhysicsObject = None) -> None:
        '''
        Detect and handle the collision of the object and this ball. If collision occurs, a 
        force is applied on the ball. If further the object is not a wall, friction is also 
        applied on the ball.

        Parameters
        ----------
        obj: :class:`PhysicsObject`
            The object to be checked.
        exception: Optional[:class:`PhysicsObject`]
            The object to be excluded from possible colliding object list. Usually the ground of
            the ball.
        '''
        if obj is exception:
            return
        if (collision_vector := obj.check_collision(self)) is None:
            return
        self.collide(obj, obj.velocity, collision_vector)
        if not isinstance(obj, PhysicsWall):
            self.handle_friction(
                obj.velocity, 
                collision_vector, 
                times=_HANDLING_TIMES_ONCOLLISION
            )

    def collide(self, obj: PhysicsObject, obj_velocity: Vector, normal_vector: Vector) -> None:
        '''
        Apply the given collision to the ball. If the collision occurs inside a wall, 
        :meth:`wall_stuck_removal` will be called.
        
        Parameters
        ----------
        obj: :class:`PhysicsObject`
            The object which the ball collides with.
        obj_velocity: :class:`Vector`
            The velocity of the object.
        normal_vector: :class:`Vector`
            The normal vector of the object at the contact point.
        '''
        rel_velocity = self.__v - obj_velocity
        rel_normal_velocity = rel_velocity.project_on(normal_vector)
        rel_tangent_velocity = rel_velocity - rel_normal_velocity
        
        if isinstance(obj, PhysicsBall):
            raise NotImplementedError
        if rel_normal_velocity * normal_vector > 0:
            return
        
        rel_normal_velocity = linear_contraction(
            -rel_normal_velocity, Vector.zero, _COLLISION_SCALE, _COLLISION_OFFSET
        )
        
        if rel_normal_velocity.is_zerovec and normal_vector == Vector.unit_upward:
            self.set_onground(True, ground=obj)
        elif normal_vector * Vector.unit_upward > 0:
            self.set_bounceability(True)
        self.__v = obj_velocity + rel_tangent_velocity + rel_normal_velocity
        if isinstance(obj, PhysicsWall):
            self.remove_wall_stuck(obj)
    
    def remove_wall_stuck(self, wall: PhysicsWall) -> None:
        '''
        Try to remove the situation where the ball is stuck in the wall. Precisely, if the ball 
        is on-ground, the ball is directly moved out of the wall. Otherwise, a force outward 
        the wall is applied on the ball.

        Parameters
        ----------
        wall: :class:`PhysicsWall`
            The wall which the ball get stuck in.
        '''
        if self.__onground:
            if wall.facing == PhysicsWall.FACING_RIGHT:
                self.__pos.x = wall.x_side + self.__radius
            elif wall.facing == PhysicsWall.FACING_LEFT:
                self.__pos.x = wall.x_side - self.__radius
            return
        
        if wall.facing == PhysicsWall.FACING_RIGHT:
            self.__v.x = max(
                self.__v.x,
                wall_reflect_velocity(wall.x_side - self.__pos.x + self.__radius)
            )
        elif wall.facing == PhysicsWall.FACING_LEFT:
            self.__v.x = min(
                self.__v.x,
                -wall_reflect_velocity(wall.x_side - self.__pos.x - self.__radius)
            )

    def handle_friction(
            self, 
            obj_velocity: Vector = None, 
            normal_vector: Vector = None, 
            *, 
            times: int = 1
        ) -> None:
        '''
        Apply the simulated friction within a tick to the ball. If the ball is on the ground, 
        the object parameters need not be passed and will be overridden.
        
        Parameters
        ----------
        obj_velocity: Optional[:class:`Vector`]
            The velocity of the object. Default to the ground of the ball.
        normal_vector: Optional[:class:`Vector`]
            The normal vector of the object at the contact point. Default to the normal vector 
            of the ground.
        times: Optional[:class:`int`]
            The times of sliding friction applied. Default to 1.
        '''
        if self.__onground:
            obj_velocity = self.__ground.velocity
            normal_vector = self.__ground.get_normal_vector(self)
        
        obj_tangent = Vector(-normal_vector[1], normal_vector[0]).unit
        obj_projected_velocity = obj_velocity.project_on(obj_tangent)
        projected_velocity = self.__v.project_on(obj_tangent)
        normal_velocity = self.__v - projected_velocity

        # Change to relative inertial frame of reference
        rel_linear_velocity = obj_projected_velocity - projected_velocity
        rel_rolling_velocity = obj_tangent * self.__w * self.__radius
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
        self.__v = obj_projected_velocity - rel_linear_velocity + normal_velocity
        self.__w = rel_rolling_velocity.magnitude * sign(rel_rolling_velocity * obj_tangent) \
            / self.radius
        
    def set_onground(
            self, 
            onground: bool, 
            /, *, 
            ground: PhysicsGround | PhysicsSlab = None
        ) -> None:
        '''
        Set the ground attributes.

        Parameters
        ----------
        (positional)onground: `bool`
            Whether the ball is now on-ground.
        ground: Optional[Union[:class:`PhysicsGround`, :class:`PhysicsSlab`]]
            The ground which the ball is on. Required when ``onground`` is ``True``.
        '''
        self.__onground = onground
        self.__ground = ground
        if onground:
            self.__pos.y = ground.y_top - self.__radius
            self.set_bounceability(True)
        
    def set_bounceability(self, bounceable: bool, /) -> None:
        '''
        Set the bounceability attributes.

        Parameters
        ----------
        (positional)bounceable: `bool`
            Whether the ball is now bounceable.
        '''
        self.__bounceable = bounceable
        if bounceable:
            self.__path_length = 0

    def update_onground(self) -> None:
        '''
        Update whether the ball is still on-ground.
        '''
        if not self.__onground:
            return
        if not self.__ground.update_onground(self):
            self.set_onground(False)
        
    def update_bounceability(self, traveled_distance: LengthType) -> None:
        '''
        Update whether the ball is still bounceable after traveled for a given distance.

        Parameters
        ----------
        traveled_distance: `LengthType`
            The traveled distance of the ball after the previous tick.
        '''
        if self.__onground or not self.__bounceable:
            return
        self.__path_length += traveled_distance
        if self.__path_length > _MAX_BOUNCABLE_DISTANCE:
            self.set_bounceability(False)
    
    # temporary methods
    def temp(self, surface: PhysicsGround):
        self.__onground = True
        self.__ground = surface
    def vel(self, v, w):
        self.__v = Vector(v, 0)
        self.__w = w
    def getbounceability(self):
        return self.__bounceable

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