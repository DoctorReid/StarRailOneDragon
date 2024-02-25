from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenPhoneMenu(Enum):

    POWER_BTN = ScreenArea(pc_rect=Rect(1834, 951, 1897, 1008), status='返回登陆')
