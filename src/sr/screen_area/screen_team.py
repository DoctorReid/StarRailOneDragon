from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenTeam(Enum):

    TEAM_TITLE = ScreenArea(pc_rect=Rect(99, 37, 214, 59), text='队伍')
    SUPPORT_BTN = ScreenArea(pc_rect=Rect(1740, 720, 1830, 750), text='支援')

    SUPPORT_CLOSE = ScreenArea(pc_rect=Rect(1834, 39, 1889, 90))  # 支援画面 右上角关闭按钮
    SUPPORT_CHARACTER_LIST = ScreenArea(pc_rect=Rect(70, 160, 520, 940))  # 支援角色列表
    SUPPORT_JOIN = ScreenArea(pc_rect=Rect(1560, 970, 1840, 1010), text='入队')
