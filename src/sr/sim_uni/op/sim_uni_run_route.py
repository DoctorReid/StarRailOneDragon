import time
from typing import Optional, ClassVar, List, Union, Callable

from cv2.typing import MatLike

from basic import Point
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.app.sim_uni.sim_uni_route_holder import match_best_sim_uni_route
from sr.const import operation_const
from sr.context import Context
from sr.image.sceenshot import screen_state, mini_map
from sr.operation import Operation, \
    OperationResult, OperationFail, OperationSuccess, StateOperation, StateOperationNode, OperationOneRoundResult, \
    StateOperationEdge
from sr.operation.battle.start_fight import Attack, StartFightWithTechnique
from sr.operation.combine import StatusCombineOperation2, StatusCombineOperationNode, StatusCombineOperationEdge2
from sr.operation.unit.interact import Interact
from sr.operation.unit.move import SimplyMoveByPos, MoveToEnemy
from sr.operation.unit.team import SwitchMember
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight, SimUniFightElite
from sr.sim_uni.op.move_in_sim_uni import MoveDirectlyInSimUni, MoveToNextLevelByRoute, MoveToNextLevel
from sr.sim_uni.sim_uni_const import SimUniLevelType, SimUniLevelTypeEnum
from sr.sim_uni.sim_uni_priority import SimUniBlessPriority, SimUniCurioPriority, SimUniNextLevelPriority
from sr.sim_uni.sim_uni_route import SimUniRouteOperation, SimUniRoute


class SimUniMatchRoute(Operation):

    def __init__(self, ctx: Context, world_num: int,
                 level_type: SimUniLevelType,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        """
        模拟宇宙中 根据初始的小地图 匹配路线
        返回的 data=SimUniRoute
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (
                             gt('模拟宇宙', 'ui'),
                             gt('匹配路线', 'ui'),
                         ),
                         op_callback=op_callback)
        self.world_num: int = world_num  # 第几宇宙
        self.level_type: SimUniLevelType = level_type

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen)
        route = match_best_sim_uni_route(self.world_num, self.level_type, mm)

        if route is None:
            return Operation.round_retry('匹配路线失败', wait=0.5)
        else:
            return Operation.round_success(data=route)


class SimUniRunRouteOp(StateOperation):

    STATUS_ALL_OP_DONE: ClassVar[str] = '执行结束'

    def __init__(self, ctx: Context, route: SimUniRoute,
                 bless_priority: Optional[SimUniBlessPriority] = None,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        """
        模拟宇宙 按照特定路线执行
        最后返回 data=Point 最新坐标
        """
        self.route: SimUniRoute = route
        self.op_idx: int = -1
        self.current_pos: Point = self.route.start_pos
        self.bless_priority: SimUniBlessPriority = bless_priority

        edges = []

        op_node = StateOperationNode('执行路线指令', self._next_op)
        edges.append(StateOperationEdge(op_node, op_node, ignore_status=True))

        finished = StateOperationNode('结束', self._finished)
        edges.append(StateOperationEdge(op_node, finished, status=SimUniRunRouteOp.STATUS_ALL_OP_DONE))

        super().__init__(ctx,
                         op_name='%s %s %s' % (
                             gt('模拟宇宙', 'ui'),
                             gt('执行路线指令', 'ui'),
                             route.display_name
                         ),
                         edges=edges,
                         specified_start_node=op_node,
                         op_callback=op_callback)

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self.op_idx = -1
        self.current_pos: Point = self.route.start_pos

    def _next_op(self) -> OperationOneRoundResult:
        """
        执行下一个指令
        :return:
        """
        self.op_idx += 1

        if self.op_idx >= len(self.route.op_list):
            return Operation.round_success(SimUniRunRouteOp.STATUS_ALL_OP_DONE)

        current_op: SimUniRouteOperation = self.route.op_list[self.op_idx]
        next_op: Optional[SimUniRouteOperation] = self.route.op_list[self.op_idx + 1] if self.op_idx + 1 < len(self.route.op_list) else None

        if current_op['op'] in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]:
            op = self.move(current_op, next_op)
        elif current_op['op'] == operation_const.OP_PATROL:
            op = SimUniEnterFight(self.ctx, bless_priority=self.bless_priority)
        else:
            return Operation.round_fail('未知指令')

        return Operation.round_by_op(op.execute())

    def move(self, current_op: SimUniRouteOperation, next_op: Optional[SimUniRouteOperation]) -> Operation:
        """
        按坐标进行移动
        :param current_op: 当前指令
        :param next_op: 下一个指令
        :return:
        """
        next_pos = Point(current_op['data'][0], current_op['data'][1])
        next_is_move = next_op is not None and next_op['op'] in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]
        op = MoveDirectlyInSimUni(self.ctx, self.ctx.ih.get_large_map(self.route.region),
                                  start=self.current_pos, target=next_pos,
                                  stop_afterwards=not next_is_move,
                                  op_callback=self._update_pos,
                                  bless_priority=self.bless_priority
                                  )
        return op

    def _update_pos(self, op_result: OperationResult):
        """
        更新坐标
        :param op_result:
        :return:
        """
        if op_result.success:
            self.current_pos = op_result.data

    def _finished(self) -> OperationOneRoundResult:
        """
        指令执行结束
        :return:
        """
        return Operation.round_success(data=self.current_pos)


class SimUniRunRouteBase(StateOperation):

    def __init__(self, ctx: Context,
                 level_type: SimUniLevelType,
                 bless_priority: Optional[SimUniBlessPriority] = None,
                 curio_priority: Optional[SimUniCurioPriority] = None,
                 next_level_priority: Optional[SimUniNextLevelPriority] = None):
        """
        模拟宇宙 按照路线执行的基类
        """
        self.level_type: SimUniLevelType = level_type
        self.route: Optional[SimUniRoute] = None
        self.current_pos: Optional[Point] = None
        self.bless_priority: SimUniBlessPriority = bless_priority
        self.curio_priority: Optional[SimUniCurioPriority] = curio_priority
        self.next_level_priority: Optional[SimUniNextLevelPriority] = next_level_priority

        match = StateOperationNode('匹配路线', self._match_route)
        before_route = StateOperationNode('指令前初始化', self._before_route)
        run_route = StateOperationNode('执行路线指令', self._run_route)
        level_sp = StateOperationNode('区域特殊指令', self._level_sp)
        go_next = StateOperationNode('下一层', self._go_next)

        super().__init__(ctx,
                         op_name='%s %s' % (
                             gt('模拟宇宙', 'ui'),
                             gt('区域-%s' % level_type.type_name, 'ui')
                         ),
                         nodes=[match, before_route, run_route, level_sp, go_next]
                         )

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self.route = None
        self.current_pos = None

    def _match_route(self) -> OperationOneRoundResult:
        """
        匹配路线
        :return:
        """
        op = SimUniMatchRoute(self.ctx, 8, self.level_type,
                              op_callback=self._update_route)
        return Operation.round_by_op(op.execute())

    def _before_route(self) -> OperationOneRoundResult:
        """
        执行路线前的初始化 由各类型楼层自行实现
        :return:
        """
        return Operation.round_success()

    def _update_route(self, op_result: OperationResult):
        """
        更新路线配置
        :param op_result:
        :return:
        """
        if op_result.success:
            self.route = op_result.data

    def _run_route(self) -> OperationOneRoundResult:
        """
        执行下一个指令
        :return:
        """
        op = SimUniRunRouteOp(self.ctx, self.route, self.bless_priority, op_callback=self._update_pos)
        return Operation.round_by_op(op.execute())

    def _update_pos(self, op_result: OperationResult):
        """
        更新坐标
        :param op_result:
        :return:
        """
        if op_result.success:
            self.current_pos = op_result.data

    def _level_sp(self) -> OperationOneRoundResult:
        """
        执行路线后的特殊操作 由各类型楼层自行实现
        :return:
        """
        return Operation.round_success()

    def _go_next(self) -> OperationOneRoundResult:
        """
        前往下一层
        :return:
        """
        if len(self.route.next_pos_list) == 0:
            op = MoveToNextLevel(self.ctx, self.next_level_priority)
        else:
            op = MoveToNextLevelByRoute(self.ctx, self.route, self.current_pos, self.next_level_priority)

        op = MoveToNextLevelByRoute(self.ctx, self.route, self.current_pos, self.next_level_priority)

        return Operation.round_by_op(op.execute())


class SimUniRunCombatRoute(SimUniRunRouteBase):

    def __init__(self, ctx: Context, level_type: SimUniLevelType,
                 bless_priority: Optional[SimUniBlessPriority] = None,
                 curio_priority: Optional[SimUniCurioPriority] = None,
                 next_level_priority: Optional[SimUniNextLevelPriority] = None):

        SimUniEnterFight(ctx, bless_priority=bless_priority, curio_priority=curio_priority)

        super().__init__(ctx, level_type,
                         bless_priority=bless_priority,
                         curio_priority=curio_priority,
                         next_level_priority=next_level_priority
                         )


class SimUniRunInteractRoute(StateOperation):

    STATUS_ICON_NOT_FOUND: ClassVar[str] = '未找到图标'

    def __init__(self, ctx: Context, icon_template_id: str, interact_word: str,
                 route: SimUniRoute, can_ignor_interact: bool = False):
        """
        朝小地图上的图标走去 并交互
        :param ctx:
        """
        wait = StateOperationNode('等待加载', self._check_screen)
        check_pos = StateOperationNode('检测图标', self._check_icon_pos)
        before_move = StateOperationNode('移动前', self._before_move)
        move = StateOperationNode('移动', self._move_to_target)
        interact = StateOperationNode('交互', self._interact)

        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (
                             gt('模拟宇宙', 'ui'),
                             gt('交互层路线 %s' % interact_word, 'ui')),
                         nodes=[wait, check_pos, before_move, move, interact]
                         )

        self.icon_template_id: str = icon_template_id
        self.interact_word: str = interact_word
        self.route: SimUniRoute = route
        self.target_pos: Optional[Point] = None  # 图标在大地图上的坐标
        self.no_icon: bool = False  # 小地图上没有图标了 说明之前已经交互过了
        self.can_ignore_interact: bool = can_ignor_interact  # 是否可以忽略交互失败 例如 黑塔

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self.target_pos = None
        if self.route.event_pos_list is not None and len(self.route.event_pos_list) > 0:
            self.target_pos = self.route.event_pos_list[0]  # 暂时都只有一个事件
        self.no_icon = False

    def _check_screen(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        if screen_state.is_normal_in_world(screen, self.ctx.im):
            return Operation.round_success(wait=1)
        else:
            return Operation.round_retry('未在大世界界面')

    def _check_icon_pos(self) -> OperationOneRoundResult:
        """
        检测小地图上的图标 在大地图上的哪个位置
        :return:
        """
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen)
        angle = mini_map.analyse_angle(mm)
        radio_to_del = mini_map.get_radio_to_del(self.ctx.im, angle)
        mm_del_radio = mini_map.remove_radio(mm, radio_to_del)
        icon_pos = self._get_icon_pos(mm_del_radio)
        if icon_pos is None:
            if self.target_pos is None:  # 未配置图标坐标时 需要识别到才能往下走
                return Operation.round_retry(SimUniRunInteractRoute.STATUS_ICON_NOT_FOUND)
            else:
                self.no_icon = True
                log.info('小地图上没有图标 该层已交互完毕')
                return Operation.round_success()
        else:
            if self.target_pos is None:
                mm_center_pos = Point(mm.shape[1] // 2, mm.shape[0] // 2)
                self.target_pos = self.route.start_pos + (icon_pos - mm_center_pos)
                log.info('识别到图标位置 %s', self.target_pos)

        return Operation.round_success()

    def _before_move(self) -> OperationOneRoundResult:
        """
        移动前的动作
        :return:
        """
        return Operation.round_success()

    def _move_to_target(self) -> OperationOneRoundResult:
        """
        向目标移动 这里可以忽略检测敌人战斗
        :return:
        """
        op = SimplyMoveByPos(self.ctx,
                             lm_info=self.ctx.ih.get_large_map(self.route.region),
                             start=self.route.start_pos,
                             target=self.target_pos,
                             no_run=True
                             )
        op_result = op.execute()
        if op_result.success:
            return Operation.round_success()
        else:
            return Operation.round_fail_by_op(op_result)

    def _interact(self) -> OperationOneRoundResult:
        # 有图标的情况 就一定要交互 no_move=False
        # 没有图标的情况 可能时不需要交互 也可能时识别图标失败 先尝试交互 no_move=True
        op = Interact(self.ctx, self.interact_word, lcs_percent=0.1, single_line=True, no_move=self.no_icon)
        op_result = op.execute()
        if op_result.success:
            return Operation.round_success()
        else:
            if self.no_icon:  # 识别不到图标 又交互不到 就默认为之前已经交互了
                return Operation.round_success(SimUniRunInteractRoute.STATUS_ICON_NOT_FOUND)
            if self.can_ignore_interact:
                # 本次交互失败 但可以跳过
                return Operation.round_success()
            else:
                return Operation.round_fail_by_op(op_result)

    def _get_icon_pos(self, mm: MatLike) -> Optional[Point]:
        """
        获取图标在小地图上的位置
        :param mm:
        :return:
        """
        angle = mini_map.analyse_angle(mm)
        radio_to_del = mini_map.get_radio_to_del(self.ctx.im, angle)
        mm_del_radio = mini_map.remove_radio(mm, radio_to_del)
        source_kps, source_desc = cv2_utils.feature_detect_and_compute(mm_del_radio)
        template = self.ctx.ih.get_template(self.icon_template_id, sub_dir='sim_uni')
        mr = cv2_utils.feature_match_for_one(source_kps, source_desc,
                                             template.kps, template.desc,
                                             template.origin.shape[1], template.origin.shape[0])

        return None if mr is None else mr.center


class SimUniRunEventRoute(SimUniRunInteractRoute):

    def __init__(self, ctx: Context, route: SimUniRoute):
        super().__init__(ctx, 'mm_sp_event', '事件', route)


class SimUniRunRespiteRoute(SimUniRunInteractRoute):

    def __init__(self, ctx: Context, route: SimUniRoute):
        super().__init__(ctx, 'mm_sp_herta', '黑塔', route, can_ignor_interact=True)

    def _init_before_execute(self):
        super()._init_before_execute()
        time.sleep(1)  # 休整层初始的小地图会有缩放 不知道为什么 稍微等一下才可以识别到黑塔的图标

    def _before_move(self) -> OperationOneRoundResult:
        """
        移动前的动作
        :return:
        """
        op = Attack(self.ctx)
        op_result = op.execute()
        if op_result.success:
            return Operation.round_success(wait=0.5)
        else:
            return Operation.round_fail_by_op(op_result)


class SimUniRunEliteRoute(SimUniRunRouteBase):

    def __init__(self, ctx: Context, level_type: SimUniLevelType,
                 bless_priority: Optional[SimUniBlessPriority] = None,
                 curio_priority: Optional[SimUniCurioPriority] = None,
                 next_level_priority: Optional[SimUniNextLevelPriority] = None):

        super().__init__(ctx, level_type,
                         bless_priority=bless_priority,
                         curio_priority=curio_priority,
                         next_level_priority=next_level_priority
                         )

        self.with_enemy: bool = True

    def _init_before_execute(self):
        super()._init_before_execute()
        self.with_enemy = True

    def _level_sp(self) -> OperationOneRoundResult:
        op = SimUniFightElite(self.ctx, bless_priority=self.bless_priority, curio_priority=self.curio_priority)
        return Operation.round_by_op(op.execute())
