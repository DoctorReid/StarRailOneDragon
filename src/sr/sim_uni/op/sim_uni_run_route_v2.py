from typing import List, ClassVar

from cv2.typing import MatLike

from basic import Point, cal_utils
from basic.i18_utils import gt
from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot import mini_map, screen_state, MiniMapInfo
from sr.operation import StateOperation, StateOperationEdge, StateOperationNode, OperationOneRoundResult, Operation
from sr.sim_uni.op.move_in_sim_uni import MoveWithoutPosInSimUni, MoveToNextLevel
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sr.sim_uni.sim_uni_const import SimUniLevelTypeEnum


class SimUniRunCombatRouteV2(StateOperation):

    STATUS_NO_ENEMY: ClassVar[str] = '无敌人'
    STATUS_ENEMY: ClassVar[str] = '有敌人'

    STATUS_NO_ENTRY: ClassVar[str] = '找下层入口失败'

    def __init__(self, ctx: Context):
        """
        1. 检测地图是否有红点
        2. 如果有红点 移动到最近的红点 并进行攻击。攻击一次后回到步骤1判断。
        3. 如果没有红点 识别敌对物种位置，向最大的移动，并进行攻击。攻击一次后回到步骤1判断。
        4. 如果没有红点也没有识别到敌对物种，检测下层入口位置，发现后进入下层移动。未发现则选择视角返回步骤1判断。
        """
        edges: List[StateOperationEdge] = []

        check = StateOperationNode('画面检测', self._check_screen)
        move_to_enemy = StateOperationNode('朝敌人移动', self._move_to_enemy)
        edges.append(StateOperationEdge(check, move_to_enemy, status=SimUniRunCombatRouteV2.STATUS_ENEMY))

        fight = StateOperationNode('进入战斗', self._enter_fight)
        edges.append(StateOperationEdge(move_to_enemy, fight, status=MoveWithoutPosInSimUni.STATUS_ARRIVE))
        edges.append(StateOperationEdge(fight, check))

        # 暂停的话 重新检测敌人坐标前进
        edges.append(StateOperationEdge(move_to_enemy, check, status=MoveWithoutPosInSimUni.STATUS_PAUSE))

        to_next = StateOperationNode('进入下层', self._move_to_next)
        edges.append(StateOperationEdge(check, to_next, status=SimUniRunCombatRouteV2.STATUS_NO_ENEMY))
        edges.append(StateOperationEdge(to_next, check, status=SimUniRunCombatRouteV2.STATUS_NO_ENTRY))  # 重试1次进入下层

        super().__init__(ctx,
                         op_name=gt('区域-战斗', 'ui'),
                         edges=edges)

        self.last_state: str = ''  # 上一次的画面状态
        self.current_state: str = ''  # 这一次的画面状态
        self.current_pos: Point = Point(0, 0)  # 人物当前的位置 固定
        self.target_enemy_pos: Point = Point(0, 0)  # 目标敌人的位置
        self.to_next_fail_times: int = 0  # 向下层移动失败次数

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

        if self.current_state == screen_state.ScreenState.NORMAL_IN_WORLD.value:
            return self._handle_in_world(screen)
        else:
            return self._handle_not_in_world(screen)

    def _handle_in_world(self, screen: MatLike) -> OperationOneRoundResult:
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)

        if mini_map.is_under_attack(mm, self.ctx.game_config.mini_map_pos):
            op = SimUniEnterFight(self.ctx)
            return Operation.round_wait_by_op(op.execute())

        mm_info: MiniMapInfo = mini_map.analyse_mini_map(mm, self.ctx.im)
        pos_list = mini_map.get_enemy_pos(mm_info.origin_del_radio)

        if len(pos_list) == 0:
            return Operation.round_success(SimUniRunCombatRouteV2.STATUS_NO_ENEMY)
        else:
            self.target_enemy_pos = None
            target_distance = 999
            for pos in pos_list:
                dis = cal_utils.distance_between(self.current_pos, pos)
                if self.target_enemy_pos is None or dis < target_distance:
                    self.target_enemy_pos = pos
                    target_distance = dis

            return Operation.round_success(SimUniRunCombatRouteV2.STATUS_ENEMY)

    def _move_to_enemy(self) -> OperationOneRoundResult:
        op = MoveWithoutPosInSimUni(self.ctx, self.target_enemy_pos)
        return Operation.round_by_op(op.execute())

    def _enter_fight(self) -> OperationOneRoundResult:
        op = SimUniEnterFight(self.ctx,
                              first_state=screen_state.ScreenState.NORMAL_IN_WORLD.value,
                              config=self.ctx.sim_uni_challenge_config
                              )
        return op.round_by_op(op.execute())

    def _handle_not_in_world(self, screen: MatLike) -> OperationOneRoundResult:
        """
        不在大世界的场景 无论是什么 都可以交给 SimUniEnterFight 处理
        :param screen:
        :return:
        """
        op = SimUniEnterFight(self.ctx, config=self.ctx.sim_uni_challenge_config)
        return Operation.round_wait_by_op(op.execute())

    def _move_to_next(self):
        """
        朝下层移动
        :return:
        """
        op = MoveToNextLevel(self.ctx, level_type=SimUniLevelTypeEnum.COMBAT.value)
        op_result = op.execute()
        if op_result.success:
            return Operation.round_success()
        else:
            self.to_next_fail_times += 1
            if self.to_next_fail_times >= 2:
                return Operation.round_fail_by_op(op_result)
            else:
                return Operation.round_success(SimUniRunCombatRouteV2.STATUS_NO_ENTRY)
