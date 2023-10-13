import time

from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.constants.map import Planet, Region
from sr.context import Context
from sr.control import GameController
from sr.image.sceenshot import large_map
from sr.operation import Operation


class ChooseRegion(Operation):

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

        # 判断当前选择区域是否目标区域
        current_region = large_map.get_active_region_name(screen, self.ctx.ocr)
        log.info('当前选择区域 %s', current_region)
        if current_region != gt(self.region.cn):
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
        return self.ctx.controller.click_ocr(screen, self.region.cn, rect=large_map.REGION_LIST_PART)

    def scroll_region_area(self, d: int = 1):
        """
        在选择区域的地方滚动鼠标
        :param d: 滚动距离 正向下 负向上
        :return:
        """
        self.ctx.controller.scroll(ChooseRegion.scroll_distance * d, pos=large_map.REGION_LIST_PART_CENTER)

    def click_target_level(self, screen, target_level_str: str) -> bool:
        """
        点击目标层数
        :param screen: 大地图界面截图
        :param target_level_str: 层数
        :return:
        """
        part = cv2_utils.crop_image(screen, large_map.LEVEL_LIST_PART)
        return self.ctx.controller.click_ocr(part, target_level_str, click_offset=large_map.LEVEL_LIST_PART[:2],
                                             same_word=True)