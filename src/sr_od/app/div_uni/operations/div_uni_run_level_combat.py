import random
import time
from typing import Optional

from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.yolo.detect_utils import DetectFrameResult, DetectObjectResult
from sr_od.app.div_uni.div_uni_const import DivUniLevelType
from sr_od.app.div_uni.operations.div_uni_choose_curio import DivUniChooseCurio
from sr_od.app.div_uni.operations.div_uni_click_empty_after_interact import DivUniClickEmptyAfterInteract
from sr_od.app.div_uni.operations.div_uni_enter_fight import DivUniEnterFight
from sr_od.app.div_uni.operations.div_uni_handle_not_in_world import DivUniHandleNotInWorld
from sr_od.context.sr_context import SrContext
from sr_od.operations.sr_operation import SrOperation
from cv2.typing import MatLike


class DivUniRunLevelCombat(SrOperation):

    def __init__(self, ctx: SrContext):
        """
        战斗区域
        1. 直接往前移动
        2. 途中遇到敌袭则进行攻击
        3. 战斗后 完成本操作任务
        """
        SrOperation.__init__(self, ctx, op_name=gt('差分宇宙-战斗区域', 'ui'))

    @operation_node(name='识别画面并处理', is_start_node=True)
    def check_screen_and_run(self):
        self.ctx.controller.start_moving_forward()

        screenshot_time = time.time()
        screen = self.screenshot()

        screen_name = self.ctx.div_uni_context.check_screen_name(screen)
        if screen_name == '差分宇宙-大世界':
            return self.handle_in_world(screen, screenshot_time)
        else:
            return self.enter_battle(False)

    def handle_in_world(self, screen: MatLike, screenshot_time: float) -> OperationRoundResult:
        """
        大世界中 继续移动
        """
        frame_result = self.ctx.yolo_detector.div_uni_combat_detect(screen, screenshot_time)
        with_entry: bool = False
        can_attack: bool = False
        for result in frame_result.results:
            if result.detect_class.class_category in ['界面提示被锁定', '界面提示可攻击']:
                can_attack = True
            elif result.detect_class.class_category in ['模拟宇宙下层入口']:
                with_entry = True

        if self.ctx.env_config.is_debug:
            if len(frame_result.results) > 3 and random.random() < 0.5:
                self.save_screenshot()

        if can_attack:
            return self.enter_battle(True)
        elif with_entry:
            self.ctx.controller.stop_moving_forward()
            return self.round_success(status='识别到下层入口')
        else:
            return self.round_wait(status='未识别目标', wait=0.1)

    def enter_battle(self, in_world: bool) -> OperationRoundResult:
        """
        进入战斗
        :return:
        """
        if in_world:
            screen_name = '差分宇宙-大世界'
        else:
            screen_name = '差分宇宙-战斗'
        self.ctx.controller.stop_moving_forward()
        op = DivUniEnterFight(self.ctx, first_screen=screen_name)
        op_result = op.execute()
        if op_result.success:
            return self.round_wait(status=op_result.status)
        else:
            return self.round_retry(status=op_result.status, wait=1)

    def move_to_next_level(self, screen: MatLike, frame_result: DetectFrameResult) -> OperationRoundResult:
        """
        移动至下层入口
        :return:
        """
        target: DetectObjectResult = None
        for result in frame_result.results:
            if result.detect_class.class_category in ['模拟宇宙下层入口', '模拟宇宙下层入口未激活']:
                target = result
                break

        if target is None:
            return self.round_retry(status='未识别到下层入口')

        turn = self.ctx.div_uni_context.turn_to_target(target)
        if not turn and not self.ctx.controller.is_moving:
            self.ctx.controller.start_moving_forward()

        return self.round_wait(status='识别移动中')

    def handle_not_in_world(self) -> OperationRoundResult:
        op = DivUniHandleNotInWorld(self.ctx)
        op_result = op.execute()
        if op_result.success:
            return self.round_wait(status=op_result.status)
        else:
            return self.round_retry(status=op_result.status, wait=1)


def __debug():
    ctx = SrContext()
    ctx.ocr.init_model()
    ctx.init_by_config()
    ctx.init_for_div_uni()
    ctx.start_running()

    op = DivUniRunLevelCombat(ctx)
    op.execute()


if __name__ == '__main__':
    __debug()
