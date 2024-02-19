from __future__ import annotations
from .vector import Vector, NumberType, LengthType, VectorType, SizeType
from .constants import GeneralConstant, PhysicsConstant as Constant
from .utils import Direction
from abc import ABC, abstractmethod
from typing import Literal, Iterable, NoReturn
from itertools import product
from random import triangular
from math import pi

def _sign(number: NumberType) -> Literal[-1, 0, 1]:
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
    return radian * Constant.RAD_INV

def _tick_based_linear_contraction(
        original: Vector, 
        center: Vector, 
        alpha: float, 
        beta: float
    ) -> Vector:
    '''
    Map the distance between original and center by:

    distance -> alpha * distance - beta

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

    distance -> distance - dt * (gamma * distance + delta)

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

def _bounce_velocity() -> NumberType:
    return triangular(*Constant.BOUNCE_VELOCITY_RANGE)

def _wall_reflect_velocity(distance: NumberType) -> NumberType:
    '''
    Get the reflection velocity for a ball stuck in a wall. The formula is given by:

    velocity = c * (distance ** 2)

    Parameters
    ----------
    distance: :class:`NumberType`
        The distance to the wall surface.
    '''
    return Constant.WALL_REFLECT_VELOCITY_MULTIPLIER * (distance ** 2)


class PhysicsObject(ABC):
    '''
    The meta class representing physical interaction of an object.
    '''
    @abstractmethod
    def check_collision(self, ball: PhysicsBall) -> Vector | None:
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
    
    @abstractmethod
    def check_onground(self, ball: PhysicsBall) -> bool:
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
    
    @abstractmethod
    def get_normal_vector(self, ball: PhysicsBall) -> Vector:
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
    @abstractmethod
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

    def check_collision(self, ball: PhysicsBall) -> Vector | None:
        if ball.position.y - ball.radius <= self.__y_top:
            return Vector.unit_upward
        return None

    def check_onground(self, ball: PhysicsBall) -> bool:
        return ball.velocity.y == 0
    
    def get_normal_vector(self, ball: PhysicsBall) -> Vector:
        return Vector.unit_upward

    @property
    def y_top(self) -> NumberType:
        '''
        (Read-only) The y coordinate of the surface.
        '''
        return self.__y_top
    
    @property
    def position(self) -> Vector:
        '''
        (Read-only) The position vector of the center of the surface of the ground. Vector 
        components can be changed by calling vector setters.
        '''
        return Vector(560, -20)
    
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
    __facing: Direction
    
    def __init__(self, x_side: NumberType, facing: Direction):
        '''
        Parameters
        ----------
        x_side: :class:`NumberType`
            The x coordinate of the surface.
        facing: ``Direction.LEFT`` or ``Direction.RIGHT``
            The facing of the wall.
        '''
        self.__x_side = x_side
        self.__facing = facing

    def check_collision(self, ball: PhysicsBall) -> Vector | None:
        if self.__facing == Direction.RIGHT \
            and ball.position.x - ball.radius <= self.__x_side:
            return Vector.unit_rightward
        if self.__facing == Direction.LEFT \
            and ball.position.x + ball.radius >= self.__x_side:
            return Vector.unit_leftward
        return None
    
    def check_onground(self, ball: PhysicsBall) -> bool:
        return False
    
    def get_normal_vector(self, ball: PhysicsBall) -> Vector:
        if self.__facing == Direction.RIGHT:
            return Vector.unit_rightward
        if self.__facing == Direction.LEFT:
            return Vector.unit_leftward
    
    @property
    def x_side(self) -> NumberType:
        '''
        (Read-only) The x coordinate of the surface.
        '''
        return self.__x_side
    
    @property
    def facing(self) -> Direction:
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
    __active_length_range: list[int]

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
        self.__active_length_range = [0, self.__size[0]]

    def tick(self, dt: float) -> None:
        '''
        Change the position and velocity of the slab with respect to time interval `dt`. 
        Velocity is constant for a slab.
        '''
        self.__pos += self.__v * dt

    def check_collision(self, ball: PhysicsBall) -> Vector | None:
        # Early exclusion
        if abs(ball.position.y - self.__pos.y) > ball.radius + self.__size[1] // 2:
            return None
        if abs(ball.position.x - self.__pos.x) > ball.radius + self.__size[0] // 2:
            return None
        if self.__active_length_range[0] == self.__active_length_range[1]:
            return None
        
        x_range = self.x_range
        y_range = self.__pos.y - self.__size[1] // 2, self.__pos.y + self.__size[1] // 2

        # Check sides
        if x_range[0] <= ball.position.x <= x_range[1]:
            if y_range[0] <= ball.position.y + ball.radius <= y_range[1]:
                return Vector.unit_downward
            if y_range[0] <= ball.position.y - ball.radius <= y_range[1]:
                return Vector.unit_upward
        if y_range[0] <= ball.position.y <= y_range[1]:
            if x_range[0] <= ball.position.x + ball.radius <= x_range[1]:
                return Vector.unit_leftward
            if x_range[0] <= ball.position.x - ball.radius <= x_range[1]:
                return Vector.unit_rightward

        # Check corners
        ball_pos = ball.position
        for x, y in product(x_range, y_range):
            if (vec := ball_pos - Vector(x, y)).magnitude <= ball.radius:
                return vec

        # Not colliding
        return None
    
    def check_onground(self, ball: PhysicsBall) -> bool:
        x_range = self.x_range
        #return ball.velocity.y == 0 and x_range[0] <= ball.position.x <= x_range[1]
        if ball.velocity.y <= 0 and x_range[0] <= ball.position.x <= x_range[1]:
            ball.position.y = self.y_top + ball.radius
            ball.velocity.y = 0
            return True
        return False
    
    def get_normal_vector(self, ball: PhysicsBall) -> Vector:
        return Vector.unit_upward
    
    def check_rocket_collision(self, rocket: PhysicsRocket) -> bool:
        if self.__active_length_range[0] == self.__active_length_range[1]:
            return False
        if self.position.y != rocket.position.y:
            return False
        if rocket.facing == Direction.LEFT:
            return rocket.x_left <= self.x_range[1]
        return rocket.x_right >= self.x_range[0]
    
    def get_shrink_parameter(self, rocket: PhysicsRocket) -> tuple[Direction, int]:
        if not self.check_rocket_collision(rocket):
            return Direction.NONE, 0
        shrink_total_length = min(Constant.UNIT_SHRINK_LENGTH, self.active_length)
        if rocket.facing == Direction.LEFT:
            self.__active_length_range[1] -= shrink_total_length
            while self.check_rocket_collision(rocket):
                shrink_length = min(Constant.UNIT_SHRINK_LENGTH, self.active_length)
                shrink_total_length += shrink_length
                self.__active_length_range[1] -= shrink_length
            return Direction.RIGHT, shrink_total_length
        else: # rocket.facing == Direction.RIGHT
            self.__active_length_range[0] += shrink_total_length
            while self.check_rocket_collision(rocket):
                shrink_length = min(Constant.UNIT_SHRINK_LENGTH, self.active_length)
                shrink_total_length += shrink_length
                self.__active_length_range[0] += shrink_length
            return Direction.LEFT, shrink_total_length
        
    def reload(self) -> None:
        self.__active_length_range = [0, self.__size[0]]

    @property
    def position(self) -> Vector:
        '''
        (Read-only) The position vector of the center of the slab. Vector components can be 
        changed by calling vector setters.
        '''
        return self.__pos
    
    @property
    def x_range(self) -> tuple[NumberType, NumberType]:
        '''
        (Read-only) The range of x coordinate of the slab entity.
        '''
        return (
            self.__pos.x - self.__size[0] // 2 + self.__active_length_range[0], 
            self.__pos.x - self.__size[0] // 2 + self.__active_length_range[1]
        )

    @property
    def y_top(self) -> NumberType:
        '''
        (Read-only) The y coordinate of the top-side surface.
        '''
        return self.__pos.y + self.__size[1] // 2
    
    @property
    def active_length(self) -> int:
        '''
        (Read-only) The length of the slab entity.
        '''
        return self.__active_length_range[1] - self.__active_length_range[0]
    
    @property
    def active_length_range(self) -> tuple[int, int]:
        '''
        (Read-only) The active range of the slab entity.
        '''
        return tuple(self.__active_length_range)
    
    @property
    def size(self) -> tuple[int, int]:
        '''
        (Read-only) The size of the slab.
        '''
        return self.__size
    
    @property
    def velocity(self):
        '''
        (Read-only) The velocity of the slab. Vector components can be changed by calling 
        vector setters.
        '''
        return self.__v
    
    
class PhysicsRocket(PhysicsObject):
    '''
    The class representing physical interaction of a rocket.
    '''
    __pos: Vector
    __v: Vector
    __halfsize: Vector
    __facing: Direction

    def __init__(self, position: VectorType, velocity_x: NumberType) -> None:
        '''
        Parameters
        ----------
        position: :class:`VectorType`
            The vector-like initial position of its center.
        velocity_x: :class:`NumberType`
            The constant horizontal velocity of the rocket.
        '''
        self.__pos = Vector(position)
        self.__v = Vector(velocity_x, 0)
        self.__halfsize = Vector(75, 50)
        self.__facing = Direction.LEFT if velocity_x < 0 else Direction.RIGHT

    def tick(self, dt: float) -> None:
        '''
        Change the position and velocity of the rocket with respect to time interval `dt`. 
        Velocity is constant for a rocket.
        '''
        self.__pos += self.__v * dt

    def check_collision(self, ball: PhysicsBall) -> Vector | Literal[True] | None:
        '''
        To be documented
        '''
        reference = ball.position - self.__pos
        abs_ref_x, abs_ref_y = abs(reference.x), abs(reference.y)

        # Early exclusion
        if not abs_ref_y <= self.__halfsize.y + ball.radius:
            return None
        if not abs_ref_x <= self.__halfsize.x + ball.radius:
            return None
        
        # Reflection to left-facing
        if self.__facing == Direction.RIGHT:
            reference.x = -reference.x

        # Right side: rebound
        if abs_ref_y <= 40 and -10 <= reference.x - ball.radius - self.__halfsize.x <= 0:
            return (
                Vector.unit_rightward
                if self.__facing == Direction.LEFT
                else Vector.unit_leftward
            )
        
        # Right-top / right-bottom
        if (
            48 <= reference.x <= 59 
            and -12 <= abs_ref_y - ball.radius - self.__halfsize.y <= -2
        ):
            return True
        
        # Middle-top / middle-bottom
        if (
            -9 <= reference.x <= 43 
            and -20 <= abs_ref_y - ball.radius - self.__halfsize.y <= -10
        ):
            return True
        
        # Left-top / left-bottom
        if (
            -47 <= reference.x <= -18 
            and -32 <= abs_ref_y - ball.radius - self.__halfsize.y <= -22
        ):
            return True
        
        # Left side
        if abs_ref_y <= 8 and 0 <= reference.x + ball.radius + self.__halfsize.x <= 10:
            return True
        
        # Left slopes
        yabs_reference = Vector(reference.x, abs_ref_y)
        if (
            -56.38 <= yabs_reference * Vector(7, 5).unit <= -21.97
            and 40.10 <= yabs_reference * Vector(-5, 7).unit - ball.radius <= 50.10
        ):
            return True
        
        # Right slopes
        if (
            5.66 <= yabs_reference * Vector(1, -1).unit <= 21.21
            and 63.54 <= yabs_reference * Vector(1, 1).unit - ball.radius <= 73.54
        ):
            return True
        
        squared_radius = ball.radius ** 2
        # Rightmost corners
        if (yabs_reference - Vector(67, 40)).squared_magnitude <= squared_radius:
            return True
        
        # Topmost(Bottommost) right corners
        if (yabs_reference - Vector(59, 48)).squared_magnitude <= squared_radius:
            return True
        
        # Topmost(Bottommost) left corners
        if (yabs_reference - Vector(48, 48)).squared_magnitude <= squared_radius:
            return True
        
        # Middle corners
        if (yabs_reference - Vector(-9, 40)).squared_magnitude <= squared_radius:
            return True

        # Middle-left corners
        if (yabs_reference - Vector(-75, 8)).squared_magnitude <= squared_radius:
            return True
        
        return None
    
    @property
    def remove(self) -> bool:
        return (
            self.__pos.x + self.__halfsize[0] <= 0
            or self.__pos.x - self.__halfsize[0] >= GeneralConstant.DEFAULT_SCREEN_SIZE[0]
        )
    
    def check_onground(self, ball: PhysicsBall) -> bool:
        return False
    
    def get_normal_vector(self, ball: PhysicsBall) -> NoReturn:
        raise NotImplementedError

    @property
    def position(self) -> Vector:
        '''
        (Read-only) The position vector of the center of the rocket. Vector components can be 
        changed by calling vector setters.
        '''
        return self.__pos
    
    @property
    def halfsize(self) -> Vector:
        '''
        (Read-only) Half of the size of the rocket.
        '''
        return self.__halfsize
    
    @property
    def x_left(self) -> NumberType:
        '''
        (Read-only) The x coordinate of the left side.
        '''
        return self.__pos.x - self.__halfsize.x
    
    @property
    def x_right(self) -> NumberType:
        '''
        (Read-only) The x coordinate of the right side.
        '''
        return self.__pos.x + self.__halfsize.x
    
    @property
    def facing(self) -> Direction:
        '''
        (Read-only) The facing of the rocket.
        '''
        return self.__facing
    
    @property
    def velocity(self):
        '''
        (Read-only) The velocity of the rocket. Vector components can be changed by calling 
        vector setters.
        '''
        return self.__v


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
    __ground: PhysicsObject | None
    __bounceable: bool
    __path_length: LengthType
    __collided: bool
    __collision_exceptions: list[PhysicsObject]
    __crash_on_rocket: bool
    __debug_msgs: list[str]

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
        self.__collided = False
        self.__collision_exceptions = [self]
        self.__crash_on_rocket = False
        self.__debug_msgs = []

    def tick(self, dt: float, bounce: bool, *objs: Iterable[PhysicsObject]) -> bool:
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

        Returns
        -------
        :class:`bool`
            Whether the ball collided.
        '''
        self.__pos += self.__v * dt
        self.__angle += self.__w * dt
        self.update_onground()
        self.update_bounceability(self.__v.magnitude * dt)
        if not self.__onground:
            self.__v += Constant.GRAVITY * dt
        else:
            self.__collision_exceptions.append(self.__ground)
            self.handle_friction(
                dt, 
                self.__ground.velocity, 
                self.__ground.get_normal_vector(self)
            )
        if bounce:
            self.bounce()
            self.__debug_msgs.append("<bounce>")
        for iterable in objs:
            for obj in iterable:
                self.handle_collision(dt, obj)
        self.__collision_exceptions = [self]
        if self.__collided:
            self.__collided = False
            return True
        return False

    def bounce(self) -> None:
        '''
        Apply a bounce on the ball. If the ball is not bounceable, there will be no effect.
        '''
        if not self.__bounceable:
            return
        self.__v.y = min(self.__v.y, 0) + _bounce_velocity()
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
        if isinstance(obj, PhysicsRocket):
            if (collision_vector := obj.check_collision(self)) is None:
                return
            elif collision_vector is True:
                self.__crash_on_rocket = True
                self.__debug_msgs.append("<crash: Rocket>")
                return
        elif (collision_vector := obj.check_collision(self)) is None:
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
                multiplier=Constant.SLIDING_MULTIPLIER_ONCOLLISION
            )
            if isinstance(obj, PhysicsBall):
                # Added this to deal with contacted balls problem.
                # (which is due to friction -> not on ground -> gravity force)
                # However, this does not seem to be an elegent solution.
                obj.handle_friction(
                    dt, 
                    self.velocity, 
                    -collision_vector, 
                    multiplier=Constant.SLIDING_MULTIPLIER_ONCOLLISION
                )
                self.update_onground()
                obj.update_onground()
        else:
            self.remove_wall_stuck(obj)
        if isinstance(obj, PhysicsGround) and self.__v * Vector.unit_downward > 0:
            self.remove_ground_stuck(obj)

    def collide_with_ball(self, ball: PhysicsBall, normal_vector: Vector) -> None:
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
        v1_perp, v2_perp = (
            _tick_based_linear_contraction(
                v2_perp, 
                Vector.zero, 
                Constant.COLLISION_ALPHA, 
                Constant.COLLISION_BETA
            ), 
            _tick_based_linear_contraction(
                v1_perp, 
                Vector.zero, 
                Constant.COLLISION_ALPHA, 
                Constant.COLLISION_BETA
            )
        )
        self.__v = v1_perp + v1_para
        if self.__v.y >= 0 and normal_vector * Vector.unit_upward >= 0:
            self.set_bounceability(True)
        if ball.__v.y >= 0 and -normal_vector * Vector.unit_upward >= 0:
            ball.set_bounceability(True)
        ball.__v = v2_perp + v2_para
        self.__collided = True
        ball.__collided = True
        self.__debug_msgs.append("<collide: Ball>")
        ball.__debug_msgs.append("<collide: Ball>")

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
            -v_rel_perp, 
            Vector.zero, 
            Constant.COLLISION_ALPHA, 
            Constant.COLLISION_BETA
        )
        self.__v = v_2 + v_rel_perp + v_rel_para
        if v_rel_perp.is_zerovec and normal_vector == Vector.unit_upward:
            self.set_onground(True, ground=obj)
        elif self.__v.y >= 0 and normal_vector * Vector.unit_upward > 0:
            self.set_bounceability(True)
        self.__collided = True
        self.__debug_msgs.append(
            f"<collide: {type(obj).__name__.removeprefix("Physics")}>"
        )

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
        distance = (
            wall.x_side - self.__pos.x + self.__radius
            if wall.facing == Direction.RIGHT
            else self.__pos.x + self.__radius - wall.x_side
        )
        if abs(distance) <= Constant.WALL_REFLECT_ALLOWED_DISTANCE:
            return
        self.__debug_msgs.append("<stuck removal: Wall>")
        if self.__onground:
            if wall.facing == Direction.RIGHT:
                self.__pos.x = wall.x_side + self.__radius
            elif wall.facing == Direction.LEFT:
                self.__pos.x = wall.x_side - self.__radius
            return
        
        if wall.facing == Direction.RIGHT:
            self.__v.x = max(
                self.__v.x,
                _wall_reflect_velocity(wall.x_side - self.__pos.x + self.__radius)
            )
        elif wall.facing == Direction.LEFT:
            self.__v.x = min(
                self.__v.x,
                -_wall_reflect_velocity(self.__pos.x + self.__radius - wall.x_side)
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
        self.__pos.y = ground.y_top + self.__radius
        self.__v.y = 0
        self.__debug_msgs.append("<stuck removal: Ground>")

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
            v_diff, 
            Vector.zero, 
            multiplier * dt, 
            Constant.SLIDING_GAMMA, 
            Constant.SLIDING_DELTA
        )
        v_rot = 2 * v_diff + v_weighted
        v_rel_para = v_weighted - v_diff

        # Rolling friction
        v_rot = _time_based_linear_contraction(
            v_rot, 
            Vector.zero, 
            dt, 
            Constant.ROLLING_GAMMA, 
            Constant.ROLLING_DELTA
        )
        v_rel_para = _time_based_linear_contraction(
            v_rel_para, 
            Vector.zero, 
            dt, 
            Constant.ROLLING_GAMMA, 
            Constant.ROLLING_DELTA
        )
        self.__v = obj_velocity - (v_rel_perp + v_rel_para)
        self.__w = v_rel_para.magnitude * _sign(v_rel_para * tangent_vector) / self.__radius
    
    def check_collision(self, ball: PhysicsBall) -> Vector | None:
        if (vec := ball.__pos - self.__pos).magnitude <= self.__radius + ball.__radius:
            return vec
        return None
    
    def check_onground(self, ball: PhysicsBall) -> bool:
        return False
    
    def get_normal_vector(self, ball: PhysicsBall) -> Vector:
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
            The ground which the ball is on. Required only when ``onground`` is ``True``.
        '''
        self.__onground = onground
        self.__ground = ground
        if onground:
            self.__pos.y = ground.y_top + self.__radius
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
        if not self.__ground.check_onground(self):
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
        if self.__path_length > Constant.MAX_BOUNCABLE_DISTANCE:
            self.set_bounceability(False)

    @property
    def position(self) -> Vector:
        '''
        (Read-only) The position vector of the center of the ball. Vector components can be 
        changed by calling vector setters.
        '''
        return self.__pos
    
    @property
    def velocity(self) -> Vector:
        '''
        (Read-only) The velocity of the ball. Vector components can be changed by calling 
        vector setters.
        '''
        return self.__v
    
    @property
    def rad_angle(self) -> NumberType:
        '''
        (Read-only) The reduced rotated angle of the ball, in unit of radian.
        '''
        return self.__angle % (2 * pi)
    
    @property
    def deg_angle(self) -> NumberType:
        '''
        (Read-only) The reduced rotated angle of the ball, in unit of degree.
        '''
        return _to_degree(self.__angle) % 360
    
    @property
    def angular_frequency(self) -> NumberType:
        '''
        (Read-only) The angular frequency of the ball, in unit of radian/second.
        '''
        return self.__w
    
    @property
    def ground(self) -> PhysicsObject | None:
        return self.__ground
    
    @property
    def ground_text(self) -> str:
        '''
        (Read-only) The text of the ground of the ball.
        '''
        if self.__ground is None:
            return "None"
        return type(self.__ground).__name__.removeprefix("Physics")
    
    @property
    def bounceable(self) -> bool:
        '''
        (Read-only) The bounceability of the ball.
        '''
        return self.__bounceable
    
    @property
    def radius(self) -> LengthType:
        '''
        (Read-only) The radius of the ball.
        '''
        return self.__radius
    
    @property
    def crash_on_rocket(self) -> bool:
        '''
        To be documented
        '''
        crash_on_rocket = self.__crash_on_rocket
        self.__crash_on_rocket = False
        return crash_on_rocket
    
    @property
    def debug_msgs(self) -> tuple[str]:
        '''
        (Read-only) Read the debug messages of the ball. This will also clear the message list 
        of the :class:`PhysicsBall` instance.
        '''
        msgs = tuple(self.__debug_msgs)
        self.__debug_msgs.clear()
        return msgs


class PhysicsParticle:
    '''
    The class representing physical interaction of a single particle in particle effects.
    '''
    __pos: Vector
    __v: Vector
    __angle: NumberType
    __w: NumberType
    def __init__(
        self, 
        position: VectorType, 
        velocity: VectorType, 
        angle: NumberType, 
        angular_frequency: NumberType
    ) -> None:
        self.__pos = Vector(position)
        self.__v = Vector(velocity)
        self.__angle = angle
        self.__w = angular_frequency

    def tick(self, dt: float) -> None:
        '''
        Change the physical constants of the particle with respect to time interval `dt`. The 
        particle only takes gravity as the only force. Angular frequency is constant for a
        particle.
        '''
        self.__pos += self.__v * dt
        self.__angle += self.__w * dt
        self.__v += Constant.GRAVITY * dt
    
    @property
    def position(self) -> Vector:
        '''
        (Read-only) The position vector of the center of the ball. Vector components can be 
        changed by calling vector setters.
        '''
        return self.__pos
    
    @property
    def rad_angle(self) -> NumberType:
        '''
        (Read-only) The reduced rotated angle of the ball, in unit of radian.
        '''
        return self.__angle % (2 * pi)
    
    @property
    def deg_angle(self) -> NumberType:
        '''
        (Read-only) The reduced rotated angle of the ball, in unit of degree.
        '''
        return _to_degree(self.__angle) % 360