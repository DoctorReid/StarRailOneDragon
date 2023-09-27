import time

from sr.constants import LabelValue, get_planet_region_by_cn
from sr.context import Context, get_context
from sr.control import GameController
from sr.image.sceenshot import large_map
from sr.operation import Operation


class ChooseRegion(Operation):

    click_rect = (1480, 220, 1880, 1020)
    scroll_pos = ((click_rect[0] + click_rect[2]) // 2, (click_rect[1] + click_rect[3]) // 2)

    def __init__(self, planet_cn: str, region_cn: str):
        """
        默认已经打开了大地图 且选择了正确的星球。
        选择目标区域
        :param planet_cn: 星球中文名
        :param region_cn: 区域中文名
        """
        self.planet: LabelValue = get_planet_region_by_cn(planet_cn)
        self.region: LabelValue = get_planet_region_by_cn(region_cn)
        self.scroll_distance = -200

    def execute(self) -> bool:
        ctx: Context = get_context()
        ctrl: GameController = ctx.controller
        try_times = 0

        while ctx.running and try_times < 10:
            try_times += 1
            screen = ctrl.screenshot()
            planet = large_map.get_planet(screen, ctx.ocr)
            if planet is None or planet != self.planet:
                return False  # 目前不在目标大地图了

            find = self.click_target_region(screen, ctrl)
            if not find:  # 向下滚动5次 再向上滚动5次
                if try_times <= 5:
                    self.scroll_region_area(ctrl)
                elif try_times == 5:
                    for _ in range(try_times):  # 回到原点
                        self.scroll_region_area(ctrl, -1)
                        time.sleep(0.5)
                    self.scroll_region_area(ctrl)
                else:
                    self.scroll_region_area(ctrl)
                time.sleep(1)

        return False

    def click_target_region(self, screen, ctrl) -> bool:
        return ctrl.click_ocr(screen, self.region.cn, rect=ChooseRegion.click_rect)

    def scroll_region_area(self, ctrl, d: int = 1):
        """
        在选择区域的地方滚动鼠标
        :param ctrl: 控制器
        :param d: 滚动距离 正向下 负向上
        :return:
        """
        ctrl.scroll(self.scroll_distance * d, pos=ChooseRegion.scroll_pos)
