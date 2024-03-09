from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenPhoneMenu(Enum):

    EXIT_BTN = ScreenArea(pc_rect=Rect(1840, 25,1895, 80))  # 关闭按钮

    TRAILBLAZE_LEVEL_PART = ScreenArea(pc_rect=Rect(1280, 240, 1505, 275), text='开拓等级', lcs_percent=0.55)

    POWER_BTN = ScreenArea(pc_rect=Rect(1834, 951, 1897, 1008), status='返回登陆')
