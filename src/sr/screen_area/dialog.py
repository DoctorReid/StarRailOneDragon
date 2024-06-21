from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenDialog(Enum):

    # 返回登陆 对话框
    BACK_TO_LOGIN_CONFIRM = ScreenArea(pc_rect=Rect(1004, 645, 1324, 705), text='确认')

    # 快速恢复 对话框
    FAST_RECOVER_TITLE = ScreenArea(pc_rect=Rect(890, 250, 1030, 300), text='快速恢复', lcs_percent=0.5)
    FAST_RECOVER_CONFIRM = ScreenArea(pc_rect=Rect(1020, 790, 1330, 844), text='确认')
    FAST_RECOVER_CANCEL = ScreenArea(pc_rect=Rect(592, 790, 903, 844), text='取消')
    FAST_RECOVER_NO_CONSUMABLE = ScreenArea(pc_rect=Rect(1094, 554, 1266, 585), text='暂无可用消耗品')
    
    # 奇巧零食
    QUIRKY_SNACKS = ScreenArea(pc_rect=Rect(900, 300, 1450, 760), template_id="quirky_snacks", template_match_threshold=0.5)