from typing import List, Optional, Callable, ClassVar

from basic import str_utils
from basic.i18_utils import gt
from sr.app.sim_uni.sim_uni_route_holder import match_best_sim_uni_route
from sr.context import Context
from sr.image.sceenshot import screen_state, mini_map
from sr.operation import Operation, OperationResult, StateOperation, StateOperationEdge, \
    StateOperationNode, OperationOneRoundResult
from sr.operation.unit.move import MoveDirectly
from sr.operation.unit.team import CheckTeamMembersInWorld
from sr.sim_uni.op.move_in_sim_uni import MoveToNextLevel
from sr.sim_uni.op.reset_sim_uni_level import ResetSimUniLevel
from sr.sim_uni.op.sim_uni_run_route import SimUniRunInteractRoute, SimUniRunEliteRoute, SimUniRunCombatRoute
from sr.sim_uni.op.sim_uni_wait import SimUniWaitLevelStart
from sr.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig
from sr.sim_uni.sim_uni_const import UNI_NUM_CN, SimUniLevelType, SimUniLevelTypeEnum
from sr.sim_uni.sim_uni_route import SimUniRoute


class SimUniRunLevel(StateOperation):

    STATUS_BOSS_CLEARED: ClassVar[str] = '首领通关'
    STATUS_NO_RESET: ClassVar[str] = '失败到达重置上限'

    def __init__(self, ctx: Context, world_num: int,
                 config: Optional[SimUniChallengeConfig] = None,
                 max_reward_to_get: int = 0,
                 get_reward_callback: Optional[Callable[[int, int], None]] = None,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        """
        模拟宇宙中 识别楼层类型并运行
        完整通过整个楼层 进入下个楼层或通关后退出
        异常情况交由外层处理
        - 战斗失败
        """
        op_name = '%s %s %s' % (
            gt('模拟宇宙', 'ui'),
            gt('第%s世界' % UNI_NUM_CN[world_num], 'ui'),
            gt('挑战楼层', 'ui')
        )

        edges: List[StateOperationEdge] = []

        wait_start = StateOperationNode('等待加载', self._wait)

        check_members = StateOperationNode('识别组队成员', self._check_members)
        edges.append(StateOperationEdge(wait_start, check_members))

        check_route = StateOperationNode('匹配路线', self._check_route)
        edges.append(StateOperationEdge(check_members, check_route))

        route = StateOperationNode('区域', self._route_op)
        edges.append(StateOperationEdge(check_route, route, ignore_status=True))

        reset = StateOperationNode('重置', self._reset)
        edges.append(StateOperationEdge(route, reset, success=False, status=MoveDirectly.STATUS_NO_POS))
        edges.append(StateOperationEdge(route, reset, success=False, status=MoveToNextLevel.STATUS_ENTRY_NOT_FOUND))
        edges.append(StateOperationEdge(reset, route))

        super().__init__(ctx, op_name=op_name, edges=edges, specified_start_node=wait_start, op_callback=op_callback)

        self.world_num: int = world_num
        self.level_type: Optional[SimUniLevelType] = None
        self.route: Optional[SimUniRoute] = None
        self.config: Optional[SimUniChallengeConfig] = config
        self.max_reward_to_get: int = max_reward_to_get  # 最多获取多少次奖励
        self.get_reward_callback: Optional[Callable[[int, int], None]] = get_reward_callback  # 获取奖励后的回调
        self.reset_times: int = 0  # 重置次数

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self.level_type = None
        self.route = None
        self.reset_times = 0

    def _wait(self) -> OperationOneRoundResult:
        op = SimUniWaitLevelStart(self.ctx, config=self.config)
        return Operation.round_by_op(op.execute())

    def _check_members(self) -> OperationOneRoundResult:
        op = CheckTeamMembersInWorld(self.ctx)
        return Operation.round_by_op(op.execute())

    def _check_route(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        region_name = screen_state.get_region_name(screen, self.ctx.ocr)
        level_type_list: List[SimUniLevelType] = [enum.value for enum in SimUniLevelTypeEnum]
        target_list = [gt(level_type.type_name, 'ocr') for level_type in level_type_list]
        target_idx = str_utils.find_best_match_by_lcs(region_name, target_list)

        if target_idx is None:
            self.level_type = None
            self.route = None
            return Operation.round_retry('匹配楼层类型失败', wait=1)

        another_route = False  # 是否匹配到另一条路线
        target_level_type = level_type_list[target_idx]
        if self.level_type is None or self.level_type != target_level_type:
            self.level_type = target_level_type
            another_route = True

        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        target_route = match_best_sim_uni_route(self.world_num, self.level_type, mm)

        if target_route is None:
            self.level_type = None
            self.route = None
            return Operation.round_retry('匹配路线失败', wait=1)
        elif self.route is None or self.route.uid != target_route.uid:
            self.route = target_route
            another_route = True

        if another_route:
            return Operation.round_wait(wait=0.5)  # 两次匹配成功才认为是正确的路线 牺牲一点时间换取稳定性
        else:
            return Operation.round_success()

    def _route_op(self) -> OperationOneRoundResult:
        """
        获取路线指令
        :return:
        """
        if self.level_type == SimUniLevelTypeEnum.COMBAT.value:
            op = SimUniRunCombatRoute(self.ctx, self.world_num, self.level_type, self.route, config=self.config)
        elif self.level_type == SimUniLevelTypeEnum.EVENT.value or \
                self.level_type == SimUniLevelTypeEnum.TRANSACTION.value or \
                self.level_type == SimUniLevelTypeEnum.ENCOUNTER.value or \
                self.level_type == SimUniLevelTypeEnum.RESPITE.value:
            op = SimUniRunInteractRoute(self.ctx, self.world_num, self.level_type, self.route, config=self.config)
        elif self.level_type == SimUniLevelTypeEnum.ELITE.value or \
                self.level_type == SimUniLevelTypeEnum.BOSS.value:
            op = SimUniRunEliteRoute(self.ctx, self.world_num, self.level_type, self.route, config=self.config,
                                     max_reward_to_get=self.max_reward_to_get,
                                     get_reward_callback=self.get_reward_callback)
        else:
            return Operation.round_fail(status='未知楼层类型 %s' % self.level_type)

        op_result = op.execute()
        if op_result.success and self.level_type == SimUniLevelTypeEnum.BOSS.value:
            return Operation.round_success(status=SimUniRunLevel.STATUS_BOSS_CLEARED)
        else:
            return Operation.round_by_op(op_result)

    def _reset(self) -> OperationOneRoundResult:
        """
        重置再来
        :return:
        """
        if self.reset_times >= 1:  # 最多重置1次
            return Operation.round_fail(SimUniRunLevel.STATUS_NO_RESET)

        self.reset_times += 1
        op = ResetSimUniLevel(self.ctx)
        return Operation.round_by_op(op.execute())
