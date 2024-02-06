from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenLargeMap(Enum):

    PLANET_NAME = ScreenArea(pc_rect=Rect(100, 60, 350, 100))  # 左上角 - 星球名字
