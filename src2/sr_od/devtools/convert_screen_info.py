from enum import Enum

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.screen.screen_area import ScreenArea
from one_dragon.base.screen.screen_info import ScreenInfo
from sr_od.context.sr_context import SrContext



class ScreenTrillionCatapult(Enum):
    CATAPULT_SINGLE_LINE = ScreenArea(pc_rect=Rect(908, 946, 1012, 971))  # 弹射轨迹连通文本位置 - 单行文本

    EXIT_BTN = ScreenArea(pc_rect=Rect(1847, 44,1886, 90))  # 关闭按钮
    CATAPULT = ScreenArea(pc_rect=Rect(1125, 914, 1220, 1009), text='弹射')
    DIALOG_CONFIRM = ScreenArea(pc_rect=Rect(989, 644, 1354, 704), text='确认')  # 放弃弹窗的确认
    EXIT_DIALOG_CONFIRM = ScreenArea(pc_rect=Rect(1006, 644, 1327, 704), text='确认')  # 退出对话框





if __name__ == '__main__':
    ctx = SrContext()

    screen = ScreenInfo(create_new=True)
    screen.screen_id = 'catapult'
    screen.screen_name = '弹珠机'
    screen.pc_alt = False

    area_list = []
    for area_enum in ScreenTrillionCatapult:
        area = area_enum.value
        area.area_name = area_enum.name
        area_list.append(area)

    screen.area_list = area_list
    screen.save()