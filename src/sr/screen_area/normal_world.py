from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenNormalWorld(Enum):

    CHARACTER_ICON = ScreenArea(pc_rect=Rect(1800, 0, 1900, 90), text='大世界', template_id='ui_icon_01')  # 右上角的角色图标

    TEAM_MEMBER_AVATAR_1 = ScreenArea(pc_rect=Rect(0, 0, 0, 0))
    TEAM_MEMBER_AVATAR_2 = ScreenArea(pc_rect=Rect(0, 0, 0, 0))
    TEAM_MEMBER_AVATAR_3 = ScreenArea(pc_rect=Rect(0, 0, 0, 0))
    TEAM_MEMBER_AVATAR_4 = ScreenArea(pc_rect=Rect(0, 0, 0, 0))

    TEAM_MEMBER_NAME_1 = ScreenArea(pc_rect=Rect(0, 0, 0, 0))
    TEAM_MEMBER_NAME_2 = ScreenArea(pc_rect=Rect(0, 0, 0, 0))
    TEAM_MEMBER_NAME_3 = ScreenArea(pc_rect=Rect(0, 0, 0, 0))
    TEAM_MEMBER_NAME_4 = ScreenArea(pc_rect=Rect(0, 0, 0, 0))
