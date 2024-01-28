from typing import Optional, Callable

from basic.i18_utils import gt
from sr.app.sim_uni.sim_uni_run_level import SimUniRunLevel
from sr.context import Context
from sr.operation import Operation, OperationResult, StateOperation, OperationOneRoundResult, \
    StateOperationNode, StateOperationEdge
from sr.sim_uni.sim_uni_const import UNI_NUM_CN
from sr.sim_uni.sim_uni_priority import SimUniAllPriority


class SimUniRunWorld(StateOperation):

    def __init__(self, ctx: Context, world_num: int,
                 priority: Optional[SimUniAllPriority] = None,
                 max_reward_to_get: int = 0,
                 get_reward_callback: Optional[Callable[[int, int], None]] = None,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        """
        模拟宇宙 完成整个宇宙
        """
        op_name = '%s %s' % (
            gt('模拟宇宙', 'ui'),
            gt('第%s世界' % UNI_NUM_CN[world_num], 'ui')
        )

        edges = []

        run_level = StateOperationNode('挑战楼层', self._run_level)
        finished = StateOperationNode('结束', self._finish)

        edges.append(StateOperationEdge(run_level, finished, status=SimUniRunLevel.STATUS_BOSS_CLEARED))
        edges.append(StateOperationEdge(run_level, run_level, ignore_status=True))

        super().__init__(ctx, op_name=op_name, edges=edges, specified_start_node=run_level,
                         op_callback=op_callback)

        self.world_num: int = world_num
        self.priority: Optional[SimUniAllPriority] = priority
        self.max_reward_to_get: int = max_reward_to_get  # 最多获取多少次奖励
        self.get_reward_cnt: int = 0  # 当前获取的奖励次数
        self.get_reward_callback: Optional[Callable[[int, int], None]] = get_reward_callback  # 获取奖励后的回调

    def _init_before_execute(self):
        super()._init_before_execute()
        self.get_reward_cnt = 0

    def _run_level(self) -> OperationOneRoundResult:
        op = SimUniRunLevel(self.ctx, self.world_num, priority=self.priority,
                            max_reward_to_get=self.max_reward_to_get - self.get_reward_cnt,
                            get_reward_callback=self._on_get_reward)
        return Operation.round_by_op(op.execute())

    def _finish(self) -> OperationOneRoundResult:
        return Operation.round_success()

    def _on_get_reward(self, use_power: int, user_qty: int):
        """
        获取奖励后的回调
        :return:
        """
        self.get_reward_cnt += 1
        if self.get_reward_callback is not None:
            self.get_reward_callback(use_power, user_qty)
