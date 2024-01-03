import pygame

pygame.init()
pygame.display.set_mode(size = (1120, 630))

class Font:
    class Game:
        START_TEXT = pygame.font.Font(".\\fonts\\zpix.ttf", 14)
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
        RESTART_TEXT = pygame.font.Font(".\\fonts\\zpix.ttf", 14)

class Texture:
    BALL = pygame.image.load(".\\textures\\ball-40px.png").convert_alpha()
    BALL_FRAME = pygame.image.load(".\\textures\\ball-40px.png").convert_alpha()
    BALL_SURFACE = pygame.image.load(".\\textures\\ball-40px-surface.png").convert_alpha()
    SLAB = pygame.image.load(".\\textures\\brick-150x10.png").convert()
    GROUND = pygame.image.load(".\\textures\\ground-62x28.png").convert()
    SCOREBOARD = pygame.image.load(".\\textures\\scoreboard-10x60.png").convert()

class Color:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    class Game:
        START_TEXT = (255, 255, 255)
        DEBUG_TEXT = (255, 255, 255)
        DEBUG_BACKGROUND = (89, 89, 89)
        SCOREBOARD_TITLE = (200, 200, 200)
        SCOREBOARD_VALUE = (200, 200, 200)
        LEVEL_TEXT = (230, 230, 230)
        LEVEL_SHADOW = (200, 200, 200)
        RESTART_TEXT = (255, 255, 255)
        RESTART_BACKGROUND = (0, 0, 0)