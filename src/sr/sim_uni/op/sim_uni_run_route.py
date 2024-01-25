import time
from typing import Optional, ClassVar, Callable

from cv2.typing import MatLike

from basic import Point
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.app.sim_uni.sim_uni_route_holder import match_best_sim_uni_route
from sr.const import operation_const
from sr.context import Context
from sr.image.sceenshot import mini_map
from sr.operation import Operation, \
    OperationResult, StateOperation, StateOperationNode, OperationOneRoundResult, \
    StateOperationEdge
from sr.operation.unit.interact import Interact
from sr.sim_uni.op.move_in_sim_uni import MoveDirectlyInSimUni, MoveToNextLevelByRoute, MoveToNextLevel
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight, SimUniFightElite
from sr.sim_uni.op.sim_uni_event import SimUniEvent
from sr.sim_uni.op.sim_uni_exit import SimUniExit
from sr.sim_uni.sim_uni_const import SimUniLevelType, SimUniLevelTypeEnum
from sr.sim_uni.sim_uni_priority import SimUniAllPriority
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
                 priority: Optional[SimUniAllPriority] = None,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        """
        模拟宇宙 按照特定路线执行
        最后返回 data=Point 最新坐标
        """
        self.route: SimUniRoute = route
        self.route_no_battle: bool = self.route.no_battle_op  # 路线上是否无战斗 可以优化移动的效率
        self.op_idx: int = -1
        self.current_pos: Point = self.route.start_pos
        self.priority: Optional[SimUniAllPriority] = priority

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
        next_op: Optional[SimUniRouteOperation] = None
        if self.op_idx + 1 < len(self.route.op_list):
            next_op = self.route.op_list[self.op_idx + 1]

        if current_op['op'] in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]:
            op = self.move(current_op, next_op)
        elif current_op['op'] == operation_const.OP_PATROL:
            op = SimUniEnterFight(self.ctx, priority=self.priority)
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
                                  priority=self.priority,
                                  no_battle=self.route_no_battle
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
                 priority: Optional[SimUniAllPriority] = None
                 ):
        """
        模拟宇宙 按照路线执行的基类
        """
        self.level_type: SimUniLevelType = level_type
        self.route: Optional[SimUniRoute] = None
        self.current_pos: Optional[Point] = None
        self.priority: Optional[SimUniAllPriority] = priority

        match = StateOperationNode('匹配路线', self._match_route)
        before_route = StateOperationNode('指令前初始化', self._before_route)
        run_route = StateOperationNode('执行路线指令', self._run_route)
        after_route = StateOperationNode('区域特殊指令', self._after_route)
        go_next = StateOperationNode('下一层', self._go_next)

        super().__init__(ctx,
                         op_name='%s %s' % (
                             gt('模拟宇宙', 'ui'),
                             gt('区域-%s' % level_type.type_name, 'ui')
                         ),
                         nodes=[match, before_route, run_route, after_route, go_next]
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
            self.route: SimUniRoute = op_result.data
            log.info('匹配路线 %s', self.route.display_name)

    def _run_route(self) -> OperationOneRoundResult:
        """
        执行下一个指令
        :return:
        """
        op = SimUniRunRouteOp(self.ctx, self.route, priority=self.priority, op_callback=self._update_pos)
        return Operation.round_by_op(op.execute())

    def _update_pos(self, op_result: OperationResult):
        """
        更新坐标
        :param op_result:
        :return:
        """
        if op_result.success:
            self.current_pos = op_result.data

    def _after_route(self) -> OperationOneRoundResult:
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
            op = MoveToNextLevel(self.ctx, priority=self.priority)
        else:
            op = MoveToNextLevelByRoute(self.ctx, self.route, self.current_pos, priority=self.priority)

        op = MoveToNextLevelByRoute(self.ctx, self.route, self.current_pos, priority=self.priority)

        return Operation.round_by_op(op.execute())


class SimUniRunCombatRoute(SimUniRunRouteBase):

    def __init__(self, ctx: Context, level_type: SimUniLevelType,
                 priority: Optional[SimUniAllPriority] = None,
                 ):

        super().__init__(ctx, level_type, priority=priority)


class SimUniInteractAfterRoute(StateOperation):

    STATUS_INTERACT: ClassVar[str] = '交互成功'

    def __init__(self, ctx: Context, interact_word: str,
                 no_icon: bool, can_ignore_interact: bool,
                 priority: Optional[SimUniAllPriority] = None,
                 ):
        """
        模拟宇宙 交互楼层移动到交互点后的处理
        事件、交易、遭遇、休整
        :param ctx:
        :param interact_word: 交互文本
        :param no_icon: 小地图上没有图标 说明可能已经交互过了
        :param can_ignore_interact: 可以不交互进入下一层 - 黑塔
        :param priority: 优先级
        """
        edges = []

        interact = StateOperationNode('交互', self._interact)
        event = StateOperationNode('事件', self._event)
        edges.append(StateOperationEdge(interact, event, status=SimUniInteractAfterRoute.STATUS_INTERACT))

        super().__init__(ctx, op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('事件交互', 'ui')),
                         edges=edges)

        self.priority: Optional[SimUniAllPriority] = priority
        self.interact_word: str = interact_word
        self.no_icon: bool = no_icon
        self.can_ignore_interact: bool = can_ignore_interact

    def _interact(self) -> OperationOneRoundResult:
        # 有图标的情况 就一定要交互 no_move=False
        # 没有图标的情况 可能时不需要交互 也可能时识别图标失败 先尝试交互 no_move=True
        op = Interact(self.ctx, self.interact_word, lcs_percent=0.1, single_line=True, no_move=self.no_icon)
        op_result = op.execute()
        if op_result.success:
            return Operation.round_success(SimUniInteractAfterRoute.STATUS_INTERACT, wait=1.5)
        else:
            if self.no_icon:  # 识别不到图标 又交互不到 就默认为之前已经交互了
                return Operation.round_success()
            if self.can_ignore_interact:
                # 本次交互失败 但可以跳过
                return Operation.round_success()
            else:
                return Operation.round_fail_by_op(op_result)

    def _event(self) -> OperationOneRoundResult:
        op = SimUniEvent(self.ctx, priority=self.priority,
                         skip_first_screen_check=False)
        return Operation.round_by_op(op.execute())  # 事件结束会回到大世界 不需要等待时间


class SimUniRunInteractRoute(SimUniRunRouteBase):

    def __init__(self, ctx: Context, level_type: SimUniLevelType,
                 priority: Optional[SimUniAllPriority] = None,
                 ):
        """
        需要交互的楼层使用
        :param ctx:
        """
        super().__init__(ctx, level_type, priority)

        is_respite = level_type == SimUniLevelTypeEnum.RESPITE.value
        self.icon_template_id: str = 'mm_sp_herta' if is_respite else 'mm_sp_event'
        self.interact_word: str = '黑塔' if is_respite else '事件'
        self.can_ignore_interact: bool = is_respite
        self.no_icon: bool = False  # 小地图上没有图标了 说明之前已经交互过了

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self.no_icon = False

    def _before_route(self) -> OperationOneRoundResult:
        """
        执行路线前的初始化 由各类型楼层自行实现
        检测小地图上的图标 在大地图上的哪个位置
        :return:
        """
        if self.level_type == SimUniLevelTypeEnum.RESPITE.value:
            self.ctx.controller.initiate_attack()
            time.sleep(0.5)

        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen)
        angle = mini_map.analyse_angle(mm)
        radio_to_del = mini_map.get_radio_to_del(self.ctx.im, angle)
        mm_del_radio = mini_map.remove_radio(mm, radio_to_del)
        icon_pos = self._get_icon_pos(mm_del_radio)
        if icon_pos is None:
            self.no_icon = True
            if len(self.route.op_list) == 0:  # 未配置路线时 需要识别到才能往下走
                return Operation.round_retry('未配置交互点坐标且识别交互图标失败')
            else:
                return Operation.round_success()
        else:
            if len(self.route.op_list) == 0:  # 未配置路线时 自动加入坐标
                mm_center_pos = Point(mm.shape[1] // 2, mm.shape[0] // 2)
                target_pos = self.route.start_pos + (icon_pos - mm_center_pos)
                op = SimUniRouteOperation(op=operation_const.OP_MOVE, data=[target_pos.x, target_pos.y])
                self.route.op_list.append(op)
                self.route.save()
            return Operation.round_success()

    def _after_route(self) -> OperationOneRoundResult:
        """
        执行路线后的特殊操作 由各类型楼层自行实现
        进行交互
        :return:
        """
        op = SimUniInteractAfterRoute(self.ctx, self.interact_word,
                                      self.no_icon, self.can_ignore_interact,
                                      self.priority)
        return Operation.round_by_op(op.execute())

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


class SimUniRunEliteRoute(SimUniRunRouteBase):

    def __init__(self, ctx: Context, level_type: SimUniLevelType,
                 priority: Optional[SimUniAllPriority] = None,
                 ):

        super().__init__(ctx, level_type, priority)

        self.with_enemy: bool = True
        self.no_icon: bool = False

    def _init_before_execute(self):
        super()._init_before_execute()
        self.with_enemy = True
        self.no_icon: bool = False

    def _before_route(self) -> OperationOneRoundResult:
        """
        执行路线前的初始化 由各类型楼层自行实现
        检测小地图上的红点 识别敌人 在大地图上的哪个位置
        :return:
        """
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen)
        angle = mini_map.analyse_angle(mm)
        radio_to_del = mini_map.get_radio_to_del(self.ctx.im, angle)
        mm_del_radio = mini_map.remove_radio(mm, radio_to_del)
        red_pos = mini_map.find_one_enemy_pos(mm_del_radio, self.ctx.im)
        if red_pos is None:
            self.no_icon = True
            if len(self.route.op_list) == 0:  # 未配置路线时 需要识别到才能往下走
                return Operation.round_retry('未配置坐标且识别地图红点失败')
            else:
                return Operation.round_success()
        else:
            if len(self.route.op_list) == 0:  # 未配置路线时 自动加入坐标
                mm_center_pos = Point(mm.shape[1] // 2, mm.shape[0] // 2)
                target_pos = self.route.start_pos + (red_pos - mm_center_pos)
                op = SimUniRouteOperation(op=operation_const.OP_MOVE, data=[target_pos.x, target_pos.y])
                self.route.op_list.append(op)
                self.route.save()
            return Operation.round_success()

    def _after_route(self) -> OperationOneRoundResult:
        if self.no_icon:
            return Operation.round_success()
        op = SimUniFightElite(self.ctx, priority=self.priority)
        return Operation.round_by_op(op.execute())

    def _go_next(self) -> OperationOneRoundResult:
        if self.level_type == SimUniLevelTypeEnum.ELITE.value:
            return super()._go_next()
        else:
            op = SimUniExit(self.ctx)
            return Operation.round_by_op(op.execute())
