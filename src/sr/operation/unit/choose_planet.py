import time
from typing import ClassVar

import cv2

from basic import Point, Rect
from basic.i18_utils import gt
from basic.log_utils import log
from sr.const import STANDARD_RESOLUTION_W, STANDARD_RESOLUTION_H, STANDARD_CENTER_POS
from sr.const.map_const import Planet
from sr.context import Context
from sr.image.sceenshot import large_map
from sr.operation import Operation


class ChoosePlanet(Operation):

    xght_rect: ClassVar[Rect] = Rect(1580, 120, 1750, 160)  # 星轨航图 所在坐标

    def __init__(self, ctx: Context, planet: Planet):
        """
        在大地图页面 选择到对应的星球
        默认已经打开大地图了
        :param planet: 目标星球
        """
        super().__init__(ctx, 10, op_name=gt('选择星球 %s', 'ui') % planet.display_name)
        self.planet: Planet = planet

    def _execute_one_round(self) -> int:
        screen = self.screenshot()
        # 根据左上角判断当前星球是否正确
        planet = large_map.get_planet(screen, self.ctx.ocr)
        if planet is not None and planet.np_id == self.planet.np_id:
            return Operation.SUCCESS

        if planet is not None:  # 在大地图
            log.info('当前在大地图 准备选择 星轨航图')
            result = self.open_choose_planet(screen)
            if not result:  # 当前左上方无星球信息 右方找不到星轨航图 可能被传送点卡住了
                self.ctx.controller.click(large_map.EMPTY_MAP_POS)
            time.sleep(1)
            return Operation.RETRY
        else:
            log.info('当前在星际 准备选择 %s', self.planet.cn)
            choose = self.choose_planet(screen)
            if not choose:
                drag_from = Point(STANDARD_RESOLUTION_W // 2, 100)
                drag_to = drag_from + Point(400 if (self.op_round % 2 == 0) else -400, 0)
                self.ctx.controller.drag_to(drag_to, drag_from)
            time.sleep(1)
            return Operation.RETRY

    def open_choose_planet(self, screen) -> bool:
        """
        点击 星轨航图 准备选择星球
        :param screen: 屏幕截图
        :return: 找到 星轨航图
        """
        return self.ctx.controller.click_ocr(screen, word=gt('星轨航图', 'ocr'), rect=ChoosePlanet.xght_rect,
                                             lcs_percent=self.gc.planet_lcs_percent)

    def choose_planet(self, screen) -> bool:
        """
        点击对应星球 这里比较奇怪 需要长按才能有效
        :param screen: 屏幕截图
        :return: 找到星球
        """
        # 二值化后更方便识别字体
        gray = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)
        _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        km = self.ctx.ocr.match_words(mask, words=[self.planet.cn], lcs_percent=self.gc.planet_lcs_percent)
        if len(km) == 0:
            return False
        for v in km.values():
            drag_from = v.max.center
            drag_to = drag_from + Point(0, -100)
            self.ctx.controller.drag_to(drag_to, drag_from)
            time.sleep(0.1)
            self.ctx.controller.click(drag_to, press_time=1)
        return True
