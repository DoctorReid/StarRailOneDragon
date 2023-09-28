import time

import cv2

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
            if not ctx.running:
                return False
            try_times += 1
            screen = ctrl.screenshot()
            planet = large_map.get_planet(screen, ctx.ocr)
            if planet is not None and planet.id == self.planet.id:
                return True

            if planet is not None:  # 在大地图
                log.info('当前在大地图 准备选择 星轨航图')
                result = self.open_choose_planet(screen, ctrl)
                if not result:
                    log.error('当前左上方无星球信息 右方找不到星轨航图')
                time.sleep(1)
                continue
            else:
                log.info('当前在星际 准备选择 %s', self.planet.cn)
                self.choose_planet(screen, ctrl)
                time.sleep(1)
                continue

    def open_choose_planet(self, screen, ctrl) -> bool:
        """
        点击 星轨航图 准备选择星球
        :param screen: 屏幕截图
        :param ctrl: 控制器
        :return: 找到 星轨航图
        """
        return ctrl.click_ocr(screen, word=gt('星轨航图'), rect=ChoosePlanet.xght_rect)

    def choose_planet(self, screen, ctrl) -> bool:
        """
        点击对应星球 这里比较奇怪 需要长按才能有效
        :param screen: 屏幕截图
        :param ctrl: 控制器
        :return: 找到星球
        """
        # 二值化后更方便识别字体
        gray = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)
        _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        return ctrl.click_ocr(mask, gt(self.planet.cn), click_offset=(0, -100), press_time=1)
