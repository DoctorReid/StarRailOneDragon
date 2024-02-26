import time
from typing import Optional, ClassVar, Callable

from cv2.typing import MatLike

from basic import Point
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr import cal_pos
from sr.app.sim_uni.sim_uni_route_holder import match_best_sim_uni_route
from sr.config import game_config
from sr.const import operation_const
from sr.context import Context
from sr.image.sceenshot import mini_map, screen_state, large_map
from sr.operation import Operation, \
    OperationResult, StateOperation, StateOperationNode, OperationOneRoundResult, \
    StateOperationEdge
from sr.operation.unit.interact import Interact
from sr.operation.unit.move import MoveWithoutPos, MoveDirectly
from sr.screen_area.dialog import ScreenDialog
from sr.screen_area.screen_normal_world import ScreenNormalWorld
from sr.sim_uni.op.move_in_sim_uni import MoveDirectlyInSimUni, MoveToNextLevel
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight, SimUniFightElite
from sr.sim_uni.op.sim_uni_event import SimUniEvent
from sr.sim_uni.op.sim_uni_exit import SimUniExit
from sr.sim_uni.op.sim_uni_reward import SimUniReward
from sr.sim_uni.sim_uni_const import SimUniLevelType, SimUniLevelTypeEnum
from sr.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig
from sr.sim_uni.sim_uni_route import SimUniRouteOperation, SimUniRoute


class SimUniMatchRoute(Operation):

    STATUS_ROUTE_NOT_FOUND: ClassVar[str] = '匹配路线失败'

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
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        route = match_best_sim_uni_route(self.world_num, self.level_type, mm)

        if route is None:
            return Operation.round_retry(SimUniMatchRoute.STATUS_ROUTE_NOT_FOUND, wait=0.5)
        else:
            return Operation.round_success(data=route)


class SimUniRunRouteOp(StateOperation):

    STATUS_ALL_OP_DONE: ClassVar[str] = '执行结束'
    STATUS_USE_TECH: ClassVar[str] = '已使用秘技'

    def __init__(self, ctx: Context, route: SimUniRoute,
                 config: Optional[SimUniChallengeConfig] = None,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        """
        模拟宇宙 按照特定路线执行
        最后返回 data=Point 最新坐标
        """
        self.route: SimUniRoute = route
        self.route_no_battle: bool = self.route.no_battle_op  # 路线上是否无战斗 可以优化移动的效率
        self.op_idx: int = -1
        self.current_pos: Point = self.route.start_pos
        self.config: Optional[SimUniChallengeConfig] = config

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

    def _use_tech(self):
        """
        初始化
        :return:
        """
        if not self.config.technique_fight or self.ctx.technique_used:
            return Operation.round_success()

        screen = self.screenshot()
        state = screen_state.get_sim_uni_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                      in_world=True, fast_recover=True)

        if state == screen_state.ScreenState.NORMAL_IN_WORLD.value:
            pass

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
        elif current_op['op'] == operation_const.OP_NO_POS_MOVE:
            op = self._move_by_no_pos(current_op)
        elif current_op['op'] == operation_const.OP_PATROL:
            op = SimUniEnterFight(self.ctx, config=self.config)
        elif current_op['op'] == operation_const.OP_DISPOSABLE:
            op = SimUniEnterFight(self.ctx, config=self.config, disposable=True)
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
                                  config=self.config,
                                  no_battle=self.route_no_battle,
                                  no_run=current_op['op'] == operation_const.OP_SLOW_MOVE
                                  )
        return op

    def _move_by_no_pos(self, current_op: SimUniRouteOperation):
        start = self.current_pos
        target = Point(current_op['data'][0], current_op['data'][1])
        move_time = None if len(current_op['data']) < 3 else current_op['data'][2]
        return MoveWithoutPos(self.ctx, start, target, move_time=move_time, op_callback=self._update_pos)

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
                 world_num: int,
                 level_type: SimUniLevelType,
                 config: Optional[SimUniChallengeConfig] = None
                 ):
        """
        模拟宇宙 按照路线执行的基类
        """
        self.world_num: int = world_num
        self.level_type: SimUniLevelType = level_type
        self.route: Optional[SimUniRoute] = None
        self.current_pos: Optional[Point] = None
        self.config: Optional[SimUniChallengeConfig] = config

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
        op = SimUniMatchRoute(self.ctx, self.world_num, self.level_type,
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
        op = SimUniRunRouteOp(self.ctx, self.route, config=self.config, op_callback=self._update_pos)
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
        op = MoveToNextLevel(self.ctx, level_type=self.level_type, config=self.config,
                             current_pos=self.current_pos, next_pos_list=self.route.next_pos_list)

        return Operation.round_by_op(op.execute())


class SimUniRunCombatRoute(SimUniRunRouteBase):

    def __init__(self, ctx: Context, world_num: int, level_type: SimUniLevelType,
                 config: Optional[SimUniChallengeConfig] = None,
                 ):

        super().__init__(ctx, world_num, level_type, config=config)

    def _before_route(self) -> OperationOneRoundResult:
        """
        如果是秘技开怪 且是上buff类的 就在路线运行前上buff
        :return:
        """
        if not self.config.technique_fight or not self.ctx.is_buff_technique:
            return Operation.round_success()

        screen = self.screenshot()
        state = screen_state.get_sim_uni_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                      in_world=True, fast_recover=True)
        log.debug('当前画面 %s', state)
        if state == ScreenDialog.FAST_RECOVER_TITLE.value.text:  # 使用秘技后出现快速恢复对话框
            self.ctx.technique_used = False
            click = self.find_and_click_area(ScreenDialog.FAST_RECOVER_CONFIRM.value, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                return Operation.round_wait(wait=0.5)
            else:
                return Operation.round_retry('点击确认失败', wait=1.5)
        elif not self.ctx.technique_used:
            if state == ScreenNormalWorld.CHARACTER_ICON.value.status:
                self.ctx.controller.use_technique()
                self.ctx.technique_used = True
                return Operation.round_wait(wait=1.5)
            else:
                return Operation.round_retry('未在大世界画面', wait=1)
        else:
            return Operation.round_success()


class SimUniInteractAfterRoute(StateOperation):

    STATUS_INTERACT: ClassVar[str] = '交互成功'

    def __init__(self, ctx: Context, interact_word: str,
                 no_icon: bool, can_ignore_interact: bool,
                 config: Optional[SimUniChallengeConfig] = None,
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

        self.config: Optional[SimUniChallengeConfig] = config
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
        op = SimUniEvent(self.ctx, config=self.config,
                         skip_first_screen_check=False)
        op_result = op.execute()
        # 事件结束会回到大世界 不需要等待时间
        if op_result.success:
            return Operation.round_by_op(op_result)
        else:
            if self.can_ignore_interact:
                # 本次交互失败 但可以跳过
                return Operation.round_success()
            else:
                return Operation.round_by_op(op_result)


class SimUniRunInteractRoute(SimUniRunRouteBase):

    def __init__(self, ctx: Context, world_num: int, level_type: SimUniLevelType,
                 config: Optional[SimUniChallengeConfig] = None,
                 ):
        """
        需要交互的楼层使用
        :param ctx:
        """
        super().__init__(ctx, world_num, level_type, config)

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
        cal_pos = self._cal_interact_pos()

        if self.level_type == SimUniLevelTypeEnum.RESPITE.value:
            op = SimUniEnterFight(self.ctx, config=self.config, disposable=True)  # 攻击可破坏物 统一用这个处理大乐透
            op_result = op.execute()
            if not op_result.success:
                return Operation.round_fail('攻击可破坏物失败')

        if not cal_pos:
            return Operation.round_retry('未配置交互点坐标且识别交互图标失败')
        else:
            return Operation.round_success()

    def _cal_interact_pos(self) -> bool:
        """
        计算交互点的位置
        :return:
        """
        is_respite = self.level_type == SimUniLevelTypeEnum.RESPITE.value
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        angle = mini_map.analyse_angle(mm)
        radio_to_del = mini_map.get_radio_to_del(self.ctx.im, angle)
        mm_del_radio = mini_map.remove_radio(mm, radio_to_del)
        icon_pos = self._get_icon_pos(mm_del_radio)
        if icon_pos is None:
            self.no_icon = True
            if len(self.route.op_list) == 0:  # 未配置路线时 需要识别到才能往下走
                return False
            else:
                return True
        else:
            if len(self.route.op_list) == 0:  # 未配置路线时 自动加入坐标
                mm_center_pos = Point(mm.shape[1] // 2, mm.shape[0] // 2)
                target_pos = self.route.start_pos + (icon_pos - mm_center_pos)
                op = SimUniRouteOperation(op=operation_const.OP_SLOW_MOVE if is_respite else operation_const.OP_MOVE,
                                          data=[target_pos.x, target_pos.y])
                self.route.op_list.append(op)
                self.route.save()
            return True

    def _after_route(self) -> OperationOneRoundResult:
        """
        执行路线后的特殊操作 由各类型楼层自行实现
        进行交互
        :return:
        """
        op = SimUniInteractAfterRoute(self.ctx, self.interact_word,
                                      self.no_icon, self.can_ignore_interact,
                                      self.config)
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


class SimUniRunEliteAfterRoute(StateOperation):

    STATUS_NO_REWARD_POS: ClassVar[str] = '未配置奖励坐标'
    STATUS_NO_NEED_REWARD: ClassVar[str] = '无需获取奖励'

    def __init__(self, ctx: Context, level_type: SimUniLevelType,
                 current_pos: Point, route: SimUniRoute,
                 max_reward_to_get: int = 0,
                 config: Optional[SimUniChallengeConfig] = None,
                 get_reward_callback: Optional[Callable[[int, int], None]] = None,
                 op_callback: Optional[Callable[[OperationResult], None]] = None
                 ):
        """
        挑战精英并领取奖励
        最后返回 data=角色最新坐标
        :param ctx:
        :param level_type:
        :param priority:
        """
        edges = []
        fight = StateOperationNode('战斗', self._fight)
        back_to_angle = StateOperationNode('恢复转向', self._turn_to_original_angle)
        edges.append(StateOperationEdge(fight, back_to_angle))

        cal_pos_after_fight = StateOperationNode('更新坐标', self._cal_pos_after_fight)
        edges.append(StateOperationEdge(back_to_angle, cal_pos_after_fight))

        move = StateOperationNode('移动奖励', self._move_to_reward)
        edges.append(StateOperationEdge(cal_pos_after_fight, move))

        interact = StateOperationNode('交互', self._interact)
        edges.append(StateOperationEdge(move, interact))

        get_reward = StateOperationNode('获取奖励', self._get_reward)
        edges.append(StateOperationEdge(interact, get_reward))

        esc = StateOperationNode('结束', self._esc)
        edges.append(StateOperationEdge(move, esc, status=SimUniRunEliteAfterRoute.STATUS_NO_NEED_REWARD))  # 无需领奖励的
        edges.append(StateOperationEdge(interact, esc, success=False))  # 交互失败了 也继续
        edges.append(StateOperationEdge(get_reward, esc))  # 领取奖励成功

        super().__init__(ctx, try_times=5,
                         op_name='%s %s %s' % (
                             gt('模拟宇宙', 'ui'),
                             gt('区域-%s' % level_type.type_name, 'ui'),
                             gt('路线后', 'ui')
                         ),
                         edges=edges,
                         op_callback=op_callback
                         )

        self.level_type: SimUniLevelType = level_type
        self.current_pos: Point = current_pos  # 当前位置
        self.route: SimUniRoute = route
        self.config: Optional[SimUniChallengeConfig] = config
        self.max_reward_to_get: int = max_reward_to_get  # 最多获取多少次奖励
        self.get_reward_callback: Optional[Callable[[int, int], None]] = get_reward_callback  # 获取奖励后的回调

    def _fight(self) -> OperationOneRoundResult:
        op = SimUniFightElite(self.ctx, config=self.config)
        return Operation.round_by_op(op.execute())

    def _turn_to_original_angle(self):
        """
        攻击精英怪后人物朝向有可能改变 先恢复到原来的朝向
        :return:
        """
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        angle = mini_map.analyse_angle(mm)
        start_pos = self.route.start_pos
        elite_pos = self.route.op_list[0]['data']
        elite_pos = Point(elite_pos[0], elite_pos[1])
        self.ctx.controller.turn_by_pos(start_pos, elite_pos, angle)
        return Operation.round_success(wait=0.5)  # 等待转向

    def _cal_pos_after_fight(self):
        """
        移动停止后的惯性可能导致人物偏移 更新坐标方便进入沉浸奖励
        :return:
        """
        if self.route.last_op['op'] == operation_const.OP_NO_POS_MOVE:
            return Operation.round_success()
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        mm_info = mini_map.analyse_mini_map(mm, self.ctx.im)

        lm_info = self.ctx.ih.get_large_map(self.route.region)

        possible_pos = (self.current_pos.x, self.current_pos.y, self.ctx.controller.run_speed)
        lm_rect = large_map.get_large_map_rect_by_pos(lm_info.gray.shape, mm.shape[:2], possible_pos)

        next_pos = cal_pos.sim_uni_cal_pos(self.ctx.im, lm_info, mm_info,
                                           possible_pos=possible_pos,
                                           lm_rect=lm_rect,
                                           running=self.ctx.controller.is_moving)

        if next_pos is not None:
            self.current_pos = next_pos
            return Operation.round_success()
        else:
            return Operation.round_retry(MoveDirectly.STATUS_NO_POS, wait=1)

    def _move_to_reward(self) -> OperationOneRoundResult:
        gc = self.ctx.game_config
        if self.max_reward_to_get <= 0 and not self.ctx.one_dragon_config.is_debug:
            return Operation.round_success(SimUniRunEliteAfterRoute.STATUS_NO_NEED_REWARD)
        elif self.route.reward_pos is None:
            return Operation.round_fail(SimUniRunEliteAfterRoute.STATUS_NO_REWARD_POS)

        # op = MoveDirectlyInSimUni(self.ctx, self.ctx.ih.get_large_map(self.route.region),
        #                           start=self.current_pos, target=self.route.reward_pos,
        #                           op_callback=self._update_pos,
        #                           no_battle=True, no_run=True,
        #                           )
        op = MoveWithoutPos(self.ctx,
                            start=self.current_pos, target=self.route.reward_pos,
                            op_callback=self._update_pos,
                            )
        return Operation.round_by_op(op.execute())

    def _update_pos(self, op_result: OperationResult):
        """
        移动后更新坐标
        :param op_result:
        :return:
        """
        self.current_pos = op_result.data

    def _interact(self) -> OperationOneRoundResult:
        """
        交互进入沉浸奖励
        :return:
        """
        op = Interact(self.ctx, '沉浸奖励', lcs_percent=0.1, single_line=True)
        return Operation.round_by_op(op.execute())

    def _get_reward(self) -> OperationOneRoundResult:
        """
        获取奖励
        :return:
        """
        op = SimUniReward(self.ctx, self.max_reward_to_get, self.get_reward_callback)
        return Operation.round_by_op(op.execute())

    def _esc(self) -> OperationOneRoundResult:
        """
        所有操作完成后结束
        :return:
        """
        return Operation.round_success(data=self.current_pos)


class SimUniRunEliteRoute(SimUniRunRouteBase):

    def __init__(self, ctx: Context, world_num: int, level_type: SimUniLevelType,
                 config: Optional[SimUniChallengeConfig] = None,
                 max_reward_to_get: int = 0,
                 get_reward_callback: Optional[Callable[[int, int], None]] = None
                 ):

        super().__init__(ctx, world_num, level_type, config)

        self.with_enemy: bool = True
        self.no_icon: bool = False
        self.max_reward_to_get: int = max_reward_to_get  # 最多获取多少次奖励
        self.get_reward_callback: Optional[Callable[[int, int], None]] = get_reward_callback  # 获取奖励后的回调

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
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        red_pos = mini_map.find_one_enemy_pos(self.ctx.im, mm=mm)
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
        op = SimUniRunEliteAfterRoute(self.ctx, self.level_type,
                                      self.current_pos, self.route,
                                      config=self.config,
                                      max_reward_to_get=self.max_reward_to_get,
                                      get_reward_callback=self.get_reward_callback,
                                      op_callback=self._update_pos
                                      )
        return Operation.round_by_op(op.execute())

    def _go_next(self) -> OperationOneRoundResult:
        if self.level_type == SimUniLevelTypeEnum.ELITE.value:
            return super()._go_next()
        else:
            op = SimUniExit(self.ctx)
            return Operation.round_by_op(op.execute())
