import time
from typing import Optional, List, ClassVar

from cv2.typing import MatLike

from basic import Rect
from basic.i18_utils import gt
from basic.img import MatchResult, cv2_utils
from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult
from sr.sim_uni.sim_uni_const import match_best_bless_by_ocr, SimUniBless
from sr.sim_uni.sim_uni_priority import SimUniBlessPriority


class SimUniChooseBless(Operation):

    BLESS_RECT_LIST: ClassVar[List[List[Rect]]] = [
        # 3个祝福的情况
        [Rect(390, 475, 710, 520), Rect(390, 730, 710, 760)],
        [Rect(800, 475, 1120, 520), Rect(800, 730, 1120, 760)],
        [Rect(1210, 475, 1530, 520), Rect(1210, 730, 1530, 760)],

        # 2个祝福的情况
        [Rect(600, 475, 900, 520), Rect(600, 730, 900, 760)],
        [Rect(1010, 475, 1310, 520), Rect(1010, 730, 1310, 760)],
    ]
    """祝福对应的框 每个祝福有2个框 分别是名字、命途"""

    RESET_BTN: ClassVar[Rect] = Rect(1160, 960, 1460, 1000)  # 重置祝福
    CONFIRM_BTN: ClassVar[Rect] = Rect(1530, 960, 1865, 1000)  # 确认

    def __init__(self, ctx: Context, priority: Optional[SimUniBlessPriority] = None):
        """
        按照优先级选择祝福
        :param ctx:
        :param priority: 祝福优先级
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('选择祝福', 'ui')))

        self.priority: Optional[SimUniBlessPriority] = priority  # 祝福优先级

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        if not screen_state.in_sim_uni_choose_bless(screen, self.ctx.ocr):
            return Operation.round_retry('未在模拟宇宙-选择祝福页面', wait=1)

        bless_pos_list: List[MatchResult] = self._get_bless_pos(screen)
        if len(bless_pos_list) == 0:
            return Operation.round_retry('未识别到祝福', wait=1)

        target_bless_pos: Optional[MatchResult] = self._get_bless_to_choose(screen, bless_pos_list)
        if target_bless_pos is None:
            self.ctx.controller.click(SimUniChooseBless.RESET_BTN.center)
            return Operation.round_retry('重置祝福', wait=1)
        else:
            self.ctx.controller.click(target_bless_pos.center)
            time.sleep(0.25)
            self.ctx.controller.click(SimUniChooseBless.CONFIRM_BTN.center)
            return Operation.round_success(wait=2)

    def _get_bless_pos(self, screen: MatLike) -> List[MatchResult]:
        """
        获取屏幕上的祝福的位置
        :param screen: 屏幕截图
        :return: MatchResult.data 中是对应的祝福 Bless
        """
        bless_list: List[MatchResult] = []

        for bless_rect_list in SimUniChooseBless.BLESS_RECT_LIST:
            path_part, _ = cv2_utils.crop_image(screen, bless_rect_list[1])
            path_ocr = self.ctx.ocr.ocr_for_single_line(path_part)
            if path_ocr is None or len(path_ocr) == 0:
                continue

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

    def _can_reset(self, screen: MatLike) -> bool:
        """
        判断当前是否能重置
        :param screen: 屏幕祝福
        :return:
        """
        part, _ = cv2_utils.crop_image(screen, SimUniChooseBless.RESET_BTN)
        return True

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
