from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenDivUni(Enum):

    OE_TITLE = ScreenArea(pc_rect=Rect(105, 41, 257, 70), text='位面饰品提取')  # 左上角的title
    OE_FILE_MANAGEMENT_TITLE = ScreenArea(pc_rect=Rect(105, 63, 257, 94), text='存档管理')  # 左上角的title

    OE_SWITCH_FILE_BTN = ScreenArea(pc_rect=Rect(143, 953, 476, 1005), text='切换存档')  # 进入选择存档的按钮
    OE_FILE_1 = ScreenArea(pc_rect=Rect(37, 185, 332, 265))  # 存档1的位置
    OE_FILE_2 = ScreenArea(pc_rect=Rect(37, 315, 332, 395))  # 存档2的位置
    OE_FILE_3 = ScreenArea(pc_rect=Rect(37, 445, 332, 525))  # 存档3的位置
    OE_FILE_4 = ScreenArea(pc_rect=Rect(37, 575, 332, 655))  # 存档4的位置
    OE_CONFIRM_SWITCH_BTN = ScreenArea(pc_rect=Rect(1546, 954, 1850, 1001), text='切换存档', lcs_percent=0.55)  # 确认切换存档的按钮
    OE_FILE_USING_BTN = ScreenArea(pc_rect=Rect(1546, 954, 1850, 1001), text='存档使用中', lcs_percent=0.55)  # 确认切换存档的按钮

    OE_SUPPORT_BTN = ScreenArea(pc_rect=Rect(1067, 812, 1120, 838), text='支援')  # 支援按钮
    OE_CHALLENGE_BTN = ScreenArea(pc_rect=Rect(1478, 963, 1862, 1009), text='开始挑战')  # 挑战按钮