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
    # Game
    INGAME_FPS = 360
    RESTART_TEXT_ALPHA = 180
    DEBUG_TEXT_SEP = 20
    DEBUG_TEXT_ALPHA = 150
    DEBUG_TEXT_LASTING_TIME = 0.5
    GAMEOVER_DISPLAY_POS = Vector(560, 580)
    GAMEOVER_FADEOUT_SECOND = 0.7
    RESTART_SCENE_SECOND = 0.5
    STARTING_TEXT_CENTER = 575
    SELECTION_MENU_XPOS = 40
    SELECTION_MENU_ARROW_XPOS = 26
    SELECTION_MENU_SEP = 25
    # Option
    OPTION_TITLE_POS = GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 100
    OPTION_SEP = 50
    OPTION_TEXT_XPOS = 350
    OPTION_ARROW_XPOS = OPTION_TEXT_XPOS - 20
    OPTION_SHADOW_OFFSET = Vector(-1, 1)
    OPTION_BACK_EXTRA_SEP = 0.5
    OPTION_BARS_XPOS = 690
    OPTION_VOLUME_BUTTON_RADIUS = 24
    OPTION_VOLUME_TICKER_STARTCOOLDOWN = 0.4
    OPTION_VOLUME_TICKER_TICK = 0.02

    #-------------------------DERIVED-------------------------#
    # Game
    DEFAULT_SCREEN_DIAGONAL = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE).magnitude
    SCREEN_OFFSET = -(Vector(GeneralConstant.DEFAULT_SCREEN_SIZE) // 2)
    DT = 1 / INGAME_FPS
    # Option
    OPTION_YCENTER = GeneralConstant.DEFAULT_SCREEN_SIZE[1] // 2
    

class SettingConstant:
    DEFAULT_LANGUAGE = "Japanese"
    DEFAULT_FPS = 120
    DEFAULT_BGM_VOLUME = 100
    DEFAULT_SE_VOLUME = 100
    FPS_CHOICES = (30, 60, 90, 120, 180)

    #-------------------------DERIVED-------------------------#
    FPS_CHOICE_NUMBER = len(FPS_CHOICES)
