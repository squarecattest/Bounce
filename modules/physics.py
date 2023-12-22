from vector import *
from typing import Literal
from math import pi as _pi
_RAD_INV = 180 / _pi
_GRAVITY = -60
_COLLISION_SCALE, _COLLISION_OFFSET = 1, 0
_SLIDING_F_SCALE, _SLIDING_F_OFFSET = 0.96, 0.01
_ROLLING_R_SCALE, _ROLLING_R_OFFSET = 0.99, 0.1
# Since the screen is y-positive downwards, all "y positions" are stored in negation, and
# "y velocity" and "y acceleration" are kept unmodified.

def sign(number: NumberType) -> Literal[-1, 0, 1]:
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

    `distance` -> `distance` * `scale` - `offset`

    `center`:
        The center of contraction. Should support addition and subtraction operations.
    `scale`:
        The multiplier in contraction. Should be a number between 0 and 1.
    `offset`:
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
    
class PhysicsGround:
    '''
    The class representing physical interaction of a flat ground.
    '''
    __y_top: NumberType

    def __init__(self, y_top: NumberType) -> None:
        assert isNumber(y_top)
        self.__y_top = y_top

    def tick(self, dt: float) -> None:
        '''
        Change the position and velocity with respect to time interval `dt`. Nothing changed for 
        a ground since it is motionless.
        '''
        pass

    def in_collision(self, ball: "PhysicsBall") -> bool:
        '''
        Check if colliding with the ball.
        '''
        return self.__y_top <= ball.position_y + ball.radius
    
    def collision_unit_vector(self, ball: "PhysicsBall") -> Vector:
        '''
        Return the acceleration direction to the ball due to collision. This function does NOT 
        check if colliding.
        '''
        return 0, -1
    
    def get_normal(self, arg):
        return Vector(0, -1)
    
    @property
    def position_y_top(self): return self.__y_top
    @property
    def position_y_top_int(self): return int(self.__y_top)
    @property
    def velocity(self): return Vector(0, 0)
    

class PhysicsSlab:
    '''
    The class representing physical interaction of a floating slab.
    '''
    __x: NumberType
    __y: NumberType
    __size: SizeType
    __v: Vector

    def __init__(self, position: VectorType, size: SizeType, velocity_x: NumberType) -> None:
        self.__x, self.__y = position
        self.__size = tuple(size)
        self.__v = Vector(velocity_x, 0)

    def tick(self, dt: float) -> None:
        '''
        Change the position and velocity of the slab with respect to time interval `dt`. Velocity 
        is constant for a slab.
        '''
        self.__x += self.__v.x * dt

    def in_collision(self, ball: "PhysicsBall") -> bool:
        '''
        Check if colliding with the ball.
        '''
        if self.__x + self.size_x <= ball.position_x - ball.radius:
            return True
        if self.__x - self.size_x >= ball.position_x + ball.radius:
            return True
        #if self.__y - self.
        return self.position_y_top >= ball.position_y - ball.radius
    
    def collision_unit_vector(self, ball: "PhysicsBall") -> VectorType:
        '''
        Return the acceleration unit vector to the ball due to collision. This function does NOT 
        check if colliding.
        '''
        return 0, 1

    def handle_collision(self, ball: "PhysicsBall") -> None:
        '''
        Check the collision type of the ball.
        '''
        assert isinstance(ball, PhysicsBall)
        if self.__x + self.size_x:pass
        if self.__y_top <= ball.position_y + ball.radius:
            return _COLLISION_BOTTOM
        return _COLLISION_NONE

    @property
    def position(self): return self.__x, self.__y
    @property
    def position_int(self): return int(self.__x), int(self.__y)
    @property
    def position_x(self): return self.__x
    @property
    def position_y(self): return self.__y
    @property
    def size(self): return self.__size
    @property
    def size_x(self): return self.__size[0]
    @property
    def size_y(self): return self.__size[1]
    @property
    def velocity(self): return self.__v.copy()
    @property
    def topleft_corner(self): return self.__x - self.size_x, self.__y - self.size_y


class PhysicsBall:
    '''
    The class represents physical interaction of a ball.
    '''
    #__x: NumberType
    #__y: NumberType
    __pos: Vector
    __angle: NumberType
    __v: Vector
    __w: NumberType
    __radius: LengthType
    __onground: bool
    __ground: PhysicsGround | PhysicsSlab | None

    def __init__(self, position: VectorType, radius: LengthType) -> None:
        assert isVector(position)
        assert isPosNumber(radius)
        self.__pos = Vector(position)
        self.__angle = 0
        self.__v = Vector(0, 0)
        self.__radius = radius
        self.__onground = False
        self.__ground = None

    def accelerate(self, dt: float) -> None:
        '''
        Change the position and velocity of the ball with respect to time interval `dt`.
        '''
        assert isinstance(dt, float)
        self.__pos += self.__v * dt
        self.__angle += self.__w * dt
        #self.__vy += _GRAVITY * dt
        pass #############

    def detect_collision(self, *objs: PhysicsGround | PhysicsSlab):
        for obj in objs:
            pass

    def handle_friction(
            self, surface_velocity: Vector = None, surface_normal: Vector = None
        ) -> None:
        '''
        Apply the simulated friction within a tick to the ball. If the ball is on the ground, 
        the surface parameters need not be passed.
        `surface_velocity`:
            The velocity of the surface.
        `surface_normal`:
            The normal vector of the surface at the contact point. Should be pointing outward.
        '''
        if self.__onground:
            surface_velocity = self.__ground.velocity
            surface_normal = self.__ground.get_normal(self)
        
        surface_tangent = Vector(-surface_normal[1], surface_normal[0]).unit
        surface_projected_velocity = surface_velocity.project_on(surface_tangent)
        projected_velocity = self.__v.project_on(surface_tangent)
        normal_velocity = self.__v - projected_velocity
        rolling_velocity = surface_tangent * self.__w * self.__radius

        # Change to relative inertial frame of reference
        rel_linear_velocity = surface_projected_velocity - projected_velocity
        rel_rolling_velocity = rolling_velocity - surface_projected_velocity
        rel_average_velocity = (rel_linear_velocity + rel_rolling_velocity) / 2

        # Sliding friction
        rel_linear_velocity = linear_contraction(
            rel_linear_velocity, rel_average_velocity, _SLIDING_F_SCALE, _SLIDING_F_OFFSET
        )
        rel_rolling_velocity = linear_contraction(
            rel_rolling_velocity, rel_average_velocity, _SLIDING_F_SCALE, _SLIDING_F_OFFSET
        )
        
        # Rolling friction / Rolling resistence
        rel_linear_velocity = linear_contraction(
            rel_linear_velocity, Vector(0, 0), _ROLLING_R_SCALE, _ROLLING_R_OFFSET
        )
        rel_rolling_velocity = linear_contraction(
            rel_rolling_velocity, Vector(0, 0), _ROLLING_R_SCALE, _ROLLING_R_OFFSET
        )

        # Change back to the normal frame of reference
        self.__v = surface_projected_velocity - rel_linear_velocity + normal_velocity
        rolling_velocity = rel_rolling_velocity + surface_projected_velocity
        self.__w = rolling_velocity.magnitude * sign(rolling_velocity * surface_tangent) \
            / self.radius
        print(self.__v.magnitude, self.__w * self.__radius)
        
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
    def position_x(self): return self.__x
    @property
    def position_y(self): return self.__y
    @property
    def velocity(self): return self.__vx, self.__vy
    @property
    def velocity_int(self): return int(self.__vx), int(self.__vy)
    @property
    def velocity_x(self): return self.__vx
    @property
    def velocity_y(self): return self.__vy
    @property
    def angle(self): return self.__angle
    @property
    def radius(self): return self.__radius