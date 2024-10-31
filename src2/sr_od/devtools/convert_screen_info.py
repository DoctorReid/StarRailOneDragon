from enum import Enum

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.screen.screen_area import ScreenArea
from one_dragon.base.screen.screen_info import ScreenInfo
from sr_od.context.sr_context import SrContext



class ScreenTeam(Enum):

    TEAM_TITLE = ScreenArea(pc_rect=Rect(99, 37, 214, 59), text='队伍')
    SUPPORT_BTN = ScreenArea(pc_rect=Rect(1740, 720, 1830, 750), text='支援')

    SUPPORT_CLOSE = ScreenArea(pc_rect=Rect(1834, 39, 1889, 90))  # 支援画面 右上角关闭按钮
    SUPPORT_CHARACTER_LIST = ScreenArea(pc_rect=Rect(70, 160, 520, 940))  # 支援角色列表
    SUPPORT_JOIN = ScreenArea(pc_rect=Rect(1560, 970, 1840, 1010), text='入队')

    SUPPORT_TITLE = ScreenArea(pc_rect=Rect(99, 37, 214, 59), text='支援')





if __name__ == '__main__':
    ctx = SrContext()

    screen = ScreenInfo(create_new=True)
    screen.screen_id = 'team'
    screen.screen_name = '队伍'
    screen.pc_alt = False

    area_list = []
    for area_enum in ScreenTeam:
        area = area_enum.value
        area.area_name = area_enum.name
        area_list.append(area)

    screen.area_list = area_list
    screen.save()