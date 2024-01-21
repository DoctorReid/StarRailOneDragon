import time
from typing import Optional, ClassVar, List

from cv2.typing import MatLike

from basic import Point
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.const import operation_const
from sr.context import Context
from sr.image.sceenshot import screen_state, mini_map
from sr.operation import Operation, \
    OperationResult, OperationFail, OperationSuccess, StateOperation, StateOperationNode, OperationOneRoundResult
from sr.operation.battle.start_fight import Attack, StartFightWithTechnique
from sr.operation.combine import StatusCombineOperation2, StatusCombineOperationNode, StatusCombineOperationEdge2
from sr.operation.unit.interact import Interact
from sr.operation.unit.move import SimplyMoveByPos, MoveToEnemy
from sr.operation.unit.team import SwitchMember
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sr.sim_uni.op.move_in_sim_uni import MoveDirectlyInSimUni
from sr.sim_uni.sim_uni_priority import SimUniBlessPriority, SimUniCurioPriority
from sr.sim_uni.sim_uni_route import SimUniRouteOperation, SimUniRoute


class SimUniRunRoute(StatusCombineOperation2):

    def __init__(self, ctx: Context, route: SimUniRoute,
                 bless_priority: Optional[SimUniBlessPriority] = None):
        """
        按照特定路线执行
        """
        self.route: SimUniRoute = route
        self.op_idx: int = -1
        self.current_pos: Point = self.route.start_pos
        self.bless_priority: SimUniBlessPriority = bless_priority

        op_node = StatusCombineOperationNode('执行路线指令', op_func=self._next_op)
        finish_node = StatusCombineOperationNode('结束', OperationSuccess(ctx))
        go_next = StatusCombineOperationEdge2(op_node, op_node, ignore_status=True)
        go_finish = StatusCombineOperationEdge2(op_node, finish_node, status='执行结束')

        edges = [go_next, go_finish]

        super().__init__(ctx,
                         op_name='%s %s %s' % (
                             gt('模拟宇宙', 'ui'),
                             gt('战斗路线', 'ui'),
                             route.display_name
                         ),
                         edges=edges,
                         specified_start_node=op_node)

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self.op_idx = -1
        self.current_pos: Point = self.route.start_pos

    def _next_op(self) -> Operation:
        """
        获取下一个具体的指令
        :return:
        """
        self.op_idx += 1

        if self.op_idx >= len(self.route.op_list):
            return OperationSuccess(self.ctx, '执行结束')

        current_op: SimUniRouteOperation = self.route.op_list[self.op_idx]
        next_op: Optional[SimUniRouteOperation] = self.route.op_list[self.op_idx + 1] if self.op_idx + 1 < len(self.route.op_list) else None

        if current_op['op'] in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]:
            return self.move(current_op, next_op)
        elif current_op['op'] == operation_const.OP_PATROL:
            return SimUniEnterFight(self.ctx, bless_priority=self.bless_priority)
        else:
            return OperationFail(self.ctx, status='未知指令')

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
        self.can_ignor_interact: bool = can_ignor_interact  # 是否可以忽略交互失败

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self.target_pos = None
        if len(self.route.op_list) > 0:
            pos = self.route.op_list[0]['data']
            self.target_pos = Point(pos[0], pos[1])
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
        if self.no_icon:  # 没有图标 不需要交互了
            return Operation.round_success(SimUniRunInteractRoute.STATUS_ICON_NOT_FOUND)
        op = Interact(self.ctx, self.interact_word, lcs_percent=0.1, single_line=True)
        op_result = op.execute()
        if op_result.success:
            return Operation.round_success()
        else:
            if self.can_ignor_interact:
                log.info('交互失败 跳过')
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


class SimUniRunEliteRoute(StatusCombineOperation2):

    def __init__(self, ctx: Context,
                 bless_priority: Optional[SimUniBlessPriority] = None,
                 curio_priority: Optional[SimUniCurioPriority] = None):
        edges: List[StatusCombineOperationEdge2] = []

        move = StatusCombineOperationNode('移动', MoveToEnemy(ctx))

        enter_fight = StatusCombineOperationNode('秘技进入战斗', StartFightWithTechnique(ctx))
        edges.append(StatusCombineOperationEdge2(move, enter_fight))

        fight = StatusCombineOperationNode('战斗', SimUniEnterFight(ctx,
                                                                    bless_priority=bless_priority,
                                                                    curio_priority=curio_priority)
                                           )
        edges.append(StatusCombineOperationEdge2(enter_fight, fight))

        switch = StatusCombineOperationNode('切换1号位', SwitchMember(ctx, 1))
        edges.append(StatusCombineOperationEdge2(fight, switch))

        no_enemy = StatusCombineOperationNode('无敌人', OperationSuccess(ctx))
        edges.append(StatusCombineOperationEdge2(move, no_enemy, success=False, status=MoveToEnemy.STATUS_ENEMY_NOT_FOUND))

        SimUniEnterFight(ctx, bless_priority=bless_priority, curio_priority=curio_priority)

        super().__init__(ctx,
                         op_name='%s %s' % (
                             gt('模拟宇宙', 'ui'),
                             gt('精英路线', 'ui'),
                         ),
                         edges=edges
                         )
