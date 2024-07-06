import random
import time
from typing import ClassVar, Optional, List

from cv2.typing import MatLike

from basic import str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.context.context import Context
from sr.control import GameController
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult, OperationResult
from sr.operation.unit.interact import get_move_interact_words
from sr.screen_area.screen_normal_world import ScreenNormalWorld
from sr.sim_uni.op.sim_uni_move.sim_uni_move_by_detect import delta_angle_to_detected_object, turn_by_angle_slowly, \
    _MAX_TURN_ANGLE
from sryolo.detector import DetectObjectResult, draw_detections


class SimUniMoveToInteractByDetect(Operation):

    STATUS_ARRIVAL: ClassVar[str] = '已到达'
    STATUS_INTERACT: ClassVar[str] = '已交互'
    STATUS_NO_DETECT: ClassVar[str] = '识别不到交互目标'

    def __init__(self, ctx: Context,
                 interact_class: str,
                 interact_word: str,
                 interact_during_move: bool = False):
        """
        根据画面识别可交互内容的位置 并朝之移动。
        进入之前 应该确保当前朝向能识别到内容，本操作不会旋转太多去找识别目标
        停下来的条件有
        - 识别不到可交互内容
        - 可交互(单行文本)
        - 进行了交互
        :param ctx: 上下文
        :param interact_class: 需要交互的类型
        :param interact_word: 交互文本
        :param interact_during_move: 移动过程中不断尝试交互 开启后不会再使用OCR判断是否有可交互的文本。使用前需满足 1.移动时任何交互都能接受 2.交互后不在大世界
        """
        super().__init__(ctx,
                         op_name=gt(f'向 {interact_class} 移动', 'ui'),
                         timeout_seconds=20,  # 理论上移动目标都比较近 不可能20秒还没有到达
                         )

        self.no_detect_times: int = 0
        """没有识别的次数"""

        self.start_move_time: float = 0
        """开始移动的时间"""

        self.interact_class: str = interact_class
        """需要交互的类型"""

        self.interact_word: str = interact_word
        """交互文本"""

        self.interact_during_move: bool = interact_during_move
        """移动过程中不断尝试交互"""

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """

        self.existed_interact_word: Optional[str] = None
        """还没开始移动就已经存在的交互词"""

        self.find_in_last_detect: bool = False
        """在上一次识别中找到目标"""

    def _execute_one_round(self) -> OperationOneRoundResult:
        now = time.time()
        screen = self.screenshot()

        if self.existed_interact_word is None:
            self._check_interact_word(screen)

        if self.interact_during_move:  # 只有不断交互的情况 可能会进入不在大世界的页面
            in_world = screen_state.is_normal_in_world(screen, self.ctx.im)
        else:
            in_world = True

        if in_world:
            return self.handle_in_world(screen, now)
        else:
            return self.handle_not_in_world(screen, now)

    def handle_in_world(self, screen: MatLike, now: float) -> Optional[OperationOneRoundResult]:
        """
        处理在大世界的情况
        :param screen: 游戏画面
        :param now: 当前时间
        :return:
        """
        need_ocr = len(self.existed_interact_word) > 0 or not self.interact_during_move

        if not need_ocr:
            self.ctx.controller.interact(
                pos=ScreenNormalWorld.MOVE_INTERACT_SINGLE_LINE.value.center,
                interact_type=GameController.MOVE_INTERACT_TYPE
            )

        # 移动2秒后 如果丢失了目标 停下来
        if self.ctx.controller.is_moving and now - self.start_move_time >= 2 and self.no_detect_times > 0:
            self.ctx.controller.stop_moving_forward()
            return self.round_wait()

        # 只有不直接交互的情况下 使用OCR判断是否已经到达
        if need_ocr and self._check_interact_word(screen):
            self.ctx.controller.stop_moving_forward()
            return self.round_success(status=SimUniMoveToInteractByDetect.STATUS_ARRIVAL)

        # 判断交互物体的位置
        pos_list = self.get_interact_pos(screen)
        if len(pos_list) == 0:
            return self.handle_no_detect()
        else:
            return self.handle_detect(pos_list)

    def get_interact_pos(self, screen: MatLike) -> List[DetectObjectResult]:
        """
        识别画面中交互物体的位置
        :param screen: 游戏截图
        :return:
        """
        frame_result = self.ctx.yolo_detector.sim_uni_yolo.detect(screen)
        filter_results = []
        for result in frame_result.results:
            if not result.detect_class.class_cate == self.interact_class:
                continue
            filter_results.append(result)
        if self.ctx.one_dragon_config.is_debug:
            cv2_utils.show_image(draw_detections(frame_result), win_name='SimUniMoveToInteractByDetect')
            if len(frame_result.results) > 3 and random.random() < 0.3:
                self.save_screenshot()
        return filter_results

    def handle_no_detect(self) -> OperationOneRoundResult:
        """
        处理当前画面识别不到交互物体的情况
        :return:
        """
        if self.no_detect_times == 0 and self.find_in_last_detect:
            # 上一次能识别的 但转向之后刚好盖住了 那也可以开始移动了
            self.ctx.controller.start_moving_forward()
            self.start_move_time = time.time()

        self.no_detect_times += 1
        self.find_in_last_detect = False

        if self.no_detect_times >= 9:
            return self.round_fail(SimUniMoveToInteractByDetect.STATUS_NO_DETECT)

        # 第一次向右转一点 后续就在固定范围内晃动
        if self.no_detect_times == 1:
            angle = 15
        else:
            angle = -30 if self.no_detect_times % 2 == 0 else 30

        self.ctx.controller.turn_by_angle(angle)
        return self.round_wait(SimUniMoveToInteractByDetect.STATUS_NO_DETECT, wait=0.3)

    def handle_detect(self, pos_list: List[DetectObjectResult]) -> OperationOneRoundResult:
        """
        处理有交互物体的情况
        :param pos_list: 识别的列表
        :return:
        """
        self.find_in_last_detect = True
        self.no_detect_times = 0
        target = pos_list[0]  # 先固定找第一个
        target_angle = delta_angle_to_detected_object(target)
        log.debug('目标角度 %.2f', target_angle)
        turn_by_angle_slowly(self.ctx, target_angle)
        if abs(target_angle) >= _MAX_TURN_ANGLE * 2:  # 转向较大时 先完成转向再开始移动
            return self.round_wait()
        self.ctx.controller.start_moving_forward()
        self.start_move_time = time.time()
        return self.round_wait()

    def handle_not_in_world(self, screen: MatLike, now: float) -> Optional[OperationOneRoundResult]:
        """
        处理不在大世界的情况 暂时只有交互成功会进入
        :param screen: 游戏画面
        :param now: 当前时间
        :return:
        """
        self.ctx.controller.stop_moving_forward()
        return self.round_success(status=SimUniMoveToInteractByDetect.STATUS_INTERACT)

    def _after_operation_done(self, result: OperationResult):
        """
        无论以哪种方式结束 都停止移动
        :param result:
        :return:
        """
        super()._after_operation_done(result)
        self.ctx.controller.stop_moving_forward()

    def _check_interact_word(self, screen: MatLike) -> bool:
        """
        识别当前画面的交互文本
        :param screen:
        :return: 是否符合目标 可以交互
        """
        words = get_move_interact_words(self.ctx, screen, single_line=True)
        self.existed_interact_word = words[0].data if len(words) > 0 else ''
        log.debug('移动前已有交互 %s', self.existed_interact_word)
        is_target = self._is_target_interact()
        if is_target:  # 符合目标交互 就不需要OCR了
            self.existed_interact_word = ''

        return is_target

    def _is_target_interact(self) -> bool:
        return (
                len(self.existed_interact_word) > 0
                and str_utils.find_by_lcs(self.existed_interact_word, gt(self.interact_word, 'ocr'), percent=0.1)
        )
