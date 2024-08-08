from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenTrillionCatapult(Enum):
    CATAPULT_SINGLE_LINE = ScreenArea(pc_rect=Rect(908, 946, 1012, 971))  # 弹射轨迹连通文本位置 - 单行文本

    EXIT_BTN = ScreenArea(pc_rect=Rect(1847, 44,1886, 90))  # 关闭按钮
    CATAPULT = ScreenArea(pc_rect=Rect(1125, 914, 1220, 1009), text='弹射')
    DIALOG_CONFIRM = ScreenArea(pc_rect=Rect(989, 644, 1354, 704), text='确认')  # 放弃弹窗的确认
    EXIT_DIALOG_CONFIRM = ScreenArea(pc_rect=Rect(1006, 644, 1327, 704), text='确认')  # 退出对话框
