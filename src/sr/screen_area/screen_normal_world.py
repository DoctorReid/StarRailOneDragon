from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenNormalWorld(Enum):

    CHARACTER_ICON = ScreenArea(pc_rect=Rect(1800, 0, 1900, 90), template_id='ui_icon_01', status='大世界', pc_alt=True)  # 右上角的角色图标
    UID = ScreenArea(pc_rect=Rect(26, 1040, 160, 1063))

    TEAM_MEMBER_AVATAR_1 = ScreenArea(pc_rect=Rect(1770, 275, 1873, 355))
    TEAM_MEMBER_AVATAR_2 = ScreenArea(pc_rect=Rect(1770, 375, 1873, 455))
    TEAM_MEMBER_AVATAR_3 = ScreenArea(pc_rect=Rect(1770, 475, 1873, 555))
    TEAM_MEMBER_AVATAR_4 = ScreenArea(pc_rect=Rect(1770, 575, 1873, 655))

    TEAM_MEMBER_NAME_1 = ScreenArea(pc_rect=Rect(1655, 285, 1800, 330))
    TEAM_MEMBER_NAME_2 = ScreenArea(pc_rect=Rect(1655, 385, 1800, 430))
    TEAM_MEMBER_NAME_3 = ScreenArea(pc_rect=Rect(1655, 485, 1800, 530))
    TEAM_MEMBER_NAME_4 = ScreenArea(pc_rect=Rect(1655, 585, 1800, 630))

    TECHNIQUE_POINT_1 = ScreenArea(pc_rect=Rect(1654, 836, 1674, 862))
    TECHNIQUE_POINT_2 = ScreenArea(pc_rect=Rect(1684, 836, 1704, 862))  # 2.0版本更新后 这块UI改变了 按ESC之后会变成上面的

    TECH_STATUS = ScreenArea(pc_rect=Rect(1767, 232, 1857, 255), text='状态效果')  # 右方 角色列表上方
    TECH_KEY = ScreenArea(pc_rect=Rect(1789, 823, 1807, 841))  # 秘技 显示快捷键的位置

    EXPRESS_SUPPLY = ScreenArea(pc_rect=Rect(870, 80, 1050, 130), text='列车补给', lcs_percent=0.55)
    EXPRESS_SUPPLY_2 = ScreenArea(pc_rect=Rect(870, 50, 1050, 110), text='列车补给', lcs_percent=0.55)
    EXPRESS_SUPPLY_GET = ScreenArea(pc_rect=Rect(855, 892, 1078, 932), text='点击领取今日补贴')

    EMPTY_TO_CLOSE = ScreenArea(pc_rect=Rect(866, 925, 1062, 965), text='点击空白处关闭')

    MOVE_INTERACT = ScreenArea(pc_rect=Rect(900, 400, 1450, 870))  # 可移动时的交互框位置
    MOVE_INTERACT_SINGLE_LINE = ScreenArea(pc_rect=Rect(1174, 598, 1558, 647))  # 可移动时的交互框位置 - 单行文本
