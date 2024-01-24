from typing import List, Optional, Callable, ClassVar

from basic.i18_utils import gt
from sr.context import Context
from sr.operation import Operation, OperationResult, OperationFail, OperationSuccess
from sr.operation.combine import StatusCombineOperation2, StatusCombineOperationEdge2, StatusCombineOperationNode
from sr.operation.unit.move import MoveToEnemy
from sr.sim_uni.op.sim_uni_check_level_type import SimUniCheckLevelType
from sr.sim_uni.op.sim_uni_event import SimUniEvent
from sr.sim_uni.op.sim_uni_exit import SimUniExit
from sr.sim_uni.op.sim_uni_run_route import SimUniRunInteractRoute, SimUniRunEventRoute, \
    SimUniRunRespiteRoute, SimUniRunEliteRoute, SimUniRunCombatRoute
from sr.sim_uni.op.sim_uni_wait import SimUniWaitLevelStart
from sr.sim_uni.sim_uni_const import UNI_NUM_CN, SimUniLevelType, SimUniLevelTypeEnum
from sr.sim_uni.sim_uni_priority import SimUniBlessPriority, SimUniNextLevelPriority, SimUniCurioPriority
from sr.sim_uni.sim_uni_route import SimUniRoute


class SimUniRunLevel(StatusCombineOperation2):

    STATUS_ALL_LEVEL_FINISHED: ClassVar[str] = '全楼层通关'

    def __init__(self, ctx: Context, world_num: int,
                 bless_priority: Optional[SimUniBlessPriority] = None,
                 curio_priority: Optional[SimUniCurioPriority] = None,
                 next_level_priority: Optional[SimUniNextLevelPriority] = None,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        """
        模拟宇宙中 识别楼层类型并运行
        """
        op_name = '%s %s %s' % (
            gt('模拟宇宙', 'ui'),
            gt('第%s世界' % UNI_NUM_CN[world_num], 'ui'),
            gt('挑战楼层', 'ui')
        )

        edges: List[StatusCombineOperationEdge2] = []

        wait_start = StatusCombineOperationNode('等待加载',
                                                SimUniWaitLevelStart(ctx,
                                                                     bless_priority=bless_priority,
                                                                     curio_priority=curio_priority)
                                                )
        check_level_type = StatusCombineOperationNode('识别楼层类型',
                                                      SimUniCheckLevelType(ctx, op_callback=self._on_level_type_checked))
        edges.append(StatusCombineOperationEdge2(wait_start, check_level_type, status=SimUniWaitLevelStart.STATUS_START))

        # 战斗楼层
        combat_route = StatusCombineOperationNode('区域-战斗', op_func=self._route_op)
        edges.append(StatusCombineOperationEdge2(check_level_type, combat_route,
                                                 status=SimUniLevelTypeEnum.COMBAT.value.type_id))
        edges.append(StatusCombineOperationEdge2(combat_route, wait_start))

        # 精英
        elite_route = StatusCombineOperationNode('区域-精英', op_func=self._route_op)
        edges.append(StatusCombineOperationEdge2(check_level_type, elite_route,
                                                 status=SimUniLevelTypeEnum.ELITE.value.type_id))

        edges.append(StatusCombineOperationEdge2(elite_route, wait_start))
        edges.append(StatusCombineOperationEdge2(elite_route, wait_start,
                                                 success=False, status=MoveToEnemy.STATUS_ENEMY_NOT_FOUND))  # 也可能没敌人

        # 首领
        boss_route = StatusCombineOperationNode('区域-首领', op_func=self._route_op)
        edges.append(StatusCombineOperationEdge2(check_level_type, boss_route,
                                                 status=SimUniLevelTypeEnum.BOSS.value.type_id))

        # 通关
        boss_exit = StatusCombineOperationNode('通关', SimUniExit(ctx))
        edges.append(StatusCombineOperationEdge2(boss_route, boss_exit))
        edges.append(StatusCombineOperationEdge2(boss_route, boss_exit,
                                                 success=False, status=MoveToEnemy.STATUS_ENEMY_NOT_FOUND))  # 也可能没敌人

        # 成功结束
        success = StatusCombineOperationNode('成功结束', OperationSuccess(ctx, status=SimUniRunLevel.STATUS_ALL_LEVEL_FINISHED))
        edges.append(StatusCombineOperationEdge2(boss_exit, success))

        # 休整楼层
        respite_move_to_herta = StatusCombineOperationNode('区域-休整-走向黑塔', op_func=self._route_op)
        edges.append(StatusCombineOperationEdge2(check_level_type, respite_move_to_herta,
                                                 status=SimUniLevelTypeEnum.RESPITE.value.type_id))

        respite_herta_event = StatusCombineOperationNode(
            '区域-休整-黑塔事件',
            SimUniEvent(ctx, bless_priority=bless_priority, curio_priority=curio_priority))
        edges.append(StatusCombineOperationEdge2(respite_move_to_herta, respite_herta_event))

        edges.append(StatusCombineOperationEdge2(respite_herta_event, wait_start))
        edges.append(StatusCombineOperationEdge2(respite_move_to_herta, wait_start,
                                                 status=SimUniRunInteractRoute.STATUS_ICON_NOT_FOUND))

        # 事件、交易、遭遇
        event_route = StatusCombineOperationNode('区域-事件', op_func=self._route_op)
        edges.append(StatusCombineOperationEdge2(check_level_type, event_route,
                                                 status=SimUniLevelTypeEnum.EVENT.value.type_id))
        edges.append(StatusCombineOperationEdge2(check_level_type, event_route,
                                                 status=SimUniLevelTypeEnum.TRANSACTION.value.type_id))
        edges.append(StatusCombineOperationEdge2(check_level_type, event_route,
                                                 status=SimUniLevelTypeEnum.ENCOUNTER.value.type_id))

        event_handle = StatusCombineOperationNode('区域-事件-选择',
                                                  SimUniEvent(ctx,
                                                              bless_priority=bless_priority,
                                                              curio_priority=curio_priority))
        edges.append(StatusCombineOperationEdge2(event_route, event_handle))

        edges.append(StatusCombineOperationEdge2(event_handle, wait_start))
        edges.append(StatusCombineOperationEdge2(event_route, wait_start,
                                                 status=SimUniRunInteractRoute.STATUS_ICON_NOT_FOUND))

        super().__init__(ctx, op_name=op_name, edges=edges, specified_start_node=wait_start, op_callback=op_callback)

        self.world_num: int = world_num
        self.level_type: Optional[SimUniLevelType] = None
        self.route: Optional[SimUniRoute] = None
        self.bless_priority: Optional[SimUniBlessPriority] = bless_priority
        self.curio_priority: Optional[SimUniCurioPriority] = curio_priority
        self.next_level_priority: Optional[SimUniNextLevelPriority] = next_level_priority

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self.route = None
        self.level_type = None

    def _on_level_type_checked(self, op_result: OperationResult):
        if not op_result.success:
            return
        self.level_type = op_result.data

    def _route_op(self) -> Operation:
        """
        获取路线指令
        :return:
        """
        if self.level_type == SimUniLevelTypeEnum.COMBAT.value:
            return SimUniRunCombatRoute(self.ctx, self.level_type,
                                        bless_priority=self.bless_priority,
                                        curio_priority=self.curio_priority,
                                        next_level_priority=self.next_level_priority)
        elif self.level_type == SimUniLevelTypeEnum.EVENT.value or \
                self.level_type == SimUniLevelTypeEnum.TRANSACTION.value or \
                self.level_type == SimUniLevelTypeEnum.ENCOUNTER.value:
            return SimUniRunEventRoute(self.ctx, self.route)
        elif self.level_type == SimUniLevelTypeEnum.RESPITE.value:
            return SimUniRunRespiteRoute(self.ctx, self.route)
        elif self.level_type == SimUniLevelTypeEnum.ELITE.value or \
                self.level_type == SimUniLevelTypeEnum.BOSS.value:
            return SimUniRunEliteRoute(self.ctx, self.level_type,
                                       bless_priority=self.bless_priority,
                                       curio_priority=self.curio_priority,
                                       next_level_priority=self.next_level_priority)
        else:
            return OperationFail(self.ctx, status='未知楼层类型 %s' % self.level_type)
