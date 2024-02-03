import pygame
from sys import exit
from modules.utils import FPSCounter
from modules.resources import MAIN_SCREEN, CENTER_SCREEN, HIDDEN_SCREEN
from modules.errorlog import Log
from modules.display import CenterScreenDisplay
from modules.interface import (
    save, 
    GameInterface, 
    OptionInterface, 
    AchievementInterface, 
    ControlInterface, 
    GameRequest, 
    OptionRequest, 
    AchievementRequest, 
    ControlRequest
)

def enter_event() -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEMOTION, pos=pygame.mouse.get_pos())

def quit() -> None:
    pygame.quit()
    save()
    OI.save()

OI = OptionInterface()
GI = GameInterface(OI.settings.language)
AI = AchievementInterface(OI.settings.language)
CI = ControlInterface(OI.settings.language)
FPS_SET = OI.settings.FPS
CLOCK = pygame.time.Clock()
CENTER_SCREEN_DISPLAY = CenterScreenDisplay(CENTER_SCREEN)
FPS_COUNTER = FPSCounter(100)
interface = GI
while True:
    try:
        FPS_COUNTER.append(CLOCK.tick(FPS_SET))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            interface.add_event(event)
        for request in interface.get_request():
            match request:
                case (
                    GameRequest.QUIT | OptionRequest.QUIT 
                    | AchievementRequest.QUIT | ControlRequest.QUIT
                ):
                    exit()
                case GameRequest.GOTO_OPTIONS:
                    interface = OI
                    interface.add_event(enter_event())
                case GameRequest.GOTO_ACHIEVEMENT:
                    interface = AI
                    interface.add_event(enter_event())
                case GameRequest.GOTO_CONTROLS:
                    interface = CI
                    interface.add_event(enter_event())
                case GameRequest.RELOAD_ACHIEVEMENT_INTERFACE:
                    AI.set_language(OI.settings.language)
                case OptionRequest.CHANGE_LANGUAGE:
                    GI.language = OI.settings.language
                    AI.set_language(OI.settings.language)
                    CI.set_language(OI.settings.language)
                case OptionRequest.CHANGE_FPS:
                    FPS_SET = OI.settings.FPS
                case OptionRequest.BACK | AchievementRequest.BACK:
                    interface = GI
                    interface.add_event(enter_event())
                case ControlRequest.BACK:
                    interface = GI
                    interface.add_event(enter_event())
        if interface is GI:
            GI.display(MAIN_SCREEN, CENTER_SCREEN, FPS_SET, FPS_COUNTER.read())
        else:
            GI.display(HIDDEN_SCREEN, HIDDEN_SCREEN, 0, 0)
            interface.display(MAIN_SCREEN, CENTER_SCREEN)
        CENTER_SCREEN_DISPLAY.display(MAIN_SCREEN)
        pygame.display.update()
    except (KeyboardInterrupt, SystemExit):
        quit()
        raise
    except BaseException as e:
        try:
            Log.log(e)
        except:
            quit()
            raise