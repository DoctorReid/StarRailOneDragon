import time

from basic.i18_utils import gt
from basic.log_utils import log
from sr.constants import get_planet_region_by_cn
from sr.context import Context, get_context
from sr.control import GameController
from sr.image.sceenshot import large_map
from sr.operation import Operation


class ChoosePlanet(Operation):

    xght_rect = (1580, 120, 1750, 160)  # 星轨航图 所在坐标

    def __init__(self, planet_cn: str):
        """
        在大地图页面 选择到对应的星球
        默认已经打开大地图了
        :param planet_cn: 目标星球的中文
        """
        self.planet = get_planet_region_by_cn(planet_cn)

    def execute(self) -> bool:
        ctx: Context = get_context()
        ctrl: GameController = ctx.controller
        try_times = 0

        while ctx.running and try_times < 10:
            try_times += 1
            screen = ctrl.screenshot()
            planet = large_map.get_planet(screen, ctx.ocr)
            if planet is not None and planet.id == self.plane.id:
                return True

            if planet is not None:  # 在大地图
                result = self.open_choose_planet(screen, ctrl)
                if not result:
                    log.error('当前左上方无星球信息 右方找不到星轨航图')
                time.sleep(1)
                continue
            else:  # 在星际图
                self.choose_planet(screen, ctrl)
                time.sleep(1)
                continue

    def open_choose_planet(self, screen, ctrl) -> bool:
        """
        点击 星轨航图 准备选择星球
        :param screen:
        :param ctrl:
        :return:
        """
        return ctrl.click_ocr(screen, gt('星轨航图'), rect=ChoosePlanet.xght_rect)

    def choose_planet(self, screen, ctrl):
        return ctrl.click_ocr(screen, gt(self.planet.cn), click_offset=(0, -50))
