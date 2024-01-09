import pygame
from sys import exit
from modules import utils, language
from modules.resources import MAIN_SCREEN, CENTER_SCREEN, HIDDEN_SCREEN
from modules.display import CenterScreenDisplay
from modules.interface import (
    GameInterface, 
    OptionInterface, 
    AchievementInterface, 
    ControlInterface, 
    GameRequest, 
    OptionRequest, 
    AchievementRequest, 
    ControlRequest
)

OI = OptionInterface()
GI = GameInterface(OI.settings.language)
CI = ControlInterface(OI.settings.language)
FPS = OI.settings.FPS
CLOCK = pygame.time.Clock()
Center_screen_dispaly = CenterScreenDisplay(CENTER_SCREEN)
FPSCounter = utils.FPSCounter(50)
interface = GI

while True:
    CLOCK.tick(FPS)
    events = pygame.event.get()
    for event in events:
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
            case GameRequest.GOTO_CONTROLS:
                interface = CI
            case OptionRequest.CHANGE_LANGUAGE:
                GI.language = OI.settings.language
                CI.set_language(OI.settings.language)
            case OptionRequest.CHANGE_FPS:
                FPS = OI.settings.FPS
            case OptionRequest.BACK:
                interface = GI
            case ControlRequest.BACK:
                interface = GI
    CENTER_SCREEN.fill((255, 255, 255))
    FPSCounter.tick()
    if interface.isGameInterface:
        OI.display(HIDDEN_SCREEN, HIDDEN_SCREEN)
        interface.display(MAIN_SCREEN, CENTER_SCREEN, FPS, FPSCounter.read())
    else:
        GI.display(HIDDEN_SCREEN, HIDDEN_SCREEN, FPS, FPSCounter.read())
        interface.display(MAIN_SCREEN, CENTER_SCREEN)
    Center_screen_dispaly.display(MAIN_SCREEN)
    pygame.display.update()