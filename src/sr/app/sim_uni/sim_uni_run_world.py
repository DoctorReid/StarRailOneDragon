from typing import Optional, Callable

from basic.i18_utils import gt
from sr.app.sim_uni.sim_uni_run_level import SimUniRunLevel
from sr.context import Context
from sr.operation import Operation, OperationSuccess, OperationResult
from sr.operation.combine import StatusCombineOperation2, StatusCombineOperationNode, StatusCombineOperationEdge2
from sr.sim_uni.op.sim_uni_exit import SimUniExit
from sr.sim_uni.sim_uni_const import UNI_NUM_CN
from sr.sim_uni.sim_uni_priority import SimUniBlessPriority, SimUniCurioPriority, SimUniNextLevelPriority


class SimUniRunWorld(StatusCombineOperation2):

    def __init__(self, ctx: Context, world_num: int,
                 bless_priority: Optional[SimUniBlessPriority] = None,
                 curio_priority: Optional[SimUniCurioPriority] = None,
                 next_level_priority: Optional[SimUniNextLevelPriority] = None,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        """
        模拟宇宙 完成整个宇宙
        """
        op_name = '%s %s' % (
            gt('模拟宇宙', 'ui'),
            gt('第%s世界' % UNI_NUM_CN[world_num], 'ui')
        )

        edges = []

        run_level = StatusCombineOperationNode('挑战楼层', op_func=self._run_level)
        finished = StatusCombineOperationNode('结束', OperationSuccess(ctx, status='一轮结束'))

        edges.append(StatusCombineOperationEdge2(run_level, finished, status=SimUniRunLevel.STATUS_ALL_LEVEL_FINISHED))
        edges.append(StatusCombineOperationEdge2(run_level, run_level, ignore_status=True))

        super().__init__(ctx, op_name=op_name, edges=edges, specified_start_node=run_level,
                         op_callback=op_callback)

        self.world_num: int = world_num
        self.bless_priority: Optional[SimUniBlessPriority] = bless_priority
        self.curio_priority: Optional[SimUniCurioPriority] = curio_priority
        self.next_level_priority: Optional[SimUniNextLevelPriority] = next_level_priority

    def _run_level(self) -> Operation:
        return SimUniRunLevel(
            self.ctx, self.world_num,
            bless_priority=self.bless_priority,
            curio_priority=self.curio_priority,
            next_level_priority=self.next_level_priority
        )
