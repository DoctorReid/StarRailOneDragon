from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenDialog(Enum):

    # 返回登陆 对话框
    BACK_TO_LOGIN_CONFIRM = ScreenArea(pc_rect=Rect(1004, 645, 1324, 705), text='确认')

    # 快速恢复 对话框
    FAST_RECOVER_TITLE = ScreenArea(pc_rect=Rect(890, 250, 1030, 300), text='快速恢复')
    FAST_RECOVER_CONFIRM = ScreenArea(pc_rect=Rect(1020, 790, 1330, 844), text='确认')

