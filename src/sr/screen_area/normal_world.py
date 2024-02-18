from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenNormalWorld(Enum):

    CHARACTER_ICON = ScreenArea(pc_rect=Rect(1800, 0, 1900, 90), template_id='ui_icon_01', status='大世界')  # 右上角的角色图标

    TEAM_MEMBER_AVATAR_1 = ScreenArea(pc_rect=Rect(1770, 275, 1873, 355))
    TEAM_MEMBER_AVATAR_2 = ScreenArea(pc_rect=Rect(1770, 375, 1873, 455))
    TEAM_MEMBER_AVATAR_3 = ScreenArea(pc_rect=Rect(1770, 475, 1873, 555))
    TEAM_MEMBER_AVATAR_4 = ScreenArea(pc_rect=Rect(1770, 575, 1873, 655))

    TEAM_MEMBER_NAME_1 = ScreenArea(pc_rect=Rect(1655, 285, 1765, 330))
    TEAM_MEMBER_NAME_2 = ScreenArea(pc_rect=Rect(1655, 385, 1765, 430))
    TEAM_MEMBER_NAME_3 = ScreenArea(pc_rect=Rect(1655, 485, 1765, 530))
    TEAM_MEMBER_NAME_4 = ScreenArea(pc_rect=Rect(1655, 585, 1765, 630))

    TECHNIQUE_POINT_1 = ScreenArea(pc_rect=Rect(1654, 836, 1674, 862))
    TECHNIQUE_POINT_2 = ScreenArea(pc_rect=Rect(1684, 836, 1704, 862))  # 2.0版本更新后 这块UI改变了 按ESC之后会变成上面的

    TECH_STATUS = ScreenArea(pc_rect=Rect(1767, 232, 1857, 255), text='状态效果')  # 右方 角色列表上方
    TECH_KEY = ScreenArea(pc_rect=Rect(1789, 823, 1807, 841))  # 秘技 显示快捷键的位置
