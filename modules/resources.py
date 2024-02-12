from __future__ import annotations
import pygame
from constants import GeneralConstant as Constant
from utils import Timer
import base64
import io

# Initial settings
pygame.init()
MAIN_SCREEN = pygame.display.set_mode(size = Constant.DEFAULT_SCREEN_SIZE, flags=pygame.RESIZABLE)
CENTER_SCREEN = pygame.Surface(Constant.DEFAULT_SCREEN_SIZE)
HIDDEN_SCREEN = pygame.Surface(Constant.DEFAULT_SCREEN_SIZE)
pygame.display.set_caption("Bounce!")
pygame.display.set_icon(pygame.image.load(".\\textures\\icon.png").convert_alpha())

class Font:
    class Game:
        START_TEXT = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 18)
        START_TEXT.set_bold(True)
        SELECTION_MENU_TEXT = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 18)
        DEBUG_TEXT = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 16)
        SCOREBOARD_TITLE = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 18)
        SCOREBOARD_TITLE.set_bold(True)
        SCOREBOARD_TITLE.set_italic(True)
        SCOREBOARD_VALUE = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 32)
        SCOREBOARD_VALUE.set_bold(True)
        SCOREBOARD_VALUE.set_italic(True)
        PAUSE_TITLE = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 32)
        PAUSE_TEXT = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 18)
        ACHIEVEMENT_FRAME_HEADER = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 18)
        ACHIEVEMENT_FRAME_NAME = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 24)
        LEVEL_TEXT = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 72)
        LEVEL_TEXT.set_bold(True)
        LEVEL_TEXT.set_italic(True)
        RESTART_TEXT = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 18)
        NEW_RECORD_TEXT = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 32)

    class Option:
        TITLE = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 48)
        TEXT = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 24)
        BARTEXT = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 24)
        BACKTEXT = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 24)

    class Achievement:
        TITLE = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 48)
        NAME = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 18)
        NAME.set_italic(True)
        DESCRIPTION = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 24)
        BACKTEXT = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 24)

    class Control:
        TITLE = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 48)
        TEXT = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 32)
        BACKTEXT = pygame.font.Font(".\\fonts\\Cubic_11_1.100_R.ttf", 24)

class Texture:
    ICON = pygame.image.load(".\\textures\\icon.png").convert_alpha()
    BACKGROUND = pygame.image.load(".\\textures\\background-80x48.png").convert()
    LOGO = pygame.image.load(".\\textures\\logo-648x174.png").convert_alpha()
    BALL_FRAME = pygame.image.load(".\\textures\\ball_frame-40px.png").convert_alpha()
    BALL_FRAME_EVENT = pygame.image.load(
        ".\\textures\\ball_frame_event-40px.png"
    ).convert_alpha()
    BALL_FRAME_UNBOUNCEABLE = pygame.image.load(
        ".\\textures\\ball_frame_unbounceable-40px.png"
    ).convert_alpha()
    BALL_SURFACE = pygame.image.load(".\\textures\\ball_surface-40px.png").convert_alpha()
    BALL_SURFACE_EVENT = pygame.image.load(
        ".\\textures\\ball_surface_event-40px.png"
    ).convert_alpha()
    SLAB_FRAME = pygame.image.load(".\\textures\\slab_frame-10x10.png").convert()
    SLAB_SURFACE = pygame.image.load(".\\textures\\slab_surface-10x10.png").convert()
    ROCKET_FACING_LEFT = pygame.image.load(
        ".\\textures\\rocket_left-150x100.png"
    ).convert_alpha()
    ROCKET_FACING_RIGHT = pygame.image.load(
        ".\\textures\\rocket_right-150x100.png"
    ).convert_alpha()
    GROUND = pygame.image.load(".\\textures\\ground-62x28.png").convert()
    SCOREBOARD = pygame.image.load(".\\textures\\scoreboard-10x60.png").convert()
    PAUSE_FRAME = pygame.image.load(".\\textures\\pause_page-420x180.png").convert_alpha()
    ACHIEVEMENT_FRAME = pygame.image.load(
        ".\\textures\\achievement_frame-280x60.png"
    ).convert_alpha() #
    ACHIEVEMENT_FRAME_LEFT = pygame.image.load(
        ".\\textures\\achievement_frame_left-12x60.png"
    ).convert_alpha()
    ACHIEVEMENT_FRAME_RIGHT = pygame.image.load(
        ".\\textures\\achievement_frame_right-12x60.png"
    ).convert_alpha()
    ACHIEVEMENT_FRAME_CENTER = pygame.image.load(
        ".\\textures\\achievement_frame_center-100x60.png"
    ).convert()
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
    OPTION_VOLUME_POINT_EVENT_FRAME = pygame.image.load(
        ".\\textures\\volume_point_event_frame-48px.png"
    ).convert_alpha()
    OPTION_VOLUME_POINT_EVENT_SURFACE = pygame.image.load(
        ".\\textures\\volume_point_event_surface-48px.png"
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
    ACHIEVEMENT_NAME_LEFT = pygame.image.load(
        ".\\textures\\achievement_title_left-12x24.png"
    ).convert_alpha()
    ACHIEVEMENT_NAME_RIGHT = pygame.image.load(
        ".\\textures\\achievement_title_right-12x24.png"
    ).convert_alpha()
    ACHIEVEMENT_NAME_FILL = pygame.image.load(
        ".\\textures\\achievement_title_fill-1x24.png"
    ).convert_alpha()
    ACHIEVEMENT_DESCRIPTION = pygame.image.load(
        ".\\textures\\achievement_bar-720x36.png"
    ).convert()
    CONTROL_KEY_SPACE = pygame.image.load(".\\textures\\control_key_space.png").convert_alpha()
    CONTROL_KEY_ESC = pygame.image.load(".\\textures\\control_key_escape.png").convert_alpha()
    CONTROL_KEY_D = pygame.image.load(".\\textures\\control_key_D.png").convert_alpha()

class Color:
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    TRANSPARENT_COLORKEY = (255, 255, 254)
    class Game:
        ROCKET_TRANSPARENT = (255, 255, 255)
        START_TEXT = (255, 255, 255)
        SELECTION_MENU_TEXT = (255, 255, 255)
        SELECTION_MENU_TEXT_SELECTING = (160, 160, 160)
        SELECTION_MENU_TEXT_PRESSED = (120, 120, 120)
        DEBUG_TEXT = (255, 255, 255)
        DEBUG_BACKGROUND = (89, 89, 89)
        SCOREBOARD_TITLE = (200, 200, 200)
        SCOREBOARD_VALUE = (200, 200, 200)
        ACHIEVEMENT_FRAME = (255, 255, 255)
        LEVEL_TEXT = (230, 230, 230)
        LEVEL_SHADOW = (200, 200, 200)
        NEW_RECORD_TEXT = (255, 255, 255)
        NEW_RECORD_BACKGROUND = (80, 80, 80)
        RESTART_TEXT = (255, 255, 255)
        RESTART_BACKGROUND = (120, 120, 120)
        RESTART_COLORKEY = (255, 255, 255)
        PAUSE_TEXT = (255, 255, 255)
        PAUSE_TEXT_SELECTING = (160, 160, 160)
        PAUSE_TEXT_PRESSED = (120, 120, 120)

    class Option:
        TITLE = (255, 255, 255)
        TEXT = (255, 255, 255)
        TEXT_SELECTING = (160, 160, 160)
        TEXT_PRESSED = (120, 120, 120)
        BARTEXT = (200, 200, 200)

    class Achievement:
        TITLE = BACK_TEXT = (255, 255, 255)
        TEXT = (200, 200, 200)
        TEXT_SELECTING = (160, 160, 160)
        TEXT_PRESSED = (120, 120, 120)
        SLIDER_NORMAL = (193, 193, 193)
        SLIDER_SELECTING = (168, 168, 168)
        SLIDER_PRESSED = (120, 120, 120)

    class Control:
        TITLE = (255, 255, 255)
        TEXT = (255, 255, 255)
        TEXT_SELECTING = (160, 160, 160)
        TEXT_PRESSED = (120, 120, 120)
        TEXT_BACKGROUND = (100, 100, 100)

class Path:
    LEVEL = ".\\level.json"
    SETTING = ".\\setting.json"
    DATAS = ".\\datas.json"
    HIGHSCORE = ".\\highscore.json"
    ERRORLOG = ".\\errors.log"
    class Language:
        ENGLISH = ".\\languages\\English.json"
        JAPANESE = ".\\languages\\Japanese.json"
        CHINESE = ".\\languages\\Chinese.json"


with open(".\\music\\bgm.txt", "rb") as file:
    bgm = io.BytesIO(base64.b64decode(file.read().replace(b"rr", b"r")))
class BGM:
    SCALE = 1.0013
    LOOP_START = 0.87
    LOOP_END = 70.44
    LOOP_LENGTH = LOOP_END - LOOP_START
    pygame.mixer.init()
    pygame.mixer.music.load(bgm)

    @classmethod
    def play(cls) -> None:
        pygame.mixer.music.play()
        cls.timer = Timer(start=True)
        cls.timer.offset(-cls.LOOP_START * cls.SCALE)

    @classmethod
    def loop(cls) -> None:
        if (time := cls.timer.read() * cls.SCALE - cls.LOOP_LENGTH) >= 0:
            pygame.mixer.music.play(start=cls.LOOP_START + time)
            cls.timer.restart()
            cls.timer.offset(time * cls.SCALE)

    @classmethod
    def stop(cls) -> None:
        pygame.mixer.music.stop()
        cls.timer.stop()

    @staticmethod
    def set_volume(volume: int) -> None:
        pygame.mixer.music.set_volume(0.75 * volume / 100)


class Sound:
    sounds: list[Sound] = []
    bounce: Sound
    
    @classmethod
    def register(cls, name: str, filepath: str) -> None:
        setattr(cls, name, cls(filepath))
        cls.sounds.append(getattr(cls, name))

    def __init__(self, filepath: str) -> None:
        self.sound = pygame.mixer.Sound(filepath)

    def play(self) -> None:
        self.sound.play()

    def stop(self) -> None:
        self.sound.stop()

    @classmethod
    def set_volume(cls, volume: int) -> None:
        for sound in cls.sounds:
            sound.sound.set_volume(0.75 * volume / 100)

Sound.register("bounce", ".\\sound\\bounce.wav")
