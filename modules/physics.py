from vector import *
from abc import ABC as _ABC, abstractmethod as _abstractmethod
from typing import Literal as _Literal, Iterable as _Iterable
from itertools import product as _product
from math import pi as _pi

_RAD_INV = 180 / _pi
'------------------Constant Settings------------------'
_GRAVITY = Vector(0, 1960)
_BOUNCE_VELOCITY = -720
_WALL_REFLECT_VELOCITY_CONSTANT = 1.25
_WALL_REFLECT_ALLOWED_DISTANCE = 0 #1 ?
_MAX_BOUNCABLE_DISTANCE = 20
_SLIDING_MULTIPLIER = 3

## Tick-based Constants
_COLLISION_SCALE, _COLLISION_OFFSET = 0.6, 20
_SLIDING_F_SCALE, _SLIDING_F_OFFSET = 0.92, 0.01
_ROLLING_R_SCALE, _ROLLING_R_OFFSET = 0.993, 0.1
## Time-based Constants
_SLIDING_F_GAMMA, _SLIDING_F_DELTA = 15, 0.139
_ROLLING_GAMMA, _ROLLING_DELTA = 1.26, 0.126
'-----------------------------------------------------'

def _sign(number: NumberType) -> _Literal[-1, 0, 1]:
    '''
    Mathematical sign function.
    '''
    if number > 0: return 1
    if number < 0: return -1
    return 0

def _to_degree(radian: float) -> float:
    '''
    Convert an angle from radian to degree.
    '''
    return radian * _RAD_INV

def _tick_based_linear_contraction(
        original: Vector, 
        center: Vector, 
        alpha: float, 
        beta: float
    ) -> Vector:
    '''
    Map the distance between original and center by:

    distance -> scale * distance - offset

    Parameters
    ----------
    original: :class:`Vector`
        The vector to be mapped.
    center: :class:`Vector`
        The center of contraction.
    alpha: :class:`float`
        The multiplier in contraction. Should be a number between 0 and 1.
    beta: :class:`float`
        The subtraction constant in contraction. Should be a positive number.

    Returns
    -------
    :class:`Vector`
        The vector after mapped.
    '''
    difference = original - center
    if difference.is_zerovec:
        return center.copy()
    unit, mag = difference.unit, difference.magnitude
    mag *= alpha
    if mag < beta:
        return center.copy()
    return center + unit * (mag - beta)

def _time_based_linear_contraction(
        original: Vector, 
        center: Vector, 
        dt: float, 
        gamma: float, 
        delta: float
    ) -> Vector:
    '''
    Map the distance between original and center by:

    distance -> distance - dt * (scale * distance + offset)

    Parameters
    ----------
    original: :class:`Vector`
        The vector to be mapped.
    center: :class:`Vector`
        The center of contraction.
    dt: :class:`float`
        The time interval of a tick.
    gamma: :class:`float`
        The multiplier in contraction. Should be a positive number.
    delta: :class:`float`
        The subtraction constant in contraction. Should be a positive number.

    Returns
    -------
    :class:`Vector`
        The vector after mapped.
    '''
    difference = original - center
    if difference.is_zerovec:
        return center.copy()
    unit, mag = difference.unit, difference.magnitude
    mag -= dt * (gamma * mag + delta)
    if mag < 0:
        return center.copy()
    return center + unit * mag

def _wall_reflect_velocity(distance: NumberType) -> NumberType:
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
    def ckeck_onground(self, ball: "PhysicsBall") -> bool:
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

    def ckeck_onground(self, ball: "PhysicsBall") -> bool:
        return ball.velocity.y == 0
    
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
    
    def ckeck_onground(self, ball: "PhysicsBall") -> bool:
        return False
    
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
    
    def ckeck_onground(self, ball: "PhysicsBall") -> bool:
        return self.__v.y == 0 \
            and self.__pos.x - self.__size[0] // 2 <= ball.pos_x \
            <= self.__pos.x + self.__size[0] // 2
    
    def get_normal_vector(self, ball: "PhysicsBall") -> Vector:
        return Vector(0, -1)

    @property
    def position(self) -> Vector:
        '''
        (Read-only) The position vector of the center of the slab.
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
    The class representing physical interaction of a ball.
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
    __collision_exceptions: list[PhysicsObject]

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
        self.__collision_exceptions = []

    def tick(self, dt: float, objs: _Iterable[PhysicsObject], bounce: bool) -> None:
        '''
        Apply all the interactions.

        Parameters
        ----------
        dt: :class:`float`
            The time interval of a tick.
        objs: :class:`Iterable[PhysicsObject]`
            All the other interactable objects.
        bounce: :class:`bool`
            Whether the player bounced.
        '''
        self.__pos += self.__v * dt
        self.__angle += self.__w * dt
        self.update_onground()
        self.update_bounceability(self.__v.magnitude * dt)
        if not self.__onground:
            self.__v += _GRAVITY * dt
        else:
            self.__collision_exceptions.append(self.__ground)
            self.handle_friction(
                dt, self.__ground.velocity, self.__ground.get_normal_vector(self)
            )
        if bounce:
            self.bounce()
        for obj in objs:
            self.handle_collision(dt, obj)
        self.__collision_exceptions.clear()

    def bounce(self) -> None:
        '''
        Apply a bounce on the ball. If the ball is not bounceable, there will be no effect.
        '''
        if not self.__bounceable:
            return
        self.__v.y = max(_BOUNCE_VELOCITY, self.__v.y + _BOUNCE_VELOCITY)
        self.set_onground(False)
        self.set_bounceability(False)

    def handle_collision(self, dt: float, obj: PhysicsObject) -> None:
        '''
        Detect and handle the collision of the object and this ball. If collision occurs, a 
        force is applied on the ball. If the object is not a wall, friction is also applied on 
        the ball. If the collision occurs inside a wall, :meth:`wall_stuck_removal` will be 
        called. If after the collision is applied and the ball is still moving into the ground, 
        :meth:`ground_stuck_removal` will be called.

        Parameters
        ----------
        dt: :class:`float`
            The time interval of a tick.
        obj: :class:`PhysicsObject`
            The object to be checked.
        '''
        if obj in self.__collision_exceptions:
            return
        if (collision_vector := obj.check_collision(self)) is None:
            return
        if isinstance(obj, PhysicsBall):
            self.collide_with_ball(obj, collision_vector)
        else:
            self.collide_with_object(obj, collision_vector)
        if not isinstance(obj, PhysicsWall):
            self.handle_friction(
                dt, 
                obj.velocity, 
                collision_vector, 
                multiplier=_SLIDING_MULTIPLIER
            )
        else:
            self.remove_wall_stuck(obj)
        if isinstance(obj, PhysicsGround) and self.__v * Vector.unit_downward > 0:
            self.remove_ground_stuck(obj)

    def collide_with_ball(self, ball: "PhysicsBall", normal_vector: Vector) -> None:
        '''
        Apply the collision force to the ball for a ball-to-ball collision.
        
        Parameters
        ----------
        ball: :class:`PhysicsBall`
            The other ball which the ball collides with.
        normal_vector: :class:`Vector`
            The normal vector of the object at the contact point.
        '''
        ball.__collision_exceptions.append(self)
        v1_perp = self.__v.project_on(normal_vector)
        v2_perp = ball.__v.project_on(normal_vector)
        if (v1_perp - v2_perp) * normal_vector >= 0:
            return
        v1_para = self.__v - v1_perp
        v2_para = ball.__v - v2_perp
        v1_perp, v2_perp = _tick_based_linear_contraction(
                v2_perp, Vector.zero, _COLLISION_SCALE, _COLLISION_OFFSET
            ), _tick_based_linear_contraction(
                v1_perp, Vector.zero, _COLLISION_SCALE, _COLLISION_OFFSET
            )
        self.__v = v1_perp + v1_para
        ball.__v = v2_perp + v2_para

    def collide_with_object(self, obj: PhysicsObject, normal_vector: Vector) -> None:
        '''
        Apply the collision force to the ball for a ball-to-object collision.
        
        Parameters
        ----------
        obj: :class:`PhysicsObject`
            The object which the ball collides with.
        normal_vector: :class:`Vector`
            The normal vector of the object at the contact point.
        '''
        v_rel = self.__v - (v_2 := obj.velocity)
        v_rel_perp = v_rel.project_on(normal_vector)
        if v_rel_perp * normal_vector > 0:
            return
        v_rel_para = v_rel - v_rel_perp
        v_rel_perp = _tick_based_linear_contraction(
            -v_rel_perp, Vector.zero, _COLLISION_SCALE, _COLLISION_OFFSET
        )
        self.__v = v_2 + v_rel_perp + v_rel_para
        if v_rel_perp.is_zerovec and normal_vector == Vector.unit_upward:
            self.set_onground(True, ground=obj)
        elif self.__v.y <= 0 and normal_vector * Vector.unit_upward > 0:
            self.set_bounceability(True)

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
                _wall_reflect_velocity(wall.x_side - self.__pos.x + self.__radius)
            )
        elif wall.facing == PhysicsWall.FACING_LEFT:
            self.__v.x = min(
                self.__v.x,
                -_wall_reflect_velocity(wall.x_side - self.__pos.x - self.__radius)
            )

    def remove_ground_stuck(self, ground: PhysicsGround) -> None:
        '''
        Try to remove the situation where the ball is stuck in the ground. Precisely, the ball 
        is directly moved to the surface and the vertical velocity is set to zero.

        Parameters
        ----------
        ground: :class:`PhysicsGround`
            The ground which the ball get stuck in.
        '''
        self.__pos.y = ground.y_top - self.__radius
        self.__v.y = 0

    def handle_friction(
            self, 
            dt: float, 
            obj_velocity: Vector, 
            normal_vector: Vector, 
            *, 
            multiplier: LengthType = 1
        ) -> None:
        '''
        Apply the simulated friction within a tick to the ball.
        
        Parameters
        ----------
        dt: :class:`float`
            The time interval of a tick.
        obj_velocity: :class:`Vector`
            The velocity of the object.
        normal_vector: :class:`Vector`
            The normal vector of the object at the contact point.
        multiplier: Optional[:class:`LengthType`]
            The multiplier of time length when applying sliding friction. Default to 1.
        '''
        tangent_vector = Vector(-normal_vector.y, normal_vector.x).unit
        v_rel = obj_velocity - self.__v
        v_rel_para = v_rel.project_on(tangent_vector)
        v_rel_perp = v_rel - v_rel_para
        v_rot = tangent_vector * (self.__w * self.__radius)

        # Sliding friction
        v_diff = (v_rot - v_rel_para) / 3
        v_weighted = (v_rot + 2 * v_rel_para) / 3
        v_diff = _time_based_linear_contraction(
            v_diff, Vector.zero, multiplier * dt, _SLIDING_F_GAMMA, _SLIDING_F_DELTA
        )
        v_rot = 2 * v_diff + v_weighted
        v_rel_para = v_weighted - v_diff

        # Rolling friction
        v_rot = _time_based_linear_contraction(
            v_rot, Vector.zero, dt, _ROLLING_GAMMA, _ROLLING_DELTA
        )
        v_rel_para = _time_based_linear_contraction(
            v_rel_para, Vector.zero, dt, _ROLLING_GAMMA, _ROLLING_DELTA
        )
        self.__v = obj_velocity - (v_rel_perp + v_rel_para)
        self.__w = v_rel_para.magnitude * _sign(v_rel_para * tangent_vector) / self.__radius
    
    def check_collision(self, ball: "PhysicsBall") -> Vector | None:
        if (vec := ball.__pos - self.__pos).magnitude <= self.__radius + ball.__radius:
            return vec
        return None
    
    def ckeck_onground(self, ball: "PhysicsBall") -> bool:
        return False
    
    def get_normal_vector(self, ball: "PhysicsBall") -> Vector:
        return ball.__pos - self.__pos
    
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
        Update the on-ground attributes of the ball.
        '''
        if not self.__onground:
            return
        if not self.__ground.ckeck_onground(self):
            self.set_onground(False)
        
    def update_bounceability(self, traveled_distance: LengthType) -> None:
        '''
        Update the bounceability of the ball after traveled for a given distance.

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

    @property
    def position(self) -> Vector:
        '''
        (Read-only) The position vector of the center of the ball.
        '''
        return self.__pos.copy()
    
    @property
    def pos_x(self):
        '''
        (Read-only) The x coordinate of the center of the ball.
        '''
        return self.__pos.x
    
    @property
    def pos_y(self):
        '''
        (Read-only) The y coordinate of the center of the ball.
        '''
        return self.__pos.y
    
    @property
    def velocity(self):
        '''
        (Read-only) The velocity of the ball.
        '''
        return self.__v.copy()
    
    @property
    def rad_angle(self):
        '''
        (Read-only) The rotated angle of the ball, in unit of radian.
        '''
        return self.__angle
    
    @property
    def deg_angle(self):
        '''
        (Read-only) The rotated angle of the ball, in unit of degree.
        '''
        return _to_degree(self.__angle)
    
    @property
    def radius(self):
        '''
        (Read-only) The radius of the ball.
        '''
        return self.__radius
    
    @property
    def bounceable(self):
        '''
        (Read-only) The bounceability of the ball.
        '''
        return self.__bounceable