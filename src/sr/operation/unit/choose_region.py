import time

from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.constants.map import Planet, Region, PLANET_2_REGION
from sr.context import Context
from sr.image.sceenshot import large_map
from sr.operation import Operation


class ChooseRegion(Operation):

    scroll_distance = -2000

    def __init__(self, ctx: Context, region: Region):
        """
        默认已经打开了大地图 且选择了正确的星球。
        选择目标区域
        :param region: 区域
        """
        super().__init__(ctx, 10)
        self.planet: Planet = region.planet
        self.region: Region = region
        self.scroll_direction: int = None

    def run(self) -> int:
        screen = self.screenshot()

        planet = large_map.get_planet(screen, self.ctx.ocr)
        if planet is None or planet != self.planet:
            return Operation.FAIL  # 目前不在目标大地图了

        if self.check_tp_and_cancel(screen):
            return Operation.WAIT

        # 判断当前选择区域是否目标区域
        current_region_name = large_map.get_active_region_name(screen, self.ctx.ocr)
        target_region_name = gt(self.region.ocr_str)
        log.info('当前选择区域 %s', current_region_name)
        if current_region_name is None or current_region_name.find(target_region_name) == -1:
            find = self.click_target_region(screen)

            if not find:
                self.scroll_when_no_target_region(current_region_name)
                return Operation.RETRY
            else:
                time.sleep(0.2)
                return Operation.WAIT

        # 需要选择层数
        if self.region.level != 0:
            level_str = large_map.get_active_level(screen, self.ctx.ocr)
            log.info('当前层数 %s', level_str)
            if level_str is None:
                log.error('未找到当前选择的层数')
            target_level_str = gt('%d层' % self.region.level)
            if target_level_str != level_str:
                cl = self.click_target_level(screen, target_level_str)
                time.sleep(0.5)
                if not cl:
                    log.error('未成功点击层数')
                    return Operation.RETRY
                else:
                    return Operation.WAIT
            else:  # 已经是目标楼层
                return Operation.SUCCESS

        return Operation.SUCCESS

    def click_target_region(self, screen) -> bool:
        """
        在右侧找到点击区域并点击
        :param screen:
        :return:
        """
        return self.ctx.controller.click_ocr(screen, self.region.ocr_str, rect=large_map.REGION_LIST_RECT, threshold=0.4)

    def scroll_when_no_target_region(self, current_region_name):
        """
        当前找不到目标区域时 进行滚动
        :param current_region_name: 当前选择的区域
        :return:
        """
        log.info('当前界面未发现 %s 准备滚动', self.region.cn)
        if current_region_name is None and self.scroll_direction is None:  # 判断不了当前选择区域的情况 就先向下滚动5次 再向上滚动5次
            if self.op_round < 5:
                self.scroll_region_area()
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
                    if current_region_name.find(gt(r.ocr_str)) != -1:
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
        self.ctx.controller.scroll(-5 * d, pos=large_map.REGION_LIST_PART_CENTER)  # TODO 有问题 一直滚动固定距离

    def click_target_level(self, screen, target_level_str: str) -> bool:
        """
        点击目标层数
        :param screen: 大地图界面截图
        :param target_level_str: 层数
        :return:
        """
        part, _ = cv2_utils.crop_image(screen, large_map.LEVEL_LIST_PART)
        return self.ctx.controller.click_ocr(part, target_level_str, click_offset=large_map.LEVEL_LIST_PART[:2],
                                             same_word=True)

    def check_tp_and_cancel(self, screen) -> bool:
        """
        检测右边是否出现传送 有的话 点一下空白位置取消
        :param screen:
        :return:
        """
        tp_btn_part, _ = cv2_utils.crop_image(screen, large_map.TP_BTN_RECT)
        # cv2_utils.show_image(tp_btn_part, win_name='tp_btn_part')
        tp_btn_ocr = self.ctx.ocr.match_words(tp_btn_part, [gt('传送')], threshold=0.4)
        if len(tp_btn_ocr) > 0:
            return self.ctx.controller.click(large_map.EMPTY_MAP_POS)
        return False