from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenDivUni(Enum):

    OE_TITLE = ScreenArea(pc_rect=Rect(1800, 0, 1900, 90), status='饰品提取')  # 左上角的title
    OE_FILE_MANAGEMENT_TITLE = ScreenArea(pc_rect=Rect(1800, 0, 1900, 90), status='存档管理')  # 左上角的title

    OE_SWITCH_FILE_BTN = ScreenArea(pc_rect=Rect(1800, 0, 1900, 90), status='切换存档')  # 进入选择存档的按钮
    OE_FILE_1 = ScreenArea(pc_rect=Rect(1800, 0, 1900, 90))  # 存档1的位置
    OE_FILE_2 = ScreenArea(pc_rect=Rect(1800, 0, 1900, 90))  # 存档2的位置
    OE_FILE_3 = ScreenArea(pc_rect=Rect(1800, 0, 1900, 90))  # 存档3的位置
    OE_FILE_4 = ScreenArea(pc_rect=Rect(1800, 0, 1900, 90))  # 存档4的位置
    OC_CONFIRM_SWITCH_BTN = ScreenArea(pc_rect=Rect(1800, 0, 1900, 90), status='切换存档')  # 确认切换存档的按钮

    OE_SUPPORT_BTN = ScreenArea(pc_rect=Rect(1800, 0, 1900, 90), status='支援')  # 支援按钮
    OE_CHALLENGE_BTN = ScreenArea(pc_rect=Rect(1800, 0, 1900, 90), status='挑战')  # 挑战按钮
    OE_MISSION_TITLE = ScreenArea(pc_rect=Rect(1800, 0, 1900, 90), status='挑战')  # 左上角的title