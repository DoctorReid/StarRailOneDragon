from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenLargeMap(Enum):

    PLANET_NAME = ScreenArea(pc_rect=Rect(100, 60, 350, 100))  # 左上角 - 星球名字
    STAR_RAIL_MAP = ScreenArea(pc_rect=Rect(1580, 120, 1750, 160), text='星轨航图')  # 右上角 - 星轨航图
