from language import Language
from constants import SettingConstant as Constant
from resources import Path
from dataclasses import dataclass
from json import load as jsonload, dump as jsondump
from errorlog import Log

@dataclass
class Setting:
    language: Language
    FPS: int
    BGM_Volume: int
    SE_Volume: int

    def lshift_language(self) -> None:
        self.language <<= 1

    def rshift_language(self) -> None:
        self.language >>= 1

    def lshift_FPS(self) -> None:
        if (i := Constant.FPS_CHOICES.index(self.FPS)) == 0:
            return
        self.FPS = Constant.FPS_CHOICES[i - 1]

    def rshift_FPS(self) -> None:
        if (i := Constant.FPS_CHOICES.index(self.FPS)) == Constant.FPS_CHOICE_NUMBER - 1:
            return
        self.FPS = Constant.FPS_CHOICES[i + 1]

    @property
    def isFPSmin(self) -> bool:
        return Constant.FPS_CHOICES.index(self.FPS) == 0
    
    @property
    def isFPSmax(self) -> bool:
        return Constant.FPS_CHOICES.index(self.FPS) == Constant.FPS_CHOICE_NUMBER - 1

    def set_BGM_volume(self, value: int) -> None:
        self.BGM_Volume = value

    def set_SE_volume(self, value: int) -> None:
        self.SE_Volume = value

    @classmethod
    @property
    def default(cls) -> "Setting":
        return cls(
            Language[Constant.DEFAULT_LANGUAGE], 
            Constant.DEFAULT_FPS, 
            Constant.DEFAULT_BGM_VOLUME, 
            Constant.DEFAULT_SE_VOLUME
        )

    @staticmethod
    def load() -> "Setting":
        try:
            with open(Path.SETTING, "r") as file:
                raw_setting = jsonload(file)
        except FileNotFoundError:
            return Setting.default
        except BaseException as e:
            Log.log(e)
            return Setting.default
        if not isinstance(raw_setting, dict):
            return Setting.default
        
        setting = Setting.default
        try:
            setting.language = Language[raw_setting.get("language")]
        except KeyError:
            pass
        if (fps := raw_setting.get("FPS")) in Constant.FPS_CHOICES:
            setting.FPS = fps
        match BGM_Volume := raw_setting.get("BGM Volume"):
            case int() if 0 <= BGM_Volume <= 100:
                setting.BGM_Volume = BGM_Volume
        match SE_Volume := raw_setting.get("SE Volume"):
            case int() if 0 <= SE_Volume <= 100:
                setting.SE_Volume = SE_Volume
        return setting
    
    def save(self) -> None:
        try:
            with open(Path.SETTING, "w") as file:
                jsondump(
                    {
                        "language": self.language.name, 
                        "FPS": self.FPS, 
                        "BGM Volume": self.BGM_Volume, 
                        "SE Volume": self.SE_Volume
                    }, 
                    file, 
                    indent=4
                )
        except BaseException as e:
            Log.log(e)