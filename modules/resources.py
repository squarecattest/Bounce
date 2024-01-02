import pygame
from enum import Enum as _Enum

pygame.init()
pygame.display.set_mode(size = (1120, 630))

class Font:
    DEBUG_TEXT = pygame.font.Font(".\\fonts\\zpix.ttf", 16)
    SCOREBOARD_TITLE = pygame.font.Font(".\\fonts\\zpix.ttf", 18)
    SCOREBOARD_TITLE.set_bold(True)
    SCOREBOARD_TITLE.set_italic(True)
    SCOREBOARD_VALUE = pygame.font.Font(".\\fonts\\zpix.ttf", 32)
    SCOREBOARD_VALUE.set_bold(True)
    SCOREBOARD_VALUE.set_italic(True)

class Texture:
    BALL = pygame.image.load(".\\textures\\ball-40px.png").convert_alpha()
    SLAB = pygame.image.load(".\\textures\\brick-150x10.png").convert()
    GROUND = pygame.image.load(".\\textures\\ground25x16.png").convert()
    SCOREBOARD = pygame.image.load(".\\textures\\scoreboard-10x60.png").convert()

class Color:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    DEBUG_TEXT = WHITE
    DEBUG_BACKGROUND = (89, 89, 89)
    SCOREBOARD_TITLE = (200, 200, 200)
    SCOREBOARD_VALUE = (200, 200, 200)