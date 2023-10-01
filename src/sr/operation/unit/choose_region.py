import time

from basic.log_utils import log
from sr.constants.map import Planet, Region
from sr.context import Context
from sr.control import GameController
from sr.image.sceenshot import large_map
from sr.operation import Operation


class ChooseRegion(Operation):

    click_rect = (1450, 200, 1700, 1000)
    scroll_pos = ((click_rect[0] + click_rect[2]) // 2, (click_rect[1] + click_rect[3]) // 2)
    scroll_distance = -300

    def __init__(self, ctx: Context, region: Region):
        """
        默认已经打开了大地图 且选择了正确的星球。
        选择目标区域
        :param region: 区域
        """
        super().__init__(ctx, 10)
        self.planet: Planet = region.planet
        self.region: Region = region

    def run(self) -> int:
        ctrl: GameController = self.ctx.controller
        screen = ctrl.screenshot()
        planet = large_map.get_planet(screen, self.ctx.ocr)
        if planet is None or planet != self.planet:
            return Operation.FAIL  # 目前不在目标大地图了

        find = self.click_target_region(screen)
        if not find:  # 向下滚动5次 再向上滚动5次
            log.info('当前界面未发现 %s 准备滚动', self.region.cn)
            if self.op_round < 5:
                self.scroll_region_area()
            elif self.op_round == 5:
                for _ in range(self.op_round):  # 回到原点
                    self.scroll_region_area(-1)
                    time.sleep(0.5)
                self.scroll_region_area(-1)
            else:
                self.scroll_region_area(-1)
            time.sleep(1)
        else:
            time.sleep(0.2)
            return Operation.SUCCESS

    def click_target_region(self, screen) -> bool:
        """
        在右侧找到点击区域并点击
        :param screen:
        :return:
        """
        return self.ctx.controller.click_ocr(screen, self.region.cn, rect=ChooseRegion.click_rect)

    def scroll_region_area(self, d: int = 1):
        """
        在选择区域的地方滚动鼠标
        :param d: 滚动距离 正向下 负向上
        :return:
        """
        self.ctx.controller.scroll(ChooseRegion.scroll_distance * d, pos=ChooseRegion.scroll_pos)
