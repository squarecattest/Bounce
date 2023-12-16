from vector import *


_GRAVITY = -60
# Since the screen is y-positive downwards, all "y positions" are stored in negation, and
# "y velocity" and "y acceleration" are kept unmodified.

class PhysicsGround:
    '''
    The class represents physical interaction a flat ground.
    '''
    __y_top: NumberType

    def __init__(self, y_top: NumberType) -> None:
        assert isNumberType(y_top)
        self.__y_top = y_top

    def in_collision(self, ball: "PhysicsBall") -> bool:
        '''
        Check if colliding with the ball.
        '''
        return self.__y_top <= ball.position_y + ball.radius
    
    def collision_unit_vector(self, ball: "PhysicsBall") -> VecType:
        '''
        Return the acceleration direction to the ball due to collision. This
        function does NOT check if colliding.
        '''
        return 0, -1
    
    @property
    def position_y_top(self): return self.__y_top
    @property
    def position_y_top_int(self): return int(self.__y_top)
    @property
    def velocity_x(self): return 0
    

class PhysicsSlab:
    '''
    The class represents physical interaction of a floating slab.
    '''
    __x: NumberType
    __y: NumberType
    __size: SizeType
    __vx: NumberType

    def __init__(self, position: VecType, size: SizeType, velocity_x: NumberType) -> None:
        assert isVecType(position)
        assert isSizeType(size)
        assert isNumberType(velocity_x)
        self.__x, self.__y = position
        self.__size = tuple(size)
        self.__vx = velocity_x

    def accelerate(self, dt: float) -> None:
        '''
        Change the position of the slab with respect to time interval `dt`.
        '''
        assert isinstance(dt, float)
        self.__x += self.__vx * dt

    def in_collision(self, ball: "PhysicsBall") -> bool:
        '''
        Check if colliding with the ball.
        '''
        if self.__x + self.size_x <= ball.position_x - ball.radius:
            return True
        if self.__x - self.size_x >= ball.position_x + ball.radius:
            return True
        if self.__y - self.
        return self.position_y_top >= ball.position_y - ball.radius
    
    def collision_unit_vector(self, ball: "PhysicsBall") -> VecType:
        '''
        Return the acceleration unit vector to the ball due to collision. This
        function does NOT check if colliding.
        '''
        return 0, 1

    def handle_collision(self, ball: "PhysicsBall") -> CollisionType:
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
    def velocity_x(self): return self.__vx
    @property
    def topleft_corner(self): return self.__x - self.size_x, self.__y - self.size_y




class PhysicsBall:
    '''
    The class represents physical interaction of a ball.
    '''
    __x: NumberType
    __y: NumberType
    __vx: NumberType
    __vy: NumberType
    __radius: LengthType
    __onground: bool
    __ground: PhysicsGround | PhysicsSlab | None

    def __init__(self, position: VecType, radius: LengthType) -> None:
        assert isVecType(position)
        assert isLengthType(radius)
        self.__x, self.__y = position
        self.__vx = self.__vy = 0
        self.__radius = radius
        self.__onground = False
        self.__ground = None

    def accelerate(self, dt: float) -> None:
        '''
        Change the position and velocity of the ball with respect to time interval `dt`.
        '''
        assert isinstance(dt, float)
        self.__x += self.__vx * dt
        self.__y += self.__vy * dt # since y=0 is the top side of the window
        self.__vy += _GRAVITY * dt
        pass #############

    def detect_collision(self, *objs: PhysicsGround | PhysicsSlab):
        for obj in objs:
            pass

    @property
    def position(self): return self.__x, self.__y
    @property
    def position_int(self): return int(self.__x), int(self.__y)
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
    def radius(self): return self.__radius