import random
import time
from typing import ClassVar, List

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context.context import Context
from sr.image.sceenshot import screen_state, mini_map
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.operation import Operation, OperationOneRoundResult, OperationResult
from sr.screen_area.screen_normal_world import ScreenNormalWorld
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sr.sim_uni.op.sim_uni_move.sim_uni_move_by_detect import turn_to_detected_object
from sryolo.detector import draw_detections, DetectObjectResult


class SimUniMoveToEnemyByDetect(Operation):

    STATUS_ARRIVAL: ClassVar[str] = '已到达'
    STATUS_FIGHT: ClassVar[str] = '遭遇战斗'
    STATUS_NO_ENEMY: ClassVar[str] = '识别不到敌人'

    def __init__(self, ctx: Context):
        """
        根据画面识别怪的位置 朝怪移动。
        进入之前 应该确保当前朝向能识别到怪，本操作不会旋转去找怪
        停下来的条件有
        - 找不到怪
        - 被怪物锁定
        :param ctx:
        """
        super().__init__(ctx,
                         op_name=gt('向怪物移动', 'ui'),
                         timeout_seconds=20,  # 理论上移动目标都比较近 不可能20秒还没有到达
                         )

        self.no_enemy_times: int = 0  # 没有发现敌人的次数
        self.start_move_time: float = 0  # 开始移动的时间

        self.last_debug_time: float = 0

    def _execute_one_round(self) -> OperationOneRoundResult:
        now = time.time()
        screen = self.screenshot()

        # 不在大世界 可能被袭击了
        if not screen_state.is_normal_in_world(screen, self.ctx.im):
            return self.enter_battle(False)

        # 被怪锁定了
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        mm_info = mini_map.analyse_mini_map(mm)
        if mini_map.is_under_attack_new(mm_info, danger=True):
            return self.enter_battle(True)

        # 移动2秒后 如果丢失了目标 停下来
        if self.ctx.controller.is_moving and now - self.start_move_time >= 2 and self.no_enemy_times > 0:
            self.ctx.controller.stop_moving_forward()
            return self.round_wait()

        # 进行目标识别判断后续动作
        return self.detect_screen(screen)

    def enter_battle(self, in_world: bool) -> OperationOneRoundResult:
        """
        进入战斗
        :return:
        """
        if in_world:
            state = ScreenNormalWorld.CHARACTER_ICON.value.status
        else:
            state = ScreenState.BATTLE.value
        op = SimUniEnterFight(self.ctx, first_state=state)
        op_result = op.execute()
        if op_result.success:
            return self.round_success(SimUniMoveToEnemyByDetect.STATUS_FIGHT)
        else:
            return self.round_by_op(op_result)

    def detect_screen(self, screen: MatLike) -> OperationOneRoundResult:
        """
        对画面进行识别 根据结果进行后续判断
        :param screen:
        :return:
        """
        frame_result = self.ctx.yolo_detector.sim_uni_yolo.detect(screen)
        normal_enemy_result = []
        can_attack: bool = False
        for result in frame_result.results:
            if result.detect_class.class_cate == '普通怪':
                normal_enemy_result.append(result)
            elif result.detect_class.class_cate in ['界面提示被锁定', '界面提示可攻击']:
                can_attack = True

        if self.ctx.one_dragon_config.is_debug:
            cv2_utils.show_image(draw_detections(frame_result), win_name='SimUniMoveToEnemyByDetect')
            if len(frame_result.results) > 3 and random.random() < 0.5:
                self.save_screenshot()

        if can_attack:
            return self.enter_battle(True)
        elif len(normal_enemy_result) > 0:
            return self.handle_enemy(normal_enemy_result)
        else:
            return self.handle_no_enemy()

    def handle_no_enemy(self) -> OperationOneRoundResult:
        """
        处理当前画面没有中没有怪的情况
        :return:
        """
        self.no_enemy_times += 1
        if self.no_enemy_times >= 9:
            return self.round_fail(SimUniMoveToEnemyByDetect.STATUS_NO_ENEMY)

        # 第一次向右转一点 后续就在固定范围内晃动
        if self.no_enemy_times == 1:
            angle = 15
        else:
            angle = -30 if self.no_enemy_times % 2 == 0 else 30

        self.ctx.controller.turn_by_angle(angle)
        return self.round_wait(SimUniMoveToEnemyByDetect.STATUS_NO_ENEMY, wait=0.5)

    def handle_enemy(self, enemy_pos_list: List[DetectObjectResult]) -> OperationOneRoundResult:
        """
        处理有敌人的情况
        :param enemy_pos_list: 识别的敌人列表
        :return:
        """
        self.no_enemy_times = 0
        enemy = enemy_pos_list[0]  # 先固定找第一个
        turn_to_detected_object(self.ctx, enemy)
        self.ctx.controller.start_moving_forward()
        self.start_move_time = time.time()
        return self.round_wait()

    def _after_operation_done(self, result: OperationResult):
        """
        无论以哪种方式结束 都停止移动
        :param result:
        :return:
        """
        super()._after_operation_done(result)
        self.ctx.controller.stop_moving_forward()
