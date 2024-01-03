from json import load as _jsonload
from enum import Enum as _Enum, StrEnum as _StrEnum, auto as _auto

class Language(_Enum):
    English = _auto()
    Japanese = _auto()
    Chinese = _auto()

class TranslateName(_StrEnum):
    name = _auto()
    game_starttext = _auto()

class Translatable:
    '''
    To be documented
    '''
    class ParserError(Exception):
        pass

    __languages: dict[Language, dict[TranslateName, str]] = {lang: {} for lang in Language}
    __error = ParserError("Failed to parse the level file")

    @classmethod
    def load(cls, language: Language, filepath: str) -> None:
        '''
        To be documented
        '''
        with open(filepath, "r") as file:
            translations = _jsonload(file)
        if not isinstance(translations, dict):
            raise cls.__error
        language_dict = {}
        English_dict = cls.__languages.get(Language.English, {})
        cls.__languages[language] = language_dict
        for name in TranslateName:
            if isinstance(translation := translations.get("name"), str):
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
    
Translatable.load(Language.English, ".\\languages\\English.json")
Translatable.load(Language.Japanese, ".\\languages\\Japanese.json")
Translatable.load(Language.Chinese, ".\\languages\\Chinese.json")