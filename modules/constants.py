from vector import Vector
from math import pi
from string import ascii_letters

class GeneralConstant:
    DEFAULT_SCREEN_SIZE = (1120, 630)
    BALL_RADIUS = 20

    #-------------------------DERIVED-------------------------#
    SCREEN_OFFSET = -(Vector(DEFAULT_SCREEN_SIZE) // 2)


class PhysicsConstant:
    GRAVITY = Vector(0, -960)
    BOUNCE_VELOCITY_RANGE = (480, 525)
    WALL_REFLECT_VELOCITY_MULTIPLIER = 1.25
    WALL_REFLECT_ALLOWED_DISTANCE = 0.01 #1 ?
    MAX_BOUNCABLE_DISTANCE = 20
    SLIDING_MULTIPLIER_ONCOLLISION = 3
    UNIT_SHRINK_LENGTH = 12
    COLLISION_ALPHA, COLLISION_BETA = 0.6, 15
    SLIDING_GAMMA, SLIDING_DELTA = 15, 0.139
    ROLLING_GAMMA, ROLLING_DELTA = 2.5, 0.1

    #-------------------------DERIVED-------------------------#
    RAD_INV = 180 / pi


class GameConstant:
    DEFAULT_LEVEL = {"length": 150, "width": 10, "separation": 70, "velocity": 40}
    SLAB_GAP = 100
    TRACE_HEIGHT = 250
    ORIGINAL_TOP_HEIGHT = 500
    HIGHSCORE_BITRANDOM_MULTIPLIER = (2, 3.6)
    HIGHSCORE_BITRANDOM_MINIMUM = 10
    HIGHSCORE_SCORERANDOM_MULTIPLIER = (2, 3.6)
    HIGHSCORE_SCORERANDOM_MINIMUM = 20
    ROCKET_HALFSIZE = (75, 50)
    ROCKET_SPEED = 80
    SUPER_ROCKET_SPEED = 500
    FALLING_BALLS = 10
    EVENT_ROCKET_LEVELS = 50, 200
    EVENT_ROCKET_CHANCES = 0.1, 0.5
    EVENT_ROCKET_TICK = 5
    EVENT_ROCKET_COOLDOWNS = 60, 10
    EVENT_SUPERROCKET_CHANCE = 0.2
    EVENT_FALLING_BALL_LEVELS = 100, 200
    EVENT_FALLING_BALL_CHANCES = 0.1, 0.5
    EVENT_FALLING_BALL_TICK = 5
    EVENT_FALLING_BALL_COOLDOWN = 60
    EVENT_UNION_SPAWN_CHANCE = 0.33
    SLAB_PARTICLE_OFFSET_SPEED = 15
    SLAB_PARTICLE_RANDOM_SPEED = 15
    BALL_PARTICLE_OFFSET_SPEED = 5
    BALL_PARTICLE_RANDOM_SPEED = 10
    PARTICLE_RANDOM_ANGULAR_FREQUENCY = 1.5
    UNIT_PARTICLE_SIZE = 4

    #-------------------------DERIVED-------------------------#
    GROUND_Y = -GeneralConstant.BALL_RADIUS
    SCREEN_BOTTOM_Y = ORIGINAL_TOP_HEIGHT - GeneralConstant.DEFAULT_SCREEN_SIZE[1]
    GAMEOVER_HEIGHT = ORIGINAL_TOP_HEIGHT \
        - GeneralConstant.DEFAULT_SCREEN_SIZE[1] - GeneralConstant.BALL_RADIUS
    UPPER_SLAB_BOUNDARY = ORIGINAL_TOP_HEIGHT + SLAB_GAP
    LOWER_SLAB_BOUNDARY = \
        ORIGINAL_TOP_HEIGHT - GeneralConstant.DEFAULT_SCREEN_SIZE[1] - SLAB_GAP
    FALLING_BALL_SEP = GeneralConstant.DEFAULT_SCREEN_SIZE[0] // (FALLING_BALLS + 1)


class DataConstant:
    class Achievement:
        CONTINUOUS_BOUNCE_LEVELS = 30
        LONG_STAY_SECONDS = 25
        FAST_ROTATION_FREQUENCY = 30
        FREE_FALL_LEVELS = 3
        BOUNCE_HIGH_HEIGHT = 100000

    class Bit:
        RANDOM_MULTIPLIER = (2, 3.6)
        LENGTH_MINIMUM = (8, 15)
        ZEROS = "aBcDeFgHiJlLm"
        ONES = "NoPqRsTuVwXyZ"
        ENDS = "Ex"
        RANDOMS = tuple(set(ascii_letters).difference(ZEROS, ONES, ENDS))

    class Binary:
        RANDOM_MULTIPLIER = (2, 3.6)
        LENGTH_MINIMUM = (10, 20)
        ZEROS = "AbCdEfGhIjKlM"
        ONES = "nOpQrStUvWxYz"
        ENDS = "q"
        RANDOMS = tuple(set(ascii_letters).difference(ZEROS, ONES, ENDS))

    class Trinary:
        RANDOM_MULTIPLIER = (2, 3.6)
        LENGTH_MINIMUM = (10, 20)
        ZEROS = "aBcDeFgH"
        ONES = "iJkLmNoP"
        TWOS = "qRsTuVwX"
        ENDS = "j"
        RANDOMS = tuple(set(ascii_letters).difference(ZEROS, ONES, TWOS, ENDS))

    class Trailing:
        LENGTH = (5, 20)
        RANDOMS = ascii_letters


class InterfaceConstant:
    class Game:
        INGAME_FPS = 360
        NEW_RECORD_POS = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 520)
        NEW_RECORD_ALPHA = 225
        RESTART_ALPHA = 180
        DEBUG_TEXT_SEP = 20
        DEBUG_TEXT_ALPHA = 150
        DEBUG_TEXT_LASTING_TIME = 0.5
        START_DISPLAY_POS = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 580)
        GAMEOVER_DISPLAY_POS = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 580)
        GAMEOVER_FADEOUT_SECOND = 0.7
        RESTART_SCENE_SECOND = 0.5
        STARTING_TEXT_CENTER = 575
        SELECTION_MENU_XPOS = 40
        SELECTION_MENU_ARROW_XPOS = 26
        SELECTION_MENU_SEP = 25
        SELECTION_PRESSED_OFFSET = Vector(-1, 1)
        ACHIEVEMENT_FRAME_POS = Vector(980, 60)
        ACHIEVEMENT_FRAME_LAST_TIME = 2
        PAUSE_SCENE_ALPHA = 200
        PAUSE_TITLE_POS = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 270)
        PAUSE_CONTINUE_POS = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 320)
        PAUSE_RESTART_POS = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 360)
        PAUSE_CONFIRM_TEXT_POS = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 320)
        PAUSE_BUTTON_NO_POS = Vector(490, 360)
        PAUSE_BUTTON_YES_POS = Vector(630, 360)
        PAUSE_PRESSED_OFFSET = Vector(-1, 1)
        PAUSE_ARROW_OFFSET = -20

        #-------------------------DERIVED-------------------------#
        DEFAULT_SCREEN_DIAGONAL = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE).magnitude
        SCREEN_OFFSET = -(Vector(GeneralConstant.DEFAULT_SCREEN_SIZE) // 2)
        DT = 1 / INGAME_FPS
        SCOREBOARD_DISPLAY_POS = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 0)

    class Option:
        TITLE_POS = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 100)
        YSEP = 50
        TEXT_XPOS = 350
        ARROW_XPOS = TEXT_XPOS - 20
        PRESSED_OFFSET = Vector(-1, 1)
        BACK_EXTRA_YSEP = 0.5
        BARS_XPOS = 690
        VOLUME_BUTTON_RADIUS = 24
        VOLUME_TICKER_STARTCOOLDOWN = 0.4
        VOLUME_TICKER_TICK = 0.02
        EASTER_EGG_PROBABILITY = 0.05

        #-------------------------DERIVED-------------------------#
        YCENTER = GeneralConstant.DEFAULT_SCREEN_SIZE[1] // 2
        
    class Achievement:
        TITLE_POS = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 100)
        BACK_TEXT_POS = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 580)
        ARROW_OFFSET = Vector(-20, 0)
        PRESSED_OFFSET = Vector(-1, 1)
        YSEP = 5
        NAME_TEXT_OFFSET = Vector(0, -1)
        DESCRIPTION_TEXT_OFFSET = Vector(10, -1)
        INNER_SCREEN_SIZE = (720, 330)
        SLIDER_WIDTH = 10
        INNER_SCREEN_TOP = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 200)
        SLIDER_X = (
            GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2 + INNER_SCREEN_SIZE[0] // 2 
            + SLIDER_WIDTH // 2 + 5
        )
        UNIT_INCREMENT = 30
        PAGE_TICKER_TICK = 0.03
        PAGE_TICKER_STARTCOOLDOWN = 0.6

        #-------------------------DERIVED-------------------------#

    class Control:
        TITLE_POS = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 100)
        BACK_TEXT_POS = Vector(GeneralConstant.DEFAULT_SCREEN_SIZE[0] // 2, 580)
        PRESSED_OFFSET = Vector(-1, 1)
        ARROW_OFFSET = Vector(-20, 0)
        ICON_TEXT_HORIZONTAL_SEP = 20
        ICON_TEXT_VERTICAL_SEP = 100
        ICON_TEXT_YPOS = 225
    

class SettingConstant:
    DEFAULT_LANGUAGE = "Japanese"
    DEFAULT_FPS = 120
    DEFAULT_BGM_VOLUME = 100
    DEFAULT_SE_VOLUME = 100
    FPS_CHOICES = (30, 60, 90, 120)

    #-------------------------DERIVED-------------------------#
    FPS_CHOICE_NUMBER = len(FPS_CHOICES)


class ErrorlogConstant:
    MAX_LOGS = 50