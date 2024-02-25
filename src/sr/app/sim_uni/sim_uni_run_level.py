from typing import List, Optional, Callable, ClassVar

from basic.i18_utils import gt
from sr.context import Context
from sr.operation import Operation, OperationResult, StateOperation, StateOperationEdge, \
    StateOperationNode, OperationOneRoundResult
from sr.operation.unit.move import MoveDirectly
from sr.operation.unit.team import CheckTeamMembersInWorld
from sr.sim_uni.op.move_in_sim_uni import MoveToNextLevel
from sr.sim_uni.op.reset_sim_uni_level import ResetSimUniLevel
from sr.sim_uni.op.sim_uni_check_level_type import SimUniCheckLevelType
from sr.sim_uni.op.sim_uni_run_route import SimUniRunInteractRoute, SimUniRunEliteRoute, SimUniRunCombatRoute
from sr.sim_uni.op.sim_uni_wait import SimUniWaitLevelStart
from sr.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig
from sr.sim_uni.sim_uni_const import UNI_NUM_CN, SimUniLevelType, SimUniLevelTypeEnum


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

        check_level_type = StateOperationNode('识别楼层类型', self._check_level_type)
        edges.append(StateOperationEdge(check_members, check_level_type))

        route = StateOperationNode('区域', self._route_op)
        edges.append(StateOperationEdge(check_level_type, route, ignore_status=True))

        reset = StateOperationNode('重置', self._reset)
        edges.append(StateOperationEdge(route, reset, success=False, status=MoveDirectly.STATUS_NO_POS))
        edges.append(StateOperationEdge(route, reset, success=False, status=MoveToNextLevel.STATUS_ENTRY_NOT_FOUND))
        edges.append(StateOperationEdge(reset, route))

        super().__init__(ctx, op_name=op_name, edges=edges, specified_start_node=wait_start, op_callback=op_callback)

        self.world_num: int = world_num
        self.level_type: Optional[SimUniLevelType] = None
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
        self.reset_times = 0

    def _wait(self) -> OperationOneRoundResult:
        op = SimUniWaitLevelStart(self.ctx, config=self.config)
        return Operation.round_by_op(op.execute())

    def _check_members(self) -> OperationOneRoundResult:
        op = CheckTeamMembersInWorld(self.ctx)
        return Operation.round_by_op(op.execute())

    def _check_level_type(self) -> OperationOneRoundResult:
        op = SimUniCheckLevelType(self.ctx, op_callback=self._on_level_type_checked)
        return Operation.round_by_op(op.execute())

    def _on_level_type_checked(self, op_result: OperationResult):
        if not op_result.success:
            return
        self.level_type = op_result.data

    def _route_op(self) -> OperationOneRoundResult:
        """
        获取路线指令
        :return:
        """
        if self.level_type == SimUniLevelTypeEnum.COMBAT.value:
            op = SimUniRunCombatRoute(self.ctx, self.world_num, self.level_type, config=self.config)
        elif self.level_type == SimUniLevelTypeEnum.EVENT.value or \
                self.level_type == SimUniLevelTypeEnum.TRANSACTION.value or \
                self.level_type == SimUniLevelTypeEnum.ENCOUNTER.value or \
                self.level_type == SimUniLevelTypeEnum.RESPITE.value:
            op = SimUniRunInteractRoute(self.ctx, self.world_num, self.level_type, config=self.config)
        elif self.level_type == SimUniLevelTypeEnum.ELITE.value or \
                self.level_type == SimUniLevelTypeEnum.BOSS.value:
            op = SimUniRunEliteRoute(self.ctx, self.world_num, self.level_type, config=self.config,
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
