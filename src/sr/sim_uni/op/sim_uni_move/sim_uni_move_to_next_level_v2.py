import time

import numpy as np
from cv2.typing import MatLike
from typing import Optional, List

from basic import str_utils
from basic.i18_utils import gt
from basic.log_utils import log
from sr.const import OPPOSITE_DIRECTION
from sr.context.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import OperationOneRoundResult, OperationResult
from sr.operation.unit.interact import get_move_interact_words
from sr.sim_uni.op.move_in_sim_uni import MoveToNextLevel
from sr.sim_uni.op.sim_uni_move.sim_uni_move_by_detect import delta_angle_to_detected_object, turn_by_angle_slowly
from sr.sim_uni.sim_uni_const import SimUniLevelType


class MoveToNextLevelV2(MoveToNextLevel):

    def __init__(self, ctx: Context, level_type: SimUniLevelType, with_entry: bool = False):
        """
        朝下一层入口走去 并且交互
        需确保不会被其它内容打断
        :param ctx:
        :param level_type: 当前楼层的类型 精英层的话 有可能需要确定
        :param with_entry: 调用这个指令时，是否已经看到了入口
        """
        super().__init__(ctx,
                         level_type=level_type,
                         random_turn=with_entry
                         )

        self.with_entry: bool = with_entry  # 是否已经看到入口了

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        super().handle_init()

        self.existed_interact_word: str = ''
        """还没开始移动就已经存在的交互词"""

        return None

    def _turn_to_next(self) -> OperationOneRoundResult:
        """
        寻找下层入口 并转向
        :return:
        """
        screen = self.screenshot()

        words = get_move_interact_words(self.ctx, screen, single_line=True)
        self.existed_interact_word = words[0].data if len(words) > 0 and len(words[0].data) > 0 else ''
        if len(self.existed_interact_word) > 0:
            log.debug('开始朝下层入口移动前已有交互 %s', self.existed_interact_word)
        if self._is_target_interact():  # 符合目标交互 就不需要OCR了
            self.existed_interact_word = ''

        frame_result = self.ctx.yolo_detector.sim_uni_yolo.detect(screen)

        entry_angles: List[float] = []
        for result in frame_result.results:
            delta_angle = delta_angle_to_detected_object(result)
            if result.detect_class.class_cate == '模拟宇宙下层入口':
                entry_angles.append(delta_angle)

        if len(entry_angles) > 0:
            self.with_entry = True
            avg_delta_angle = np.mean(entry_angles)
            log.debug('转向 %.2f', avg_delta_angle)
            turn_by_angle_slowly(self.ctx, avg_delta_angle)
            if avg_delta_angle < 30:  # 慢慢转过去
                return self.round_success()
            else:
                return self.round_wait(wait=0.1)
        elif self.with_entry:
            return self.round_success()
        else:
            self.ctx.controller.turn_by_angle(35)
            return self.round_retry(status=MoveToNextLevel.STATUS_ENTRY_NOT_FOUND, wait=0.5)

    def _move_and_interact(self) -> OperationOneRoundResult:
        now = time.time()

        # 等待最开始的交互词消失了 就可以无脑交互了
        need_ocr: bool = True  # 现在OCR速度快 可以保持使用

        screen = self.screenshot()

        in_world = screen_state.is_normal_in_world(screen, self.ctx.im)

        if not in_world:
            # 如果已经不在大世界画了 就认为成功了
            return self.round_success()

        if self.is_moving:
            if now - self.start_move_time > MoveToNextLevel.MOVE_TIME:
                self.ctx.controller.stop_moving_forward()
                self.is_moving = False
                self.move_times += 1

                if self.move_times >= 4:  # 正常情况不会连续移动这么多次都没有到下层入口 尝试脱困
                    self.ctx.controller.move(self.get_rid_direction, 1)
                    self.get_rid_direction = OPPOSITE_DIRECTION[self.get_rid_direction]
            elif need_ocr:
                interact = self._try_interact(screen)
                if interact is not None:
                    return interact
            return self.round_wait()
        else:
            type_list = MoveToNextLevel.get_next_level_type(screen, self.ctx.ih)
            if len(type_list) == 0:  # 当前没有入口 随便旋转看看
                if self.random_turn:
                    # 因为前面已经转向了入口 所以就算被遮挡 只要稍微转一点应该就能看到了
                    angle = (25 + 10 * self.op_round) * (1 if self.op_round % 2 == 0 else -1)  # 来回转动视角
                else:
                    angle = 35
                self.ctx.controller.turn_by_angle(angle)
                self.move_times = 0  # 没有识别到就是没有移动
                return self.round_retry(MoveToNextLevel.STATUS_ENTRY_NOT_FOUND, wait=1)

            target = MoveToNextLevel.get_target_entry(type_list, self.config)

            self._move_towards(target)
            return self.round_wait(wait=0.1)

    def _can_interact(self, screen: MatLike) -> bool:
        """
        当前是否可以交互
        :param screen: 屏幕截图
        :return:
        """
        words = get_move_interact_words(self.ctx, screen, single_line=True)
        self.existed_interact_word = words[0].data if len(words) > 0 and len(words[0].data) > 0 else ''
        return self._is_target_interact()

    def _is_target_interact(self) -> bool:
        return (
                len(self.existed_interact_word) > 0
                and str_utils.find_by_lcs(self.existed_interact_word, gt('区域', 'ocr'), percent=0.1)
        )

    def _after_operation_done(self, result: OperationResult):
        super()._after_operation_done(result)
        self.ctx.controller.stop_moving_forward()
