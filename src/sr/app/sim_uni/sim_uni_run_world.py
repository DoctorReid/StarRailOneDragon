from typing import Optional, Callable, ClassVar

from basic.i18_utils import gt
from sr.sim_uni.op.sim_uni_exit import SimUniExit
from sr.sim_uni.op.sim_uni_run_level import SimUniRunLevel
from sr.context import Context
from sr.operation import Operation, OperationResult, StateOperation, OperationOneRoundResult, \
    StateOperationNode, StateOperationEdge
from sr.sim_uni.sim_uni_const import UNI_NUM_CN
from sr.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig


class SimUniRunWorld(StateOperation):

    STATUS_SUCCESS: ClassVar[str] = '通关'

    def __init__(self, ctx: Context, world_num: int,
                 config: Optional[SimUniChallengeConfig] = None,
                 max_reward_to_get: int = 0,
                 get_reward_callback: Optional[Callable[[int, int], None]] = None,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        """
        模拟宇宙 完成整个宇宙
        最后退出
        """
        op_name = '%s %s' % (
            gt('模拟宇宙', 'ui'),
            gt('第%s世界' % UNI_NUM_CN[world_num], 'ui')
        )

        edges = []

        # 逐层挑战
        run_level = StateOperationNode('挑战楼层', self._run_level)
        edges.append(StateOperationEdge(run_level, run_level, ignore_status=True))

        # 通关后退出
        finished = StateOperationNode('结束', self._finish)
        edges.append(StateOperationEdge(run_level, finished, status=SimUniRunLevel.STATUS_BOSS_CLEARED))

        # 失败后退出宇宙 继续下一次
        exit_world = StateOperationNode('退出宇宙', self._exit)
        edges.append(StateOperationEdge(run_level, exit_world, success=False))

        super().__init__(ctx, op_name=op_name, edges=edges, specified_start_node=run_level,
                         op_callback=op_callback)

        self.world_num: int = world_num
        self.config: Optional[SimUniChallengeConfig] = config
        self.max_reward_to_get: int = max_reward_to_get  # 最多获取多少次奖励
        self.get_reward_cnt: int = 0  # 当前获取的奖励次数
        self.get_reward_callback: Optional[Callable[[int, int], None]] = get_reward_callback  # 获取奖励后的回调

    def _init_before_execute(self):
        super()._init_before_execute()
        self.get_reward_cnt = 0
        self.ctx.no_technique_recover_consumables = False  # 模拟宇宙重新开始时重置

    def _run_level(self) -> OperationOneRoundResult:
        op = SimUniRunLevel(self.ctx, self.world_num, config=self.config,
                            max_reward_to_get=self.max_reward_to_get - self.get_reward_cnt,
                            get_reward_callback=self._on_get_reward)
        return Operation.round_by_op(op.execute())

    def _finish(self) -> OperationOneRoundResult:
        return Operation.round_success(status=SimUniRunWorld.STATUS_SUCCESS)

    def _exit(self) -> OperationOneRoundResult:
        if self.ctx.one_dragon_config.is_debug:  # 调试情况下 原地失败即可
            return Operation.round_fail()
        else:
            op = SimUniExit(self.ctx)
            return Operation.round_by_op(op.execute())

    def _on_get_reward(self, use_power: int, user_qty: int):
        """
        获取奖励后的回调
        :return:
        """
        self.get_reward_cnt += 1
        if self.get_reward_callback is not None:
            self.get_reward_callback(use_power, user_qty)
