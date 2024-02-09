import time
from typing import Optional

from basic import str_utils, Point
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.const.map_const import Planet, Region, PLANET_2_REGION, best_match_region_by_name
from sr.context import Context
from sr.image.sceenshot import large_map
from sr.operation import Operation


class ChooseRegion(Operation):

    def __init__(self, ctx: Context, region: Region):
        """
        默认已经打开了大地图 且选择了正确的星球。
        选择目标区域
        :param region: 区域
        """
        super().__init__(ctx, 20, op_name=gt('选择区域 %s') % region.display_name)
        self.planet: Planet = region.planet
        self.region: Region = region
        self.scroll_direction: Optional[int] = None

    def _execute_one_round(self) -> int:
        screen = self.screenshot()

        planet = large_map.get_planet(screen, self.ctx.ocr)
        if planet is None or planet != self.planet:
            return Operation.FAIL  # 目前不在目标星球的大地图了

        if self.check_tp_and_cancel(screen):
            return Operation.RETRY

        # 判断当前选择区域是否目标区域
        current_region_name = large_map.get_active_region_name(screen, self.ctx.ocr)
        current_region = best_match_region_by_name(current_region_name, planet=self.planet)
        log.info('当前区域文本 %s 匹配区域名称 %s', current_region_name, current_region.cn if current_region is not None else '')

        is_current: bool = (current_region is not None and current_region.pr_id == self.region.pr_id)
        if not is_current:
            find = self.click_target_region(screen)
            if not find:
                self.scroll_when_no_target_region(current_region_name)
                return Operation.RETRY
            else:
                self.ctx.controller.click(large_map.EMPTY_MAP_POS)  # 将鼠标移开 防止OCR时候有一条白线 影响OCR结果
                time.sleep(1)
                return Operation.RETRY

        # 需要选择层数
        if self.region.floor != 0:
            current_floor_str = large_map.get_active_floor(screen, self.ctx.ocr)
            log.info('当前层数 %s', current_floor_str)
            if current_floor_str is None:
                log.error('未找到当前选择的层数')
            target_floor_str = gt('%d层' % self.region.floor, 'ocr')
            log.info('目标层数 %s', target_floor_str)
            if target_floor_str != current_floor_str:
                cl = self.click_target_floor(screen, target_floor_str)
                time.sleep(0.5)
                if not cl:
                    log.error('未成功点击层数')
                    return Operation.RETRY
                else:
                    return Operation.SUCCESS
            else:  # 已经是目标楼层
                return Operation.SUCCESS

        return Operation.SUCCESS

    def click_target_region(self, screen) -> bool:
        """
        在右侧找到点击区域并点击
        :param screen:
        :return:
        """
        return self.ctx.controller.click_ocr(screen, self.region.cn, rect=large_map.REGION_LIST_RECT,
                                             lcs_percent=self.gc.region_lcs_percent, merge_line_distance=40)

    def scroll_when_no_target_region(self, current_region_name):
        """
        当前找不到目标区域时 进行滚动
        :param current_region_name: 当前选择的区域
        :return:
        """
        log.info('当前界面未发现 %s 准备滚动', gt(self.region.cn, 'ui'))
        if current_region_name is None and self.scroll_direction is None:  # 判断不了当前选择区域的情况 就先向下滚动5次 再向上滚动5次
            log.info(self.op_round)
            if self.op_round < 5:
                self.scroll_region_area(1)
            elif self.op_round == 5:
                for _ in range(self.op_round):  # 回到原点
                    self.scroll_region_area(-1)
                    time.sleep(0.5)
                self.scroll_region_area(-1)
            else:
                self.scroll_region_area(-1)
        else:
            if self.scroll_direction is None:
                find_current: bool = False
                region_list = PLANET_2_REGION.get(self.region.planet.np_id)
                for r in region_list:
                    if r == self.region:
                        break
                    if str_utils.find_by_lcs(gt(r.cn, 'ocr'), current_region_name, ignore_case=True,
                                             percent=self.gc.region_lcs_percent):
                        find_current = True

                # 在找到目标区域前 当前区域已经出现 说明目标区域在下面 向下滚动
                self.scroll_direction = 1 if find_current else -1
            self.scroll_region_area(self.scroll_direction)

        time.sleep(1)

    def scroll_region_area(self, d: int = 1):
        """
        在选择区域的地方滚动鼠标
        :param d: 滚动距离 正向下 负向上
        :return:
        """
        drag_to = large_map.REGION_LIST_RECT.center
        drag_from = Point(0, d * 200) + drag_to
        self.ctx.controller.drag_to(start=drag_from, end=drag_to, duration=0.5)

    def click_target_floor(self, screen, target_floor_str: str) -> bool:
        """
        点击目标层数
        :param screen: 大地图界面截图
        :param target_floor_str: 层数
        :return:
        """
        return self.ctx.controller.click_ocr(screen, target_floor_str, rect=large_map.FLOOR_LIST_PART,
                                             same_word=True)

    def check_tp_and_cancel(self, screen) -> bool:
        """
        检测右边是否出现传送 有的话 点一下空白位置取消
        :param screen:
        :return:
        """
        tp_btn_part, _ = cv2_utils.crop_image(screen, large_map.TP_BTN_RECT)
        # cv2_utils.show_image(tp_btn_part, win_name='tp_btn_part')
        tp_btn_ocr = self.ctx.ocr.match_words(tp_btn_part, ['传送'])
        if len(tp_btn_ocr) > 0:
            return self.ctx.controller.click(large_map.EMPTY_MAP_POS)
        return False