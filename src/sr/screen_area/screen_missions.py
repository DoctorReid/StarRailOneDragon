from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenMission(Enum):

    TRACE_BTN = ScreenArea(pc_rect=Rect(1495, 965, 1820, 1005), text='开始追踪', lcs_percent=0.55)
    CANCEL_TRACE_BTN = ScreenArea(pc_rect=Rect(1495, 965, 1820, 1005), text='停止追踪', lcs_percent=0.55)