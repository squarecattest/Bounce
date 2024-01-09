import pygame
from constants import GeneralConstant as Constant

pygame.init()
MAIN_SCREEN = pygame.display.set_mode(size = Constant.DEFAULT_SCREEN_SIZE, flags=pygame.RESIZABLE)
CENTER_SCREEN = pygame.Surface(Constant.DEFAULT_SCREEN_SIZE)
HIDDEN_SCREEN = pygame.Surface(Constant.DEFAULT_SCREEN_SIZE)

class Font:
    class Game:
        START_TEXT = pygame.font.Font(".\\fonts\\zpix.ttf", 18)
        START_TEXT.set_bold(True)
        SELECTION_MENU_TEXT = pygame.font.Font(".\\fonts\\zpix.ttf", 18)
        DEBUG_TEXT = pygame.font.Font(".\\fonts\\zpix.ttf", 16)
        SCOREBOARD_TITLE = pygame.font.Font(".\\fonts\\zpix.ttf", 18)
        SCOREBOARD_TITLE.set_bold(True)
        SCOREBOARD_TITLE.set_italic(True)
        SCOREBOARD_VALUE = pygame.font.Font(".\\fonts\\zpix.ttf", 32)
        SCOREBOARD_VALUE.set_bold(True)
        SCOREBOARD_VALUE.set_italic(True)
        LEVEL_TEXT = pygame.font.Font(".\\fonts\\zpix.ttf", 72)
        LEVEL_TEXT.set_bold(True)
        LEVEL_TEXT.set_italic(True)
        RESTART_TEXT = pygame.font.Font(".\\fonts\\zpix.ttf", 18)

    class Option:
        TITLE = pygame.font.Font(".\\fonts\\zpix.ttf", 48)
        TEXT = pygame.font.Font(".\\fonts\\zpix.ttf", 24)
        BARTEXT = pygame.font.Font(".\\fonts\\zpix.ttf", 24)
        BACKTEXT = pygame.font.Font(".\\fonts\\zpix.ttf", 24)

class Texture:
    BACKGROUND = pygame.image.load(".\\textures\\background-80x48.png").convert()
    BALL = pygame.image.load(".\\textures\\ball-40px.png").convert_alpha() #
    BALL_FRAME = pygame.image.load(".\\textures\\ball_frame-40px.png").convert_alpha()
    BALL_SURFACE = pygame.image.load(".\\textures\\ball_surface-40px.png").convert_alpha()
    SLAB = pygame.image.load(".\\textures\\brick-150x10.png").convert()
    GROUND = pygame.image.load(".\\textures\\ground-62x28.png").convert()
    SCOREBOARD = pygame.image.load(".\\textures\\scoreboard-10x60.png").convert()
    SELECTION_MENU_ARROW = pygame.image.load(
        ".\\textures\\selection_menu_arrow-16x16.png"
    ).convert_alpha()
    OPTION_VOLUME_BAR = pygame.image.load(".\\textures\\volume_bar-302x12.png").convert_alpha()
    OPTION_VOLUME_POINT_FRAME = pygame.image.load(
        ".\\textures\\volume_point_frame-48px.png"
    ).convert_alpha()
    OPTION_VOLUME_POINT_SURFACE = pygame.image.load(
        ".\\textures\\volume_point_surface-48px.png"
    ).convert_alpha()
    OPTION_SELECTION_BAR = pygame.image.load(
        ".\\textures\\option_selection_bar-200x36.png"
    ).convert()
    OPTION_SELECTION_LEFT_ARROW = pygame.image.load(
        ".\\textures\\option_selection_left_arrow-20x36.png"
    ).convert_alpha()

    OPTION_SELECTION_RIGHT_ARROW = pygame.image.load(
        ".\\textures\\option_selection_right_arrow-20x36.png"
    ).convert_alpha()
    OPTION_SELECTION_LEFT_ARROW_PRESSED = pygame.image.load(
        ".\\textures\\option_selection_left_arrow_pressed-20x36.png"
    ).convert_alpha()

    OPTION_SELECTION_RIGHT_ARROW_PRESSED = pygame.image.load(
        ".\\textures\\option_selection_right_arrow_pressed-20x36.png"
    ).convert_alpha()

class Color:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    class Game:
        START_TEXT = (255, 255, 255)
        SELECTION_MENU_TEXT = (255, 255, 255)
        DEBUG_TEXT = (255, 255, 255)
        DEBUG_BACKGROUND = (89, 89, 89)
        SCOREBOARD_TITLE = (200, 200, 200)
        SCOREBOARD_VALUE = (200, 200, 200)
        LEVEL_TEXT = (230, 230, 230)
        LEVEL_SHADOW = (200, 200, 200)
        RESTART_TEXT = (255, 255, 255)
        RESTART_BACKGROUND = (120, 120, 120)
        RESTART_COLORKEY = (255, 255, 255)

    class Option:
        TITLE = (255, 255, 255)
        TEXT = (255, 255, 255)
        TEXT_SELECTING = (160, 160, 160)
        TEXT_SHADOW = (120, 120, 120)
        BARTEXT = (200, 200, 200)

class Path:
    LEVEL = ".\\level.json"
    SETTING = ".\\setting.json"
    ERRORLOG = ".\\errorlog.txt"
    class Language:
        ENGLISH = ".\\languages\\English.json"
        JAPANESE = ".\\languages\\Japanese.json"
        CHINESE = ".\\languages\\Chinese.json"