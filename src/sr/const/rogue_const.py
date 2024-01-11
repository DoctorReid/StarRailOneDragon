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


UNI_NUM_CN: dict[int, str] = {
    1: '一',
    2: '二',
    3: '三',
    4: '四',
    5: '五',
    6: '六',
    7: '七',
    8: '八',
}


def path_of(path_str: str) -> Optional[SimUniversePath]:
    for path in SimUniversePath:
        if path.value == path_str:
            return path
    return None
