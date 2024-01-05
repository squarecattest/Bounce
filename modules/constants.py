from vector import Vector
from math import pi

class GeneralConstant:
    DEFAULT_SCREEN_SIZE = (1120, 630)
    BALL_RADIUS = 20


class PhysicsConstant:
    GRAVITY = Vector(0, -960)
    BOUNCE_VELOCITY_RANGE = (480, 525)
    WALL_REFLECT_VELOCITY_MULTIPLIER = 1.25
    WALL_REFLECT_ALLOWED_DISTANCE = 0 #1 ?
    MAX_BOUNCABLE_DISTANCE = 20
    SLIDING_MULTIPLIER_ONCOLLISION = 3
    COLLISION_ALPHA, COLLISION_BETA = 0.6, 15
    SLIDING_GAMMA, SLIDING_DELTA = 15, 0.139
    ROLLING_GAMMA, ROLLING_DELTA = 2.5, 0.1
    #-------------------------DERIVED-------------------------#
    RAD_INV = 180 / pi


class GameConstant:
    SLAB_GAP = 100
    TRACE_HEIGHT = 250
    ORIGINAL_TOP_HEIGHT = 500

    #-------------------------DERIVED-------------------------#
    GROUND_Y = -GeneralConstant.BALL_RADIUS
    GAMEOVER_HEIGHT = ORIGINAL_TOP_HEIGHT \
        - GeneralConstant.DEFAULT_SCREEN_SIZE[1] - GeneralConstant.BALL_RADIUS
    UPPER_SLAB_BOUNDARY = ORIGINAL_TOP_HEIGHT + SLAB_GAP
    LOWER_SLAB_BOUNDARY = \
        ORIGINAL_TOP_HEIGHT - GeneralConstant.DEFAULT_SCREEN_SIZE[1] - SLAB_GAP


class InterfaceConstant:
    INGAME_FPS = 360
    RESTART_TEXT_ALPHA = 180
    DEBUG_TEXT_SEP = 20
    DEBUG_TEXT_ALPHA = 150
    DEBUG_TEXT_LASTING_TIME = 0.5
    GAMEOVER_FADEOUT_SECOND = 1
    RESTART_SCENE_SECOND = 1

    #-------------------------DERIVED-------------------------#
    DEFAULT_SCREEN_DIAGONAL = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE).magnitude
    SCREEN_OFFSET = -(Vector(GeneralConstant.DEFAULT_SCREEN_SIZE) // 2)
    DT = 1 / INGAME_FPS