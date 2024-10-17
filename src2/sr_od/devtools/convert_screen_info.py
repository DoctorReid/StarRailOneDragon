from enum import Enum

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.screen.screen_area import ScreenArea
from one_dragon.base.screen.screen_info import ScreenInfo
from sr_od.context.sr_context import SrContext


class ScreenLargeMap(Enum):

    SUB_MAP_BACK = ScreenArea(pc_rect=Rect(1675, 110, 1838, 150), text='返回')  # 二级地图中 需要返回

    MAIN_SCALE_MINUS = ScreenArea(pc_rect=Rect(623, 986, 623, 986))  # 缩小地图
    MAIN_SCALE_PLUS = ScreenArea(pc_rect=Rect(999, 984, 999, 984))  # 缩小地图

    SUB_SCALE_MINUS = ScreenArea(pc_rect=Rect(819, 987, 819, 987))  # 缩小地图
    SUB_SCALE_PLUS = ScreenArea(pc_rect=Rect(1194, 984, 1194, 984))  # 缩小地图

    PLANET_NAME = ScreenArea(pc_rect=Rect(100, 60, 350, 100))  # 左上角 - 星球名字
    STAR_RAIL_MAP = ScreenArea(pc_rect=Rect(1580, 120, 1750, 160), text='星轨航图')  # 右上角 - 星轨航图
    REGION_LIST = ScreenArea(pc_rect=Rect(1480, 200, 1820, 1000))  # 右侧区域列表

    TP_BTN = ScreenArea(pc_rect=Rect(1500, 950, 1800, 1000), text='传送')  # 右侧 传送按钮

    FLOOR_LIST = ScreenArea(pc_rect=Rect(30, 580, 110, 1000))  # 楼层



if __name__ == '__main__':
    ctx = SrContext()

    screen = ScreenInfo(create_new=True)
    screen.screen_id = 'large_map'
    screen.screen_name = '大地图'
    screen.pc_alt = False

    area_list = []
    for area_enum in ScreenLargeMap:
        area = area_enum.value
        area.area_name = area_enum.name
        area_list.append(area)

    screen.area_list = area_list
    screen.save()