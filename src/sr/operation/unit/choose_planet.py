import time
from typing import ClassVar, List, Optional

import cv2
from cv2.typing import MatLike

from basic import Point, Rect
from basic.i18_utils import gt
from basic.img import MatchResult
from basic.log_utils import log
from sr.const import STANDARD_RESOLUTION_W
from sr.const.map_const import Planet, PLANET_LIST, best_match_planet_by_name
from sr.context import Context
from sr.image.sceenshot import large_map
from sr.operation import Operation, OperationOneRoundResult
from sr.screen_area.screen_large_map import ScreenLargeMap


class ChoosePlanet(Operation):

    xght_rect: ClassVar[Rect] = Rect(1580, 120, 1750, 160)  # 星轨航图 所在坐标

    def __init__(self, ctx: Context, planet: Planet):
        """
        在大地图页面 选择到对应的星球
        默认已经打开大地图了
        :param planet: 目标星球
        """
        super().__init__(ctx, 10, op_name=gt('选择星球 %s', 'ui') % planet.display_name)
        self.planet: Planet = planet  # 目标星球

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        # 根据左上角判断当前星球是否正确
        planet = large_map.get_planet(screen, self.ctx.ocr)
        if planet is not None and planet.np_id == self.planet.np_id:
            return Operation.round_success()

        if planet is not None:  # 在大地图
            log.info('当前在大地图 准备选择 星轨航图')
            area = ScreenLargeMap.STAR_RAIL_MAP.value
            click = self.find_and_click_area(area, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                return Operation.round_wait(wait=1)
            elif click == Operation.OCR_CLICK_NOT_FOUND:  # 点了传送点 星轨航图 没出现
                self.ctx.controller.click(large_map.EMPTY_MAP_POS)
                return Operation.round_wait(wait=0.5)
            else:
                return Operation.round_retry('点击星轨航图失败', wait=0.5)
        else:
            log.info('当前在星轨航图')
            planet_list = self.get_planet_pos(screen)

            target_pos: Optional[MatchResult] = None
            with_planet_before_target: bool = False  # 当前屏幕上是否有目标星球之前的星球

            for planet in PLANET_LIST:
                for planet_mr in planet_list:
                    if planet_mr.data == self.planet:
                        target_pos = planet_mr
                        break
                    if planet_mr.data == planet:
                        with_planet_before_target = True

                if target_pos is not None:
                    break

                if planet == self.planet:
                    break

            if target_pos is not None:
                self.choose_planet_by_pos(target_pos)
                return Operation.round_wait(wait=3)
            else:  # 当前屏幕没有目标星球的情况
                drag_from = Point(STANDARD_RESOLUTION_W // 2, 100)
                drag_to = drag_from + Point(-400 if with_planet_before_target else 400, 0)
                self.ctx.controller.click(drag_from)  # 这里比较神奇 直接拖动第一次会失败
                self.ctx.controller.drag_to(drag_to, drag_from)
                return Operation.round_retry(wait=1)

    def get_planet_pos(self, screen: MatLike) -> List[MatchResult]:
        """
        获取星轨航图上 星球名字的位置
        :param screen: 屏幕截图
        :return: 星球位置 data中是对应星球 Planet
        """
        # 二值化后更方便识别字体
        gray = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)
        _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

        words = [p.cn for p in PLANET_LIST]
        ocr_map = self.ctx.ocr.match_words(mask, words, lcs_percent=self.gc.planet_lcs_percent)

        result_list: List[MatchResult] = []
        for ocr_word, mrl in ocr_map.items():
            planet = best_match_planet_by_name(ocr_word)
            if planet is not None:
                mr = mrl.max
                mr.data = planet
                result_list.append(mr)

        return result_list

    def choose_planet_by_pos(self, pos: MatchResult):
        """
        根据目标位置 点击选择星球
        :param pos:
        :return:
        """
        drag_from = pos.center
        drag_to = drag_from + Point(0, -100)
        self.ctx.controller.drag_to(drag_to, drag_from)  # 这里比较奇怪 需要聚焦一段时间才能点击到星球
        time.sleep(0.1)
        self.ctx.controller.click(drag_to, press_time=1)
