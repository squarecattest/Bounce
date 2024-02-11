from __future__ import annotations
from json import load as jsonload
from enum import IntEnum, StrEnum, auto
from resources import Path

class Language(IntEnum):
    English = auto()
    Japanese = auto()
    Chinese = auto()

    def __lshift__(self, __v: int) -> Language:
        if (i := self.value - __v) <= 0:
            return Language(1)
        return Language(i)
    
    def __rshift__(self, __v: int) -> Language:
        if (i := self.value + __v) > (length := len(Language)):
            return Language(length)
        return Language(i)

class TranslateName(StrEnum):
    name = auto()
    game_start_text = auto()
    game_restart_text = auto()
    game_new_record_text = auto()
    game_scoreboard_record_height = auto()
    game_scoreboard_height = auto()
    game_scoreboard_level = auto()
    game_scoreboard_time = auto()
    game_achievement_frame_header = auto()
    game_selctionmenu_options = auto()
    game_selctionmenu_achievements = auto()
    game_selctionmenu_controls = auto()
    game_selctionmenu_quit = auto()
    game_pause_title = auto()
    game_pause_continue = auto()
    game_pause_restart = auto()
    game_pause_confirm_text = auto()
    game_pause_confirm_yes = auto()
    game_pause_confirm_no = auto()
    option_title = auto()
    option_language = auto()
    option_fps = auto()
    option_bgm = auto()
    option_se = auto()
    option_back = auto()
    achievement_title = auto()
    achievement_name_low_onground = auto()
    achievement_name_continuous_bounce = auto()
    achievement_name_long_stay = auto()
    achievement_name_fast_rotation = auto()
    achievement_name_free_fall = auto()
    achievement_name_bounce_high = auto()
    achievement_name_avoid_high_speed_rocket = auto()
    achievement_description_low_onground = auto()
    achievement_description_continuous_bounce = auto()
    achievement_description_long_stay = auto()
    achievement_description_fast_rotation = auto()
    achievement_description_free_fall = auto()
    achievement_description_bounce_high = auto()
    achievement_description_avoid_high_speed_rocket = auto()
    achievement_back = auto()
    control_title = auto()
    control_back = auto()
    control_bounce = auto()
    control_pause = auto()
    control_debug = auto()
    

class Translatable:
    '''
    To be documented
    '''
    class ParserError(Exception):
        pass

    __languages: dict[Language, dict[TranslateName, str]] = {lang: {} for lang in Language}

    @classmethod
    def load(cls, language: Language, filepath: str) -> None:
        '''
        To be documented
        '''
        with open(filepath, "r", encoding="utf-8") as file:
            translations = jsonload(file)
        if not isinstance(translations, dict):
            translations = dict()
        language_dict = {}
        English_dict = cls.__languages.get(Language.English, {})
        cls.__languages[language] = language_dict
        for name in TranslateName:
            if isinstance(translation := translations.get(name), str):
                language_dict[name] = translation
            elif (translation := English_dict.get(name)) is not None:
                language_dict[name] = translation
            else:
                language_dict[name] = ""
        
    def __init__(self, name: TranslateName, language: Language = Language.English) -> None:
        self.name = name
        self.language = language
        self.text = Translatable.__languages[language][name]

    def get(self, language: Language) -> str:
        '''
        To be documented
        '''
        if language == self.language:
            return self.text
        self.language = language
        self.text = Translatable.__languages[language][self.name]
        return self.text
    
Translatable.load(Language.English, Path.Language.ENGLISH)
Translatable.load(Language.Japanese, Path.Language.JAPANESE)
Translatable.load(Language.Chinese, Path.Language.CHINESE)