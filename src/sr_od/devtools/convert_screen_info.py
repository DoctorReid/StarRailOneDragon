from enum import Enum

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.screen.screen_area import ScreenArea
from one_dragon.base.screen.screen_info import ScreenInfo
from sr_od.context.sr_context import SrContext


class ScreenSynthesize(Enum):

    TITLE = ScreenArea(pc_rect=Rect(100, 38, 223, 65), text='合成')  # 左上角标题
    CATEGORY_TITLE = ScreenArea(pc_rect=Rect(100, 65, 228, 93))  # 左上角二级标题

    CATEGORY_1_BTN = ScreenArea(pc_rect=Rect(780, 40, 850, 85))  # 合成类别1 - 消耗品
    CATEGORY_2_BTN = ScreenArea(pc_rect=Rect(880, 40, 950, 85))  # 合成类别2 - 消耗品
    CATEGORY_3_BTN = ScreenArea(pc_rect=Rect(970, 40, 1040, 85))  # 合成类别3 - 消耗品
    CATEGORY_4_BTN = ScreenArea(pc_rect=Rect(1060, 40, 1130, 85))  # 合成类别4 - 消耗品

    ITEM_LIST = ScreenArea(pc_rect=Rect(74, 100, 507, 994))  # 合成物品的列表

    NOT_ENOUGH_MATERIAL = ScreenArea(pc_rect=Rect(1080, 849, 1289, 894), text='合成所需材料不足', lcs_percent=0.55)
    NUM_MAX = ScreenArea(pc_rect=Rect(1445, 870, 1445, 870))  # 合成数量最大值

    SYNTHESIZE_BTN = ScreenArea(pc_rect=Rect(1015, 963, 1347, 1005), text='合成')  # 合成按钮
    SYNTHESIZE_DIALOG_CONFIRM = ScreenArea(pc_rect=Rect(1008, 672, 1327, 728), text='确认')  # 合成弹窗的确认
    SYNTHESIZE_EMPTY_TO_CLOSE = ScreenArea(pc_rect=Rect(868, 930, 1053, 960), text='点击空白处关闭')



if __name__ == '__main__':
    ctx = SrContext()

    screen = ScreenInfo(create_new=True)
    screen.screen_id = 'synthesize'
    screen.screen_name = '合成'
    screen.pc_alt = False

    area_list = []
    for area_enum in ScreenSynthesize:
        area = area_enum.value
        area.area_name = area_enum.name
        area_list.append(area)

    screen.area_list = area_list
    screen.save()