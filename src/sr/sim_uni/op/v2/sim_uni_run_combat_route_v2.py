from typing import List

import numpy as np
from cv2.typing import MatLike

from basic import cal_utils, Point
from basic.log_utils import log
from sr.context.context import Context
from sr.image.sceenshot import screen_state, mini_map, MiniMapInfo
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.operation import StateOperationEdge, StateOperationNode, Operation, OperationOneRoundResult
from sr.operation.unit.technique import UseTechnique
from sr.screen_area.screen_normal_world import ScreenNormalWorld
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sr.sim_uni.op.v2.sim_uni_move_v2 import SimUniMoveToEnemyByMiniMap, SimUniMoveToEnemyByDetect, \
    delta_angle_to_detected_object
from sr.sim_uni.op.v2.sim_uni_run_route_base_v2 import SimUniRunRouteBaseV2
from sr.sim_uni.sim_uni_const import SimUniLevelType, SimUniLevelTypeEnum


class SimUniRunCombatRouteV2(SimUniRunRouteBaseV2):

    def __init__(self, ctx: Context, level_type: SimUniLevelType = SimUniLevelTypeEnum.COMBAT.value):
        """
        区域-战斗
        1. 检测地图是否有红点
        2. 如果有红点 移动到最近的红点 并进行攻击。攻击一次后回到步骤1判断。
        3. 如果没有红点 识别敌对物种位置，向最大的移动，并进行攻击。攻击一次后回到步骤1判断。
        4. 如果没有红点也没有识别到敌对物种，检测下层入口位置，发现后进入下层移动。未发现则选择视角返回步骤1判断。
        """
        edges: List[StateOperationEdge] = []

        before_route = StateOperationNode('区域开始前', self._before_route)

        check = StateOperationNode('画面检测', self._check_screen)
        edges.append(StateOperationEdge(before_route, check))

        # 小地图有红点 就按红点移动
        move_by_red = StateOperationNode('向红点移动', self._move_by_red)
        edges.append(StateOperationEdge(check, move_by_red, status=SimUniRunRouteBaseV2.STATUS_WITH_RED))

        # 小地图没有红点 就在画面上找敌人
        detect_screen = StateOperationNode('识别敌人', self._detect_screen)
        edges.append(StateOperationEdge(check, detect_screen, status=SimUniRunRouteBaseV2.STATUS_NO_RED))
        # 找到了敌人就开始移动
        move_by_detect = StateOperationNode('向敌人移动', self._move_by_detect)
        edges.append(StateOperationEdge(detect_screen, move_by_detect, status=SimUniRunRouteBaseV2.STATUS_WITH_ENEMY))
        # 识别移动超时的话 尝试脱困
        detect_timeout = StateOperationNode('移动超时脱困', self._after_detect_timeout)
        edges.append(StateOperationEdge(move_by_detect, detect_timeout, success=False, status=Operation.STATUS_TIMEOUT))
        edges.append(StateOperationEdge(detect_timeout, check))
        # 到达后开始战斗
        fight = StateOperationNode('进入战斗', self._enter_fight)
        edges.append(StateOperationEdge(move_by_red, fight, status=SimUniMoveToEnemyByMiniMap.STATUS_ARRIVAL))
        # 识别到被锁定也进入战斗
        edges.append(StateOperationEdge(detect_screen, fight, status=SimUniRunRouteBaseV2.STATUS_WITH_DANGER))
        # 进行了战斗 就重新开始
        after_fight = StateOperationNode('战斗后处理', self._turn_to_previous_angle)
        edges.append(StateOperationEdge(fight, after_fight))
        edges.append(StateOperationEdge(after_fight, check))
        # 其它可能会进入战斗的情况
        edges.append(StateOperationEdge(check, after_fight, status=SimUniRunRouteBaseV2.STATUS_FIGHT))
        edges.append(StateOperationEdge(move_by_red, after_fight, status=SimUniMoveToEnemyByMiniMap.STATUS_FIGHT))
        edges.append(StateOperationEdge(move_by_detect, after_fight, status=SimUniMoveToEnemyByDetect.STATUS_FIGHT))

        # 画面上识别不到任何内容时 使用旧的方法进行识别下层入口兜底
        check_entry = StateOperationNode('识别下层入口', self._check_next_entry)
        edges.append(StateOperationEdge(detect_screen, check_entry, status=SimUniRunRouteBaseV2.STATUS_NO_ENEMY))
        edges.append(StateOperationEdge(move_by_detect, check_entry, success=False, status=SimUniMoveToEnemyByDetect.STATUS_NO_ENEMY))
        # 找到了下层入口就开始移动
        move_to_next = StateOperationNode('向下层移动', self._move_to_next)
        edges.append(StateOperationEdge(check_entry, move_to_next, status=SimUniRunRouteBaseV2.STATUS_WITH_ENTRY))
        edges.append(StateOperationEdge(detect_screen, move_to_next, status=SimUniRunRouteBaseV2.STATUS_WITH_ENTRY))

        # 找不到下层入口就转向找目标
        turn = StateOperationNode('转动找目标', self._turn_when_nothing)
        edges.append(StateOperationEdge(check_entry, turn, status=SimUniRunRouteBaseV2.STATUS_NO_ENTRY))
        # 画面识别不到内容时 也转动找目标
        edges.append(StateOperationEdge(detect_screen, turn, status=SimUniRunRouteBaseV2.STATUS_NOTHING))
        # 移动到下层入口失败时 也转动找目标
        # 可能1 走过了 没交互成功
        # 可能2 识别错了未激活的入口 移动过程中被攻击了
        edges.append(StateOperationEdge(move_to_next, turn, success=False))
        # 转动完重新开始目标识别
        edges.append(StateOperationEdge(turn, check))

        super().__init__(ctx, level_type=level_type,
                         edges=edges,
                         specified_start_node=before_route)

        self.last_state: str = ''  # 上一次的画面状态
        self.current_state: str = ''  # 这一次的画面状态

    def _before_route(self) -> OperationOneRoundResult:
        """
        路线开始前
        1. 按照小地图识别初始的朝向
        2. 如果是 buff秘技 且需要 秘技开怪，先使用秘技
        :return:
        """
        screen = self.screenshot()
        self._check_angle(screen)

        if (self.ctx.sim_uni_challenge_config.technique_fight
                and self.ctx.team_info.is_buff_technique
                and not self.ctx.technique_used):
            op = UseTechnique(self.ctx,
                              max_consumable_cnt=self.ctx.sim_uni_challenge_config.max_consumable_cnt,
                              need_check_point=True,  # 检查秘技点是否足够 可以在没有或者不能用药的情况加快判断
                              trick_snack=self.ctx.game_config.use_quirky_snacks
                              )
            op.execute()

            return self.round_by_op(op.execute())

        return self.round_success()

    def _check_screen(self) -> OperationOneRoundResult:
        """
        检测屏幕
        :return:
        """
        screen = self.screenshot()

        # 为了保证及时攻击 外层仅判断是否在大世界画面 非大世界画面时再细分处理
        self.current_state = screen_state.get_sim_uni_screen_state(
            screen, self.ctx.im, self.ctx.ocr,
            in_world=True, battle=True)
        log.debug('当前画面 %s', self.current_state)

        if self.current_state == ScreenState.NORMAL_IN_WORLD.value:
            return self._handle_in_world(screen)
        else:
            return self._handle_not_in_world(screen)

    def _handle_in_world(self, screen: MatLike) -> OperationOneRoundResult:
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        mm_info: MiniMapInfo = mini_map.analyse_mini_map(mm)

        pos, _ = mini_map.get_closest_enemy_pos(mm_info)

        if pos is None:
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_NO_RED)
        else:
            if self.ctx.one_dragon_config.is_debug:  # 红点已经比较成熟 调试时强制使用yolo
                return self.round_success(status=SimUniRunRouteBaseV2.STATUS_NO_RED)
            self.previous_angle = cal_utils.get_angle_by_pts(Point(0, 0), pos)  # 记录有目标的方向
            log.debug(f'根据红点记录角度 {self.previous_angle}')
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_WITH_RED)

    def _move_by_red(self) -> OperationOneRoundResult:
        """
        朝小地图红点走去
        :return:
        """
        self.nothing_times = 0
        self.moved_to_target = True
        op = SimUniMoveToEnemyByMiniMap(self.ctx)
        op_result = op.execute()
        return self.round_by_op(op_result)

    def _enter_fight(self) -> OperationOneRoundResult:
        op = SimUniEnterFight(self.ctx,
                              first_state=ScreenNormalWorld.CHARACTER_ICON.value.status,
                              )
        op_result = op.execute()
        return self.round_by_op(op_result)

    def _handle_not_in_world(self, screen: MatLike) -> OperationOneRoundResult:
        """
        不在大世界的场景 无论是什么 都可以交给 SimUniEnterFight 处理
        :param screen:
        :return:
        """
        op = SimUniEnterFight(self.ctx, config=self.ctx.sim_uni_challenge_config)
        op_result = op.execute()
        if op_result.success:
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_FIGHT)
        else:
            return self.round_by_op(op_result)

    def _detect_screen(self) -> OperationOneRoundResult:
        """
        没有红点时 对画面进行目标识别
        :return:
        """
        self._view_down()
        screen: MatLike = self.screenshot()

        frame_result = self.ctx.yolo_detector.sim_uni_yolo.detect(screen)

        enemy_angles: List[float] = []
        entry_angles: List[float] = []
        inactive_entry_angles: List[float] = []
        with_danger: bool = False
        for result in frame_result.results:
            delta_angle = delta_angle_to_detected_object(result)
            if result.detect_class.class_cate == '普通怪':
                enemy_angles.append(delta_angle)
            elif result.detect_class.class_cate == '模拟宇宙下层入口':
                entry_angles.append(delta_angle)
            elif result.detect_class.class_cate == '模拟宇宙下层入口未激活':
                inactive_entry_angles.append(delta_angle)
            elif result.detect_class.class_cate == '界面提示被锁定':
                with_danger = True

        if with_danger:
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_WITH_DANGER)
        elif len(enemy_angles) > 0:
            mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
            angle = mini_map.analyse_angle(mm)
            avg_delta_angle = np.mean(enemy_angles)
            self.previous_angle = cal_utils.angle_add(angle, avg_delta_angle)
            log.debug(f'根据YOLO记录角度 识别怪角度 {enemy_angles}, 当前角度 {angle} 最终记录角度 {self.previous_angle}')
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_WITH_ENEMY)
        elif len(entry_angles) > 0 and len(inactive_entry_angles) == 0:  # 只有激活了的下层入口
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_WITH_ENTRY)
        else:
            if self.ctx.one_dragon_config.is_debug:
                if self.nothing_times == 1:
                    self.save_screenshot()
            return self.round_success(SimUniRunRouteBaseV2.STATUS_NOTHING)

    def _move_by_detect(self) -> OperationOneRoundResult:
        """
        识别到敌人人开始移动
        :return:
        """
        self.nothing_times = 0
        self.moved_to_target = True
        op = SimUniMoveToEnemyByDetect(self.ctx)
        op_result = op.execute()
        if op_result.success:
            self.detect_move_timeout_times = 0
        return self.round_by_op(op_result)
