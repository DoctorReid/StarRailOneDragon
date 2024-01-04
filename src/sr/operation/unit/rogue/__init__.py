from enum import Enum
from typing import Optional


class SimUniverseType(Enum):

    NORMAL: str = '模拟宇宙'

    EXTEND: str = '拓展装置'


class SimUniversePath(Enum):

    CH: str = '存护'

    JY: str = '记忆'

    XW: str = '虚无'

    FR: str = '丰饶'

    XL: str = '巡猎'

    HM: str = '毁灭'

    HY: str = '欢愉'

    FY: str = '繁育'

    ZS: str = '智识'


def path_of(path_str: str) -> Optional[SimUniversePath]:
    for path in SimUniversePath:
        if path.value == path_str:
            return path
    return None
