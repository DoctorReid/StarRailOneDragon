import time
from typing import List, Optional, Callable, ClassVar

from basic.i18_utils import gt
from basic.img.os import save_debug_image
from basic.log_utils import log
from sr.app.sim_uni.sim_uni_route_holder import match_best_sim_uni_route
from sr.context import Context
from sr.image.sceenshot import mini_map
from sr.operation import Operation, OperationResult, OperationFail, OperationSuccess
from sr.operation.battle.start_fight import StartFightWithTechnique, Attack
from sr.operation.combine import StatusCombineOperation2, StatusCombineOperationEdge2, StatusCombineOperationNode
from sr.operation.unit.move import MoveToEnemy, MoveForward
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sr.sim_uni.op.move_in_sim_uni import MoveToNextLevel, MoveToEventInteract, MoveToHertaInteract
from sr.sim_uni.op.sim_uni_check_level_type import SimUniCheckLevelType
from sr.sim_uni.op.sim_uni_event import SimUniEvent
from sr.sim_uni.op.sim_uni_exit import SimUniExit
from sr.sim_uni.op.sim_uni_next_level_confirm import SimUniNextLevelConfirm
from sr.sim_uni.op.sim_uni_run_route import SimUniRunCombatRoute, SimUniRunInteractRoute, SimUniRunEventRoute, \
    SimUniRunRespiteRoute, SimUniRunEliteRoute
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

        # 进入下一层
        enter_next = StatusCombineOperationNode('进入下一层', MoveToNextLevel(ctx, next_level_priority))
        next_confirm = StatusCombineOperationNode('确认进入下一层', op_func=self._next_confirm)
        edges.append(StatusCombineOperationEdge2(enter_next, next_confirm))

        # 战斗楼层
        combat_route = StatusCombineOperationNode('区域-战斗', op_func=self._route_op)
        edges.append(StatusCombineOperationEdge2(check_level_type, combat_route,
                                                 status=SimUniLevelTypeEnum.COMBAT.value.type_id))
        edges.append(StatusCombineOperationEdge2(combat_route, enter_next))

        # 精英
        elite_route = StatusCombineOperationNode('区域-精英', op_func=self._route_op)
        edges.append(StatusCombineOperationEdge2(check_level_type, elite_route,
                                                 status=SimUniLevelTypeEnum.ELITE.value.type_id))

        edges.append(StatusCombineOperationEdge2(elite_route, enter_next))
        edges.append(StatusCombineOperationEdge2(elite_route, enter_next,
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

        edges.append(StatusCombineOperationEdge2(respite_herta_event, enter_next))
        edges.append(StatusCombineOperationEdge2(respite_move_to_herta, enter_next,
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

        edges.append(StatusCombineOperationEdge2(event_handle, enter_next))
        edges.append(StatusCombineOperationEdge2(event_route, enter_next,
                                                 status=SimUniRunInteractRoute.STATUS_ICON_NOT_FOUND))

        super().__init__(ctx, op_name=op_name, edges=edges, op_callback=op_callback)

        self.world_num: int = world_num
        self.level_type: Optional[SimUniLevelType] = None
        self.route: Optional[SimUniRoute] = None
        self.bless_priority: Optional[SimUniBlessPriority] = bless_priority
        self.curio_priority: Optional[SimUniCurioPriority] = curio_priority

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

        if self.level_type.need_route:
            screen = self.screenshot()
            mm = mini_map.cut_mini_map(screen)
            self.route = match_best_sim_uni_route(self.world_num, self.level_type, mm)

    def _route_op(self) -> Operation:
        """
        获取路线指令
        :return:
        """
        if self.level_type == SimUniLevelTypeEnum.COMBAT.value:
            if self.route is None:
                return OperationFail(self.ctx, status='匹配路线失败')
            return SimUniRunCombatRoute(self.ctx, self.route, self.bless_priority)
        elif self.level_type == SimUniLevelTypeEnum.EVENT.value or \
                self.level_type == SimUniLevelTypeEnum.TRANSACTION.value or \
                self.level_type == SimUniLevelTypeEnum.ENCOUNTER.value:
            if self.route is None:
                # return MoveToEventInteract(self.ctx)  # TODO 正式发布时使用
                return OperationFail(self.ctx, status='匹配路线失败')
            return SimUniRunEventRoute(self.ctx, self.route)
        elif self.level_type == SimUniLevelTypeEnum.RESPITE.value:
            if self.route is None:
                # return MoveToHertaInteract(self.ctx)  # TODO 正式发布时使用
                return OperationFail(self.ctx, status='匹配路线失败')
            return SimUniRunRespiteRoute(self.ctx, self.route)
        elif self.level_type == SimUniLevelTypeEnum.ELITE.value or \
                self.level_type == SimUniLevelTypeEnum.BOSS.value:
            return SimUniRunEliteRoute(self.ctx, bless_priority=self.bless_priority, curio_priority=self.curio_priority)
        else:
            return OperationFail(self.ctx, status='未知楼层类型 %s' % self.level_type)

    def _next_confirm(self) -> Operation:
        if self.level_type == SimUniLevelTypeEnum.ELITE.value or self.level_type == SimUniLevelTypeEnum.BOSS.value:
            return SimUniNextLevelConfirm(self.ctx)
        else:
            return OperationSuccess(self.ctx, status='无需确认')
