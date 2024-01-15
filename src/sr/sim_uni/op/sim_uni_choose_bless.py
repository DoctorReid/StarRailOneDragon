import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Optional, List, ClassVar

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import MatchResult, cv2_utils
from basic.log_utils import log
from sr.context import Context
from sr.image.cn_ocr_matcher import CnOcrMatcher
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult
from sr.sim_uni.sim_uni_const import match_best_bless_by_ocr, SimUniBless
from sr.sim_uni.sim_uni_priority import SimUniBlessPriority


class SimUniChooseBless(Operation):
    # 3个祝福的情况 每个祝福有2个框 分别是名字、命途
    BLESS_3_RECT_LIST: ClassVar[List[List[Rect]]] = [
        [Rect(390, 475, 710, 510), Rect(430, 730, 670, 760)],
        [Rect(800, 475, 1120, 510), Rect(840, 730, 1080, 760)],
        [Rect(1210, 475, 1530, 510), Rect(1250, 730, 1490, 760)],
    ]

    # 2个祝福的情况
    BLESS_2_RECT_LIST: ClassVar[List[List[Rect]]] = [
        [Rect(600, 475, 900, 510), Rect(640, 730, 860, 760)],
        [Rect(1010, 475, 1310, 510), Rect(1050, 730, 1270, 760)],
    ]

    # 1个祝福的情况
    BLESS_1_RECT_LIST: ClassVar[List[List[Rect]]] = [
        [Rect(800, 475, 1120, 520), Rect(840, 730, 1080, 760)],
    ]

    # 楼层开始前祝福的情况 开拓祝福
    BLESS_BEFORE_LEVEL_RECT_LIST: ClassVar[List[List[Rect]]] = [
        [Rect(423, 475, 720, 520), Rect(463, 790, 680, 820)],
        [Rect(812, 475, 1109, 520), Rect(852, 790, 1069, 820)],
        [Rect(1200, 475, 1496, 520), Rect(1240, 790, 1456, 820)],
    ]

    BLESS_TITLE_RECT = Rect(400, 475, 1530, 510)
    BLESS_PATH_RECT = Rect(400, 730, 1530, 760)

    BLESS_TITLE_BEFORE_LEVEL_RECT = Rect(390, 475, 1530, 510)
    BLESS_PATH_BEFORE_LEVEL_RECT = Rect(390, 730, 1530, 760)

    RESET_BTN: ClassVar[Rect] = Rect(1160, 960, 1460, 1000)  # 重置祝福
    CONFIRM_BTN: ClassVar[Rect] = Rect(1530, 960, 1865, 1000)  # 确认
    CONFIRM_BEFORE_LEVEL_BTN: ClassVar[Rect] = Rect(783, 953, 1133, 997)  # 确认 - 楼层开始前

    def __init__(self, ctx: Context,
                 priority: Optional[SimUniBlessPriority] = None,
                 skip_first_screen_check: bool = True,
                 before_level_start: bool = False):
        """
        按照优先级选择祝福
        :param ctx:
        :param priority: 祝福优先级
        :param skip_first_screen_check: 是否跳过第一次的画面状态检查
        :param before_level_start: 是否在楼层开始的选择
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('选择祝福', 'ui')))

        self.priority: Optional[SimUniBlessPriority] = priority  # 祝福优先级
        self.skip_first_screen_check: bool = skip_first_screen_check  # 是否跳过第一次的画面状态检查 用于提速
        self.first_screen_check: bool = True  # 是否第一次检查画面状态
        self.before_level_start: bool = before_level_start

    def _init_before_execute(self):
        super()._init_before_execute()
        self.first_screen_check = True

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        if not self.first_screen_check or not self.skip_first_screen_check:
            self.first_screen_check = False
            if not screen_state.in_sim_uni_choose_bless(screen, self.ctx.ocr):
                return Operation.round_retry('未在模拟宇宙-选择祝福页面', wait=1)

        bless_pos_list: List[MatchResult] = self._get_bless_pos(screen)
        # bless_pos_list: List[MatchResult] = self._get_bless_pos_v2(screen)

        if len(bless_pos_list) == 0:
            return Operation.round_retry('未识别到祝福', wait=1)

        target_bless_pos: Optional[MatchResult] = self._get_bless_to_choose(screen, bless_pos_list)
        if target_bless_pos is None:
            self.ctx.controller.click(SimUniChooseBless.RESET_BTN.center)
            return Operation.round_retry('重置祝福', wait=1)
        else:
            self.ctx.controller.click(target_bless_pos.center)
            time.sleep(0.25)
            if self.before_level_start:
                confirm_point = SimUniChooseBless.CONFIRM_BEFORE_LEVEL_BTN.center
            else:
                confirm_point = SimUniChooseBless.CONFIRM_BTN.center
            self.ctx.controller.click(confirm_point)
            return Operation.round_success(wait=2)

    def _get_bless_pos(self, screen: MatLike) -> List[MatchResult]:
        """
        获取屏幕上的祝福的位置
        :param screen: 屏幕截图
        :return: MatchResult.data 中是对应的祝福 Bless
        """
        if self.before_level_start:
            return self._get_bless_pos_before_level(screen)
        else:  # 这么按顺序写 可以保证最多只识别3次祝福
            bless_3 = self._get_bless_pos_3(screen)
            if len(bless_3) > 0:
                return bless_3

            bless_2 = self._get_bless_pos_2(screen)
            if len(bless_2) > 0:
                return bless_2

            bless_1 = self._get_bless_pos_1(screen)
            if len(bless_1) > 0:
                return bless_1

        return []

    def _get_bless_pos_3(self, screen: MatLike) -> List[MatchResult]:
        """
        获取屏幕上的祝福的位置 - 3个祝福的情况
        :param screen: 屏幕截图
        :return: MatchResult.data 中是对应的祝福 Bless
        """
        return self._get_bless_pos_by_rect_list(screen, SimUniChooseBless.BLESS_3_RECT_LIST)

    def _get_bless_pos_2(self, screen: MatLike) -> List[MatchResult]:
        """
        获取屏幕上的祝福的位置 - 2个祝福的情况
        :param screen: 屏幕截图
        :return: MatchResult.data 中是对应的祝福 Bless
        """
        return self._get_bless_pos_by_rect_list(screen, SimUniChooseBless.BLESS_2_RECT_LIST)

    def _get_bless_pos_1(self, screen: MatLike) -> List[MatchResult]:
        """
        获取屏幕上的祝福的位置 - 1个祝福的情况
        :param screen: 屏幕截图
        :return: MatchResult.data 中是对应的祝福 Bless
        """
        return self._get_bless_pos_by_rect_list(screen, SimUniChooseBless.BLESS_1_RECT_LIST)

    def _get_bless_pos_before_level(self, screen: MatLike) -> List[MatchResult]:
        """
        获取屏幕上的祝福的位置 - 楼层开始前
        :param screen: 屏幕截图
        :return: MatchResult.data 中是对应的祝福 Bless
        """
        return self._get_bless_pos_by_rect_list(screen, SimUniChooseBless.BLESS_BEFORE_LEVEL_RECT_LIST)

    def _get_bless_pos_by_rect_list(self, screen: MatLike,
                                    rect_list: List[List[Rect]]) -> List[MatchResult]:
        bless_list: List[MatchResult] = []

        for bless_rect_list in rect_list:
            path_part, _ = cv2_utils.crop_image(screen, bless_rect_list[1])
            path_ocr = self.ctx.ocr.ocr_for_single_line(path_part)
            # cv2_utils.show_image(path_part, wait=0)
            if path_ocr is None or len(path_ocr) == 0:
                break  # 其中有一个位置识别不到就认为不是使用这些区域了 加速这里的判断

            title_part, _ = cv2_utils.crop_image(screen, bless_rect_list[0])
            title_ocr = self.ctx.ocr.ocr_for_single_line(title_part)

            bless = match_best_bless_by_ocr(title_ocr, path_ocr)

            if bless is not None:
                log.info('识别到祝福 %s', bless)
                bless_list.append(MatchResult(1,
                                              bless_rect_list[0].x1, bless_rect_list[0].y1,
                                              bless_rect_list[0].width, bless_rect_list[0].height,
                                              data=bless))

        return bless_list

    def _get_bless_pos_v2(self, screen: MatLike) -> List[MatchResult]:
        """
        获取屏幕上的祝福的位置 总共识别两次
        一行标题 - 0.44s
        一行命途 - 1.26s (可能是几个黑色点导致的文本推理变多)
        :param screen: 屏幕截图
        :return:
        """
        if self.before_level_start:
            title_rect = SimUniChooseBless.BLESS_TITLE_BEFORE_LEVEL_RECT
            path_rect = SimUniChooseBless.BLESS_PATH_BEFORE_LEVEL_RECT
        else:
            title_rect = SimUniChooseBless.BLESS_TITLE_RECT
            path_rect = SimUniChooseBless.BLESS_PATH_RECT

        title_part = cv2_utils.crop_image_only(screen, title_rect)
        # cv2_utils.show_image(title_part, win_name='title_part', wait=0)
        title_ocr_map = self.ctx.ocr.run_ocr(title_part)

        path_part = cv2_utils.crop_image_only(screen, path_rect)
        # cv2_utils.show_image(path_part, win_name='path_part', wait=0)
        path_ocr_map = self.ctx.ocr.run_ocr(path_part)

        title_pos_list: List[MatchResult] = []
        path_pos_list: List[MatchResult] = []
        for title, title_mrl in title_ocr_map.items():
            for title_mr in title_mrl:
                title_pos_list.append(title_mr)

        for path, path_mrl in path_ocr_map.items():
            for path_mr in path_mrl:
                path_pos_list.append(path_mr)

        bless_list: List[MatchResult] = []

        for title_pos in title_pos_list:
            title_ocr = title_pos.data
            for path_pos in path_pos_list:
                path_ocr = path_pos.data

                if abs(title_pos.center.x - path_pos.center.x) > 20:
                    continue

                bless = match_best_bless_by_ocr(title_ocr, path_ocr)
                if bless is None:
                    continue

                log.info('识别到祝福 %s', bless)
                bless_list.append(MatchResult(1,
                                              title_pos.x, title_pos.y,
                                              path_pos.right_bottom.x, path_pos.right_bottom.y,
                                              data=bless))

        return bless_list

    def _get_bless_pos_v3(self, screen: MatLike, rect_list: List[List[Rect]]) -> List[MatchResult]:
        """
        获取屏幕上的祝福的位置 并发地进行识别
        单个模型并发识别有线程安全问题 多个模型的并发识别的性能也不够高
        :param screen:
        :param rect_list:
        :return:
        """
        bless_list: List[MatchResult] = []

        images: List[MatLike] = []
        rects: List[Rect] = []
        for bless_rect_list in rect_list:
            path_part, _ = cv2_utils.crop_image(screen, bless_rect_list[1], copy=True)
            rects.append(bless_rect_list[1])
            images.append(path_part)

            title_part, _ = cv2_utils.crop_image(screen, bless_rect_list[0], copy=True)
            rects.append(bless_rect_list[0])
            images.append(title_part)

        ocr_list = [CnOcrMatcher() for _ in images]
        executor = ThreadPoolExecutor(thread_name_prefix='bless')
        future_list: List[Future] = []
        for i in range(len(images)):
            future_list.append(
                executor.submit(ocr_list[i].ocr_for_single_line, images[i], None, True)
            )

        st = time.time()
        ocr_list = []
        for future in future_list:
            ocr_list.append(future.result(1))
        for i in range(len(ocr_list)):
            if i % 2 == 1:
                continue
            path = ocr_list[i]
            title = ocr_list[i + 1]
            if path is None or title is None:
                continue

            bless = match_best_bless_by_ocr(title, path)
            if bless is None:
                continue

            log.info('识别到祝福 %s', bless)
            bless_list.append(MatchResult(1,
                                          rects[i].x1, rects[i].y1,
                                          rects[i+1].x2, rects[i+1].y2,
                                          data=bless))

        print(time.time() - st)
        return bless_list

    def _can_reset(self, screen: MatLike) -> bool:
        """
        判断当前是否能重置
        :param screen: 屏幕祝福
        :return:
        """
        part, _ = cv2_utils.crop_image(screen, SimUniChooseBless.RESET_BTN)
        lower_color = np.array([220, 220, 220], dtype=np.uint8)
        upper_color = np.array([255, 255, 255], dtype=np.uint8)
        white_part = cv2.inRange(part, lower_color, upper_color)

        ocr_result = self.ctx.ocr.ocr_for_single_line(white_part)

        return str_utils.find_by_lcs(gt('重置祝福', 'ocr'), ocr_result)

    def _get_bless_to_choose(self, screen: MatLike, bless_pos_list: List[MatchResult]) -> Optional[MatchResult]:
        """
        根据优先级选择对应的祝福
        :param bless_pos_list: 祝福列表
        :return:
        """
        bless_list = [bless.data for bless in bless_pos_list]
        can_reset = self._can_reset(screen)
        target_idx = SimUniChooseBless.get_bless_by_priority(bless_list, self.priority, can_reset)
        if target_idx is None:
            return None
        else:
            return bless_pos_list[target_idx]

    @staticmethod
    def get_bless_by_priority(bless_list: List[SimUniBless], priority: Optional[SimUniBlessPriority], can_reset: bool) -> Optional[int]:
        """
        根据优先级选择对应的祝福
        :param bless_list: 可选的祝福列表
        :param priority: 优先级
        :param can_reset: 当前是否可以重置
        :return: 选择祝福的下标
        """
        if priority is None:
            return 0

        for idx, bless in enumerate(bless_list):
            if bless.path.value == priority.first_path:
                return idx

        if can_reset:
            return None

        return 0
