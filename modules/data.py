from __future__ import annotations
from errorlog import log
from constants import DataConstant as Constant
from resources import Path
from utils import classproperty
from random import randint, choice
from json import load as jsonload, dump as jsondump, JSONDecodeError
from enum import Flag, auto, CONFORM
from typing import Literal

def integer_encrypt(number: int) -> str:
    def get_digits(number: int, base: int = 2) -> list[int]:
        digits = []
        while number:
            digits.append(number % base)
            number //= base
        return digits

    def get_counts(
        digit_length: int, 
        multiplier: tuple[float, float], 
        minimum: tuple[int, int]
    ) -> tuple[int, int]:
        randoms = max(
            randint(int(digit_length * multiplier[0]), int(digit_length * multiplier[1])), 
            randint(*minimum)
        )
        return randoms, digit_length + randoms
    
    string = ""
    bitlen_paras = [
        get_digits(bitlen := number.bit_length()), 
        *get_counts(
            bitlen.bit_length(), 
            Constant.Bit.RANDOM_MULTIPLIER, 
            Constant.Bit.LENGTH_MINIMUM
        )
    ]
    binary_paras = [
        get_digits(number), 
        *get_counts(bitlen, Constant.Binary.RANDOM_MULTIPLIER, Constant.Binary.LENGTH_MINIMUM)
    ]
    trinary_paras = [
        trits := get_digits(number, 3), 
        *get_counts(
            len(trits), 
            Constant.Trinary.RANDOM_MULTIPLIER, 
            Constant.Trinary.LENGTH_MINIMUM
        )
    ]

    while bitlen_paras[2]:
        if randint(1, bitlen_paras[2]) <= bitlen_paras[1]:
            string += choice(Constant.Bit.RANDOMS)
            bitlen_paras[1] -= 1
        else:
            string += choice(
                (Constant.Bit.ZEROS, Constant.Bit.ONES)[bitlen_paras[0].pop()]
            )
        bitlen_paras[2] -= 1
    string += choice(Constant.Bit.ENDS)
    while binary_paras[2]:
        if randint(1, binary_paras[2]) <= binary_paras[1]:
            string += choice(Constant.Binary.RANDOMS)
            binary_paras[1] -= 1
        else:
            string += choice(
                (Constant.Binary.ZEROS, Constant.Binary.ONES)[binary_paras[0].pop()]
            )
        binary_paras[2] -= 1
    string += choice(Constant.Binary.ENDS)
    while trinary_paras[2]:
        if randint(1, trinary_paras[2]) <= trinary_paras[1]:
            string += choice(Constant.Trinary.RANDOMS)
            trinary_paras[1] -= 1
        else:
            string += choice(
                (
                    Constant.Trinary.ZEROS, 
                    Constant.Trinary.ONES, 
                    Constant.Trinary.TWOS
                )[trinary_paras[0].pop()]
            )
        trinary_paras[2] -= 1
    string += choice(Constant.Trinary.ENDS)
    for _ in range(randint(*Constant.Trailing.LENGTH)):
        string += choice(Constant.Trailing.RANDOMS)
    return string

def integer_decrypt(string: str, default: int = 0) -> int:
    bitlen = 0
    binary = 0
    trinary = 0
    s = ""
    for i, c in enumerate(string):
        s += c
        if c in Constant.Bit.ZEROS:
            bitlen <<= 1
        elif c in Constant.Bit.ONES:
            bitlen = (bitlen << 1) + 1
        elif c in Constant.Bit.ENDS:
            break
    else:
        return default
    s = ""
    for i, c in enumerate(string[i + 1:], i + 1):
        s += c
        if c in Constant.Binary.ZEROS:
            binary <<= 1
        elif c in Constant.Binary.ONES:
            binary = (binary << 1) + 1
        elif c in Constant.Binary.ENDS:
            break
    else:
        return default
    if binary.bit_length() != bitlen:
        return default
    for i, c in enumerate(string[i + 1:], i + 1):
        if c in Constant.Trinary.ZEROS:
            trinary *= 3
        elif c in Constant.Trinary.ONES:
            trinary = trinary * 3 + 1
        elif c in Constant.Trinary.TWOS:
            trinary = trinary * 3 + 2
        elif c in Constant.Trinary.ENDS:
            break
    else:
        return default
    return binary if binary == trinary else default


class Achievement(Flag, boundary=CONFORM):
    # The newly added achievements should be added to the end of the enums for compatibility.
    # Display order should only be changed at interface.
    empty = 0
    _unused = 1 << 7
    low_onground = auto()
    continuous_bounce = auto()
    long_stay = auto()
    fast_rotation = auto()
    free_fall = auto()
    bounce_high = auto()
    avoid_high_speed_rocket = auto()

    @classproperty
    def default(cls) -> Literal[Achievement.empty]:
        return cls.empty

    @classmethod
    def decrypt(cls, data: str) -> Achievement:
        return cls(integer_decrypt(data, cls.default))
    
    def encrypt(self) -> str:
        return integer_encrypt(self.value)
    

class HighScore(int):
    @classproperty
    def default(cls) -> HighScore:
        return cls(0)

    @classmethod
    def decrypt(cls, data: str) -> HighScore:
        return cls(max(integer_decrypt(data, cls.default) - 1000, 0))
    
    def encrypt(self) -> str:
        return integer_encrypt(self + 1000)
    

class Datas:
    @classmethod
    def set_default(cls) -> None:
        cls.achievement = Achievement.default
        cls.highscore = HighScore.default
    
    @classmethod
    def load(cls) -> None:
        try:
            with open(Path.DATAS, "r") as file:
                data = jsonload(file)
            if not isinstance(data, dict):
                cls.set_default()
            else:
                if isinstance(achievement := data.get("achievement"), str):
                    cls.achievement = Achievement.decrypt(achievement)
                else:
                    cls.achievement = Achievement.default
                if isinstance(highscore := data.get("highscore"), str):
                    cls.highscore = HighScore.decrypt(highscore)
                else:
                    cls.highscore = HighScore.default
        except (FileNotFoundError, JSONDecodeError):
            cls.set_default()
        except BaseException as e:
            log(e)
            cls.set_default()

    @classmethod
    def save(cls) -> None:
        try:
            with open(Path.DATAS, "w") as file:
                jsondump(
                    {
                        "achievement": cls.achievement.encrypt(),
                        "highscore": cls.highscore.encrypt()
                    }, 
                    file, 
                    indent=4
                )
        except BaseException as e:
            log(e)

Datas.load()