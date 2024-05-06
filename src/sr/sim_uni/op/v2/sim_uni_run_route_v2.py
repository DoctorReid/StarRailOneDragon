import time
from typing import List, ClassVar, Optional, Callable

from cv2.typing import MatLike

from basic import Point, cal_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot import mini_map, screen_state, MiniMapInfo
from sr.operation import StateOperation, StateOperationEdge, StateOperationNode, OperationOneRoundResult, Operation, \
    OperationResult
from sr.operation.unit.interact import Interact
from sr.operation.unit.move import MoveWithoutPos
from sr.sim_uni.op.move_in_sim_uni import MoveToNextLevel
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight, SimUniFightElite
from sr.sim_uni.op.sim_uni_event import SimUniEvent
from sr.sim_uni.op.sim_uni_exit import SimUniExit
from sr.sim_uni.op.sim_uni_reward import SimUniReward
from sr.sim_uni.op.v2.sim_uni_move_v2 import SimUniMoveToEnemyByMiniMap, SimUniMoveToEnemyByDetect, delta_angle_to_detected_object, SimUniMoveToInteractByDetect
from sr.sim_uni.sim_uni_const import SimUniLevelTypeEnum, SimUniLevelType
from sryolo.detector import DetectResult, draw_detections


class SimUniRunRouteBase(StateOperation):

    STATUS_FIGHT: ClassVar[str] = '遭遇战斗'
    STATUS_WITH_RED: ClassVar[str] = '小地图有红点'
    STATUS_NO_RED: ClassVar[str] = '小地图无红点'
    STATUS_WITH_MM_EVENT: ClassVar[str] = '小地图有事件'
    STATUS_NO_MM_EVENT: ClassVar[str] = '小地图无事件'
    STATUS_WITH_DETECT_EVENT: ClassVar[str] = '识别到事件'
    STATUS_NO_DETECT_EVENT: ClassVar[str] = '识别不到事件'
    STATUS_WITH_ENEMY: ClassVar[str] = '识别到敌人'
    STATUS_NO_ENEMY: ClassVar[str] = '识别不到敌人'
    STATUS_WITH_ENTRY: ClassVar[str] = '识别到下层入口'
    STATUS_NO_ENTRY: ClassVar[str] = '识别不到下层入口'
    STATUS_NOTHING: ClassVar[str] = '识别不到任何内容'
    STATUS_BOSS_EXIT: ClassVar[str] = '首领后退出'
    STATUS_HAD_EVENT: ClassVar[str] = '已处理事件'
    STATUS_HAD_FIGHT: ClassVar[str] = '已进行战斗'
    STATUS_NO_NEED_REWARD: ClassVar[str] = '无需沉浸奖励'
    STATUS_WITH_DETECT_REWARD: ClassVar[str] = '识别到沉浸奖励'
    STATUS_NO_DETECT_REWARD: ClassVar[str] = '识别不到沉浸奖励'
    STATUS_WITH_DANGER: ClassVar[str] = '被敌人锁定'

    def __init__(self, ctx: Context, level_type: SimUniLevelType,
                 try_times: int = 2,
                 nodes: Optional[List[StateOperationNode]] = None,
                 edges: Optional[List[StateOperationEdge]] = None,
                 specified_start_node: Optional[StateOperationNode] = None,
                 timeout_seconds: float = -1,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        StateOperation.__init__(self,
                                ctx=ctx, try_times=try_times,
                                op_name=gt('区域-%s' % level_type.type_name, 'ui'),
                                nodes=nodes, edges=edges, specified_start_node=specified_start_node,
                                timeout_seconds=timeout_seconds, op_callback=op_callback)

        self.level_type: SimUniLevelType = level_type  # 楼层类型
        self.moved_to_target: bool = False  # 是否已经产生了朝向目标的移动
        self.nothing_times: int = 0  # 识别不到任何内容的次数
        self.previous_angle: float = 0  # 之前的朝向 识别到目标时应该记录下来 后续可以在这个方向附近找下一个目标

    def _before_route(self) -> OperationOneRoundResult:
        """
        路线开始前
        1. 按照小地图识别初始的朝向
        2. 等待头顶的区域文本消失？
        :return:
        """
        screen = self.screenshot()
        self._check_angle(screen)
        return Operation.round_success()

    def _check_angle(self, screen: Optional[MatLike] = None):
        """
        检测并更新角度
        :return:
        """
        if screen is None:
            screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        self.previous_angle = mini_map.analyse_angle(mm)

    def _turn_to_previous_angle(self, screen: Optional[MatLike] = None) -> OperationOneRoundResult:
        """
        战斗后的处理 先转到原来的朝向 再取找下一个目标
        :return:
        """
        if screen is None:
            screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        angle = mini_map.analyse_angle(mm)
        self.ctx.controller.turn_from_angle(angle, self.previous_angle)
        self.moved_to_target = False
        return Operation.round_success(wait=0.2)

    def _check_next_entry(self) -> OperationOneRoundResult:
        """
        找下层入口 主要判断能不能找到
        :return:
        """
        if self.level_type == SimUniLevelTypeEnum.BOSS.value:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_BOSS_EXIT)
        self._view_up()
        screen: MatLike = self.screenshot()
        entry_list = MoveToNextLevel.get_next_level_type(screen, self.ctx.ih)
        if len(entry_list) == 0:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_NO_ENTRY)
        else:
            self.nothing_times = 0
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_WITH_ENTRY)

    def _move_to_next(self):
        """
        朝下层移动
        :return:
        """
        self._view_up()
        self.nothing_times = 0
        self.moved_to_target = True
        op = MoveToNextLevel(self.ctx, level_type=self.level_type)
        return Operation.round_by_op(op.execute())

    def _turn_when_nothing(self) -> OperationOneRoundResult:
        """
        当前画面识别不到任何内容时候 转动一下
        :return:
        """
        self.nothing_times += 1

        if not self.moved_to_target:
            # 还没有产生任何移动的情况下 又识别不到任何内容 则可能是距离较远导致。先尝试往前走1秒
            self.ctx.controller.move('w', 1)
            self.moved_to_target = True
            return Operation.round_success()

        if self.nothing_times >= 23:
            return Operation.round_fail(SimUniRunRouteBase.STATUS_NOTHING)

        # angle = (25 + 10 * self.nothing_times) * (1 if self.nothing_times % 2 == 0 else -1)  # 来回转动视角
        # 由于攻击之后 人物可能朝反方向了 因此要转动多一点
        # 不要被360整除 否则转一圈之后还是被人物覆盖了看不到
        angle = 35
        self.ctx.controller.turn_by_angle(angle)
        time.sleep(0.5)

        if self.nothing_times % 11 == 0:
            # 大概转了一圈之后还没有找到东西 就往之前的方向走一点
            self.moved_to_target = False
            return self._turn_to_previous_angle()

        return Operation.round_success()

    def _view_down(self):
        """
        视角往下移动 方便识别目标
        :return:
        """
        if self.ctx.detect_info.view_down:
            return
        self.ctx.controller.turn_down(25)
        self.ctx.detect_info.view_down = True
        time.sleep(0.2)

    def _view_up(self):
        """
        视角往上移动 恢复原来的视角
        :return:
        """
        if not self.ctx.detect_info.view_down:
            return
        self.ctx.controller.turn_down(-25)
        self.ctx.detect_info.view_down = False
        time.sleep(0.2)


class SimUniRunCombatRouteV2(SimUniRunRouteBase):

    def __init__(self, ctx: Context, level_type: SimUniLevelType = SimUniLevelTypeEnum.COMBAT.value):
        """
        区域-战斗
        1. 检测地图是否有红点
        2. 如果有红点 移动到最近的红点 并进行攻击。攻击一次后回到步骤1判断。
        3. 如果没有红点 识别敌对物种位置，向最大的移动，并进行攻击。攻击一次后回到步骤1判断。
        4. 如果没有红点也没有识别到敌对物种，检测下层入口位置，发现后进入下层移动。未发现则选择视角返回步骤1判断。
        """
        edges: List[StateOperationEdge] = []

        before_route = StateOperationNode('区域开始前', self._before_route)

        check = StateOperationNode('画面检测', self._check_screen)
        edges.append(StateOperationEdge(before_route, check))

        # 小地图有红点 就按红点移动
        move_by_red = StateOperationNode('向红点移动', self._move_by_red)
        edges.append(StateOperationEdge(check, move_by_red, status=SimUniRunRouteBase.STATUS_WITH_RED))

        # 小地图没有红点 就在画面上找敌人
        detect_screen = StateOperationNode('识别敌人', self._detect_screen)
        edges.append(StateOperationEdge(check, detect_screen, status=SimUniRunRouteBase.STATUS_NO_RED))
        # 找到了敌人就开始移动
        move_by_detect = StateOperationNode('向敌人移动', self._move_by_detect)
        edges.append(StateOperationEdge(detect_screen, move_by_detect, status=SimUniRunRouteBase.STATUS_WITH_ENEMY))
        # 到达后开始战斗
        fight = StateOperationNode('进入战斗', self._enter_fight)
        edges.append(StateOperationEdge(move_by_red, fight, status=SimUniMoveToEnemyByMiniMap.STATUS_ARRIVAL))
        # 识别到被锁定也进入战斗
        edges.append(StateOperationEdge(detect_screen, fight, status=SimUniRunRouteBase.STATUS_WITH_DANGER))
        # 进行了战斗 就重新开始
        after_fight = StateOperationNode('战斗后处理', self._turn_to_previous_angle)
        edges.append(StateOperationEdge(fight, after_fight))
        edges.append(StateOperationEdge(after_fight, check))
        # 其它可能会进入战斗的情况
        edges.append(StateOperationEdge(check, after_fight, status=SimUniRunRouteBase.STATUS_FIGHT))
        edges.append(StateOperationEdge(move_by_red, after_fight, status=SimUniMoveToEnemyByMiniMap.STATUS_FIGHT))
        edges.append(StateOperationEdge(move_by_detect, after_fight, status=SimUniMoveToEnemyByDetect.STATUS_FIGHT))

        # 画面上识别不到任何内容时 使用旧的方法进行识别下层入口兜底
        check_entry = StateOperationNode('识别下层入口', self._check_next_entry)
        edges.append(StateOperationEdge(detect_screen, check_entry, status=SimUniRunRouteBase.STATUS_NO_ENEMY))
        edges.append(StateOperationEdge(move_by_detect, check_entry, success=False, status=SimUniMoveToEnemyByDetect.STATUS_NO_ENEMY))
        # 找到了下层入口就开始移动
        move_to_next = StateOperationNode('向下层移动', self._move_to_next)
        edges.append(StateOperationEdge(check_entry, move_to_next, status=SimUniRunRouteBase.STATUS_WITH_ENTRY))
        edges.append(StateOperationEdge(detect_screen, move_to_next, status=SimUniRunRouteBase.STATUS_WITH_ENTRY))

        # 找不到下层入口就转向找目标
        turn = StateOperationNode('转动找目标', self._turn_when_nothing)
        edges.append(StateOperationEdge(check_entry, turn, status=SimUniRunRouteBase.STATUS_NO_ENTRY))
        # 移动到下层入口失败时 也转动找目标
        # 可能1 走过了 没交互成功
        # 可能2 识别错了未激活的入口 移动过程中被攻击了
        edges.append(StateOperationEdge(move_to_next, turn, success=False))
        # 转动完重新开始目标识别
        edges.append(StateOperationEdge(turn, check))

        super().__init__(ctx, level_type=level_type,
                         edges=edges,
                         specified_start_node=before_route)

        self.last_state: str = ''  # 上一次的画面状态
        self.current_state: str = ''  # 这一次的画面状态

    def _check_screen(self) -> OperationOneRoundResult:
        """
        检测屏幕
        :return:
        """
        screen = self.screenshot()

        # 为了保证及时攻击 外层仅判断是否在大世界画面 非大世界画面时再细分处理
        self.current_state = screen_state.get_sim_uni_screen_state(
            screen, self.ctx.im, self.ctx.ocr,
            in_world=True, battle=True)
        log.debug('当前画面 %s', self.current_state)

        if self.current_state == screen_state.ScreenState.NORMAL_IN_WORLD.value:
            return self._handle_in_world(screen)
        else:
            return self._handle_not_in_world(screen)

    def _handle_in_world(self, screen: MatLike) -> OperationOneRoundResult:
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        mm_info: MiniMapInfo = mini_map.analyse_mini_map(mm)

        if mini_map.is_under_attack_new(mm_info, danger=True):
            op = SimUniEnterFight(self.ctx)
            op_result = op.execute()
            if op_result.success:
                return Operation.round_success(status=SimUniRunRouteBase.STATUS_FIGHT)
            else:
                return Operation.round_by_op(op_result)

        pos, _ = mini_map.get_closest_enemy_pos(mm_info)

        if pos is None:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_NO_RED)
        else:
            self.previous_angle = cal_utils.get_angle_by_pts(Point(0, 0), pos)  # 记录有目标的方向
            if self.ctx.one_dragon_config.is_debug:  # 红点已经比较成熟 调试时强制使用yolo
                return Operation.round_success(status=SimUniRunRouteBase.STATUS_NO_RED)
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_WITH_RED)

    def _move_by_red(self) -> OperationOneRoundResult:
        """
        朝小地图红点走去
        :return:
        """
        self.nothing_times = 0
        self.moved_to_target = True
        op = SimUniMoveToEnemyByMiniMap(self.ctx)
        return Operation.round_by_op(op.execute())

    def _enter_fight(self) -> OperationOneRoundResult:
        op = SimUniEnterFight(self.ctx,
                              first_state=screen_state.ScreenState.NORMAL_IN_WORLD.value,
                              )
        return op.round_by_op(op.execute())

    def _handle_not_in_world(self, screen: MatLike) -> OperationOneRoundResult:
        """
        不在大世界的场景 无论是什么 都可以交给 SimUniEnterFight 处理
        :param screen:
        :return:
        """
        op = SimUniEnterFight(self.ctx, config=self.ctx.sim_uni_challenge_config)
        op_result = op.execute()
        if op_result.success:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_FIGHT)
        else:
            return Operation.round_by_op(op_result)

    def _detect_screen(self) -> OperationOneRoundResult:
        """
        没有红点时 对画面进行目标识别
        :return:
        """
        self._view_down()
        screen: MatLike = self.screenshot()

        self.ctx.init_yolo()
        detect_results: List[DetectResult] = self.ctx.yolo.detect(screen)

        with_enemy: bool = False
        with_entry: bool = False
        with_danger: bool = False
        delta_angle: float = 0
        cnt: int = 0
        for result in detect_results:
            valid = False
            if result.detect_class.class_cate == '普通怪':
                with_enemy = True
                valid = True
            elif result.detect_class.class_cate == '模拟宇宙下层入口':
                with_entry = True
                valid = True
            elif result.detect_class.class_cate == '模拟宇宙下层入口未激活':
                valid = True
            elif result.detect_class.class_cate == '界面提示被锁定':
                with_danger = True

            if valid:
                delta_angle += delta_angle_to_detected_object(result)
                cnt += 1

        if cnt > 0:
            avg_delta_angle = delta_angle / cnt
            mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
            angle = mini_map.analyse_angle(mm)
            self.previous_angle = cal_utils.angle_add(angle, avg_delta_angle)

        if with_danger:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_WITH_DANGER)
        elif with_enemy:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_WITH_ENEMY)
        elif with_entry:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_WITH_ENTRY)
        else:
            if self.ctx.one_dragon_config.is_debug:
                self.save_screenshot()
                cv2_utils.show_image(draw_detections(screen, detect_results), win_name='combat_detect_screen')
            return Operation.round_success(SimUniRunRouteBase.STATUS_NOTHING)

    def _move_by_detect(self) -> OperationOneRoundResult:
        """
        识别到敌人人开始移动
        :return:
        """
        self.nothing_times = 0
        self.moved_to_target = True
        op = SimUniMoveToEnemyByDetect(self.ctx)
        return Operation.round_by_op(op.execute())


class SimUniRunEliteRouteV2(SimUniRunRouteBase):

    def __init__(self, ctx: Context, level_type: SimUniLevelType = SimUniLevelTypeEnum.ELITE.value,
                 max_reward_to_get: int = 0,
                 get_reward_callback: Optional[Callable[[int, int], None]] = None,):
        """
        区域-精英
        1. 检查小地图是否有红点 有就向红点移动
        2. 开怪
        3. 领取奖励
        4. 朝下层移动
        :param ctx: 上下文
        :param level_type: 楼层类型
        :param max_reward_to_get: 最多获取多少次奖励
        :param get_reward_callback: 获取奖励后的回调
        """
        edges: List[StateOperationEdge] = []

        before_route = StateOperationNode('区域开始前', self._before_route)

        check_red = StateOperationNode('识别小地图红点', self._check_red)
        edges.append(StateOperationEdge(before_route, check_red))

        # 有红点就靠红点移动
        move_by_red = StateOperationNode('向红点移动', self._move_by_red)
        edges.append(StateOperationEdge(check_red, move_by_red, status=SimUniRunRouteBase.STATUS_WITH_RED))

        # 到达精英怪旁边发起攻击
        start_fight = StateOperationNode('进入战斗', self._enter_fight)
        edges.append(StateOperationEdge(move_by_red, start_fight, status=SimUniMoveToEnemyByMiniMap.STATUS_ARRIVAL))

        # 战斗后处理
        after_fight = StateOperationNode('战斗后处理', self._turn_to_previous_angle)
        edges.append(StateOperationEdge(start_fight, after_fight))

        # 战斗后识别沉浸奖励装置
        detect_reward = StateOperationNode('识别沉浸奖励', self._detect_reward)
        edges.append(StateOperationEdge(after_fight, detect_reward))
        edges.append(StateOperationEdge(check_red, detect_reward, status=SimUniRunRouteBase.STATUS_HAD_FIGHT))
        # 没红点时 识别沉浸奖励装置
        edges.append(StateOperationEdge(check_red, detect_reward, status=SimUniRunRouteBase.STATUS_NO_RED))

        # 朝沉浸奖励装置移动
        move_to_reward = StateOperationNode('朝沉浸奖励移动', self._move_to_reward)
        edges.append(StateOperationEdge(detect_reward, move_to_reward, status=SimUniRunRouteBase.STATUS_WITH_DETECT_REWARD))

        # 领取奖励
        get_reward = StateOperationNode('领取沉浸奖励', self._get_reward)
        edges.append(StateOperationEdge(move_to_reward, get_reward, status=SimUniMoveToInteractByDetect.STATUS_INTERACT))

        # 无需领奖励 或者 领取奖励后 识别下层入口
        check_entry = StateOperationNode('识别下层入口', self._check_next_entry)
        edges.append(StateOperationEdge(detect_reward, check_entry, status=SimUniRunRouteBase.STATUS_NO_NEED_REWARD))
        edges.append(StateOperationEdge(get_reward, check_entry))
        # 找到了下层入口就开始移动
        move_to_next = StateOperationNode('向下层移动', self._move_to_next)
        edges.append(StateOperationEdge(check_entry, move_to_next, status=SimUniRunRouteBase.STATUS_WITH_ENTRY))
        # 找不到下层入口 就转向重新开始
        turn = StateOperationNode('转动找目标', self._turn_when_nothing)
        edges.append(StateOperationEdge(check_entry, turn, status=SimUniRunRouteBase.STATUS_NO_ENTRY))
        edges.append(StateOperationEdge(turn, check_red))
        # 需要领取沉浸奖励 而又找不到沉浸奖励时 也转向重新开始
        edges.append(StateOperationEdge(detect_reward, turn, status=SimUniRunRouteBase.STATUS_NO_DETECT_REWARD))

        # 首领后退出
        boss_exit = StateOperationNode('首领后退出', self._boss_exit)
        edges.append(StateOperationEdge(check_entry, boss_exit, status=SimUniRunRouteBase.STATUS_BOSS_EXIT))

        super().__init__(ctx, level_type=level_type,
                         edges=edges,
                         specified_start_node=before_route
                         )

        self.had_fight: bool = False  # 已经进行过战斗了
        self.had_reward: bool = False  # 已经拿过沉浸奖励了
        self.max_reward_to_get: int = max_reward_to_get  # 最多获取多少次奖励
        self.get_reward_callback: Optional[Callable[[int, int], None]] = get_reward_callback  # 获取奖励后的回调

    def _check_red(self) -> OperationOneRoundResult:
        """
        检查小地图是否有红点
        :return:
        """
        if self.had_fight:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_HAD_FIGHT)
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        mm_info = mini_map.analyse_mini_map(mm)
        pos_list = mini_map.get_enemy_pos(mm_info)
        if len(pos_list) == 0:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_NO_RED)
        else:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_WITH_RED)

    def _move_by_red(self) -> OperationOneRoundResult:
        """
        往小地图红点移动
        :return:
        """
        self.nothing_times = 0
        self.moved_to_target = True
        op = SimUniMoveToEnemyByMiniMap(self.ctx, no_attack=True, stop_after_arrival=True)
        return Operation.round_by_op(op.execute())

    def _enter_fight(self) -> OperationOneRoundResult:
        """
        移动到精英怪旁边之后 发起攻击
        :return:
        """
        op = SimUniFightElite(self.ctx)
        return Operation.round_by_op(op.execute())

    def _detect_reward(self) -> OperationOneRoundResult:
        if self.had_reward:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_NO_NEED_REWARD)

        # 调试时候强制走到沉浸奖励
        if not self.ctx.one_dragon_config.is_debug and self.max_reward_to_get == 0:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_NO_NEED_REWARD)

        self._view_down()
        screen = self.screenshot()

        self.ctx.init_yolo()
        detect_results: List[DetectResult] = self.ctx.yolo.detect(screen)

        detected: bool = False
        for result in detect_results:
            if result.detect_class.class_cate == '模拟宇宙沉浸奖励':
                detected = True
                break

        if detected:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_WITH_DETECT_REWARD)
        else:
            if self.ctx.one_dragon_config.is_debug:
                self.save_screenshot()
                cv2_utils.show_image(draw_detections(screen, detect_results), win_name='SimUniRunEliteRouteV2')

            if self.had_fight and self.nothing_times <= 11:  # 战斗后 一定要找到沉浸奖励
                return Operation.round_success(SimUniRunRouteBase.STATUS_NO_DETECT_REWARD)
            else:  # 重进的情况(没有战斗) 或者 找不到沉浸奖励太多次了 就不找了
                return Operation.round_success(SimUniRunRouteBase.STATUS_NO_NEED_REWARD)

    def _move_to_reward(self) -> OperationOneRoundResult:
        """
        朝沉浸装置移动
        :return:
        """
        self.nothing_times = 0
        self.moved_to_target = True
        op = SimUniMoveToInteractByDetect(self.ctx,
                                          interact_class='模拟宇宙沉浸奖励',
                                          interact_word='沉浸奖励',
                                          interact_during_move=True)
        return Operation.round_by_op(op.execute())

    def _get_reward(self) -> OperationOneRoundResult:
        """
        领取沉浸奖励
        :return:
        """
        self.had_reward = True
        op = SimUniReward(self.ctx, self.max_reward_to_get, self.get_reward_callback)
        return Operation.round_by_op(op.execute())

    def _boss_exit(self) -> OperationOneRoundResult:
        """
        战胜首领后退出
        :return: 
        """
        op = SimUniExit(self.ctx)
        return Operation.round_by_op(op.execute())


class SimUniRunEventRouteV2(SimUniRunRouteBase):

    def __init__(self, ctx: Context, level_type: SimUniLevelType = SimUniLevelTypeEnum.ELITE.value):
        """
        区域-事件
        1. 识别小地图上是否有事件图标 有的话就移动
        2. 小地图没有事件图标时 识别画面上是否有事件牌 有的话移动
        3. 交互
        4. 进入下一层
        :param ctx:
        """
        edges: List[StateOperationEdge] = []

        before_route = StateOperationNode('区域开始前', self._before_route)

        # 小地图有事件的话就走小地图
        check_mm = StateOperationNode('识别小地图事件', self._check_mm_icon)
        edges.append(StateOperationEdge(before_route, check_mm))
        move_by_mm = StateOperationNode('按小地图朝事件移动', self._move_by_mm)
        edges.append(StateOperationEdge(check_mm, move_by_mm, status=SimUniRunRouteBase.STATUS_WITH_MM_EVENT))

        # 小地图没有事件的话就靠识别
        detect_screen = StateOperationNode('识别画面事件', self._detect_screen)
        edges.append(StateOperationEdge(check_mm, detect_screen, status=SimUniRunRouteBase.STATUS_NO_MM_EVENT))
        # 识别到就移动
        move_by_detect = StateOperationNode('按画面朝事件移动', self._move_by_detect)
        edges.append(StateOperationEdge(detect_screen, move_by_detect, status=SimUniRunRouteBase.STATUS_WITH_DETECT_EVENT))

        # 走到了就进行交互 进入这里代码已经识别到事件了 则必须要交互才能进入下一层
        interact = StateOperationNode('交互', self._interact)
        edges.append(StateOperationEdge(move_by_mm, interact))
        edges.append(StateOperationEdge(move_by_detect, interact, status=SimUniMoveToInteractByDetect.STATUS_ARRIVAL))

        # 交互了之后开始事件判断
        event = StateOperationNode('事件', self._handle_event)
        edges.append(StateOperationEdge(interact, event))
        edges.append(StateOperationEdge(move_by_detect, event, status=SimUniMoveToInteractByDetect.STATUS_INTERACT))

        # 事件之后 识别下层入口
        check_entry = StateOperationNode('识别下层入口', self._check_next_entry)
        edges.append(StateOperationEdge(event, check_entry))
        # 识别不到事件 也识别下层入口
        edges.append(StateOperationEdge(detect_screen, check_entry, status=SimUniRunRouteBase.STATUS_NO_DETECT_EVENT))
        # 之前已经处理过事件了 识别下层人口
        edges.append(StateOperationEdge(check_mm, check_entry, status=SimUniRunRouteBase.STATUS_HAD_EVENT))
        edges.append(StateOperationEdge(detect_screen, check_entry, status=SimUniRunRouteBase.STATUS_HAD_EVENT))
        # 找到了下层入口就开始移动
        move_to_next = StateOperationNode('向下层移动', self._move_to_next)
        edges.append(StateOperationEdge(check_entry, move_to_next, status=SimUniRunRouteBase.STATUS_WITH_ENTRY))
        # 找不到下层入口就转向找目标 重新开始
        turn = StateOperationNode('转动找目标', self._turn_when_nothing)
        edges.append(StateOperationEdge(check_entry, turn, status=SimUniRunRouteBase.STATUS_NO_ENTRY))
        edges.append(StateOperationEdge(turn, check_mm))

        super().__init__(ctx, level_type=level_type,
                         edges=edges,
                         specified_start_node=before_route
                         )

        self.mm_icon_pos: Optional[Point] = None  # 小地图上事件的坐标
        self.event_handled: bool = False  # 已经处理过事件了

    def _check_mm_icon(self) -> OperationOneRoundResult:
        """
        识别小地图上的事件图标
        :return:
        """
        if self.event_handled:  # 已经交互过事件了
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_HAD_EVENT)

        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        mm_info: MiniMapInfo = mini_map.analyse_mini_map(mm)
        mrl = self.ctx.im.match_template(mm_info.origin_del_radio, template_id='mm_sp_event', template_sub_dir='sim_uni')
        if mrl.max is not None:
            self.mm_icon_pos = mrl.max.center
            if self.ctx.one_dragon_config.is_debug:  # 按小地图图标已经成熟 调试时强制使用yolo
                return Operation.round_success(status=SimUniRunRouteBase.STATUS_NO_MM_EVENT)
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_WITH_MM_EVENT)
        else:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_NO_MM_EVENT)

    def _move_by_mm(self) -> OperationOneRoundResult:
        """
        按小地图的图标位置机械移动
        :return:
        """
        self.nothing_times = 0
        self.moved_to_target = True
        op = MoveWithoutPos(self.ctx, start=self.ctx.game_config.mini_map_pos.mm_center, target=self.mm_icon_pos)
        return Operation.round_by_op(op.execute())

    def _detect_screen(self) -> OperationOneRoundResult:
        """
        识别游戏画面上是否有事件牌
        :return:
        """
        if self.event_handled:  # 已经交互过事件了
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_HAD_EVENT)
        self._view_down()
        screen = self.screenshot()

        self.ctx.init_yolo()
        detect_results: List[DetectResult] = self.ctx.yolo.detect(screen)

        with_event: bool = False
        for result in detect_results:
            if result.detect_class.class_cate == '模拟宇宙事件':
                with_event = True
                break

        if with_event:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_WITH_DETECT_EVENT)
        else:
            if self.ctx.one_dragon_config.is_debug:
                self.save_screenshot()
                cv2_utils.show_image(draw_detections(screen, detect_results), win_name='event_detect_screen')
            return Operation.round_success(SimUniRunRouteBase.STATUS_NO_DETECT_EVENT)

    def _move_by_detect(self) -> OperationOneRoundResult:
        """
        根据画面识别结果走向事件
        :return:
        """
        self.nothing_times = 0
        self.moved_to_target = True
        op = SimUniMoveToInteractByDetect(self.ctx,
                                          interact_class='模拟宇宙事件',
                                          interact_word='事件',
                                          interact_during_move=True)
        return Operation.round_by_op(op.execute())

    def _interact(self) -> OperationOneRoundResult:
        """
        尝试交互
        :return:
        """
        op = Interact(self.ctx, '事件', lcs_percent=0.1, single_line=True)
        return Operation.round_by_op(op.execute())

    def _handle_event(self) -> OperationOneRoundResult:
        """
        事件处理
        :return:
        """
        self.event_handled = True
        op = SimUniEvent(self.ctx, skip_first_screen_check=False)
        return Operation.round_by_op(op.execute())


class SimUniRunRespiteRouteV2(SimUniRunRouteBase):

    def __init__(self, ctx: Context, level_type: SimUniLevelType = SimUniLevelTypeEnum.ELITE.value):
        edges: List[StateOperationEdge] = []

        before_route = StateOperationNode('区域开始前', self._before_route)

        # 小地图有事件的话就走小地图
        check_mm = StateOperationNode('识别小地图黑塔', self._check_mm_icon)
        edges.append(StateOperationEdge(before_route, check_mm))
        move_by_mm = StateOperationNode('按小地图朝黑塔移动', self._move_by_mm)
        edges.append(StateOperationEdge(check_mm, move_by_mm, status=SimUniRunRouteBase.STATUS_WITH_MM_EVENT))

        # 小地图没有事件的话就靠识别
        detect_screen = StateOperationNode('识别画面黑塔', self._detect_screen)
        edges.append(StateOperationEdge(check_mm, detect_screen, status=SimUniRunRouteBase.STATUS_NO_MM_EVENT))
        # 识别到就移动
        move_by_detect = StateOperationNode('按画面朝黑塔移动', self._move_by_detect)
        edges.append(StateOperationEdge(detect_screen, move_by_detect, status=SimUniRunRouteBase.STATUS_WITH_DETECT_EVENT))

        # 走到了就进行交互
        interact = StateOperationNode('交互', self._interact)
        edges.append(StateOperationEdge(move_by_mm, interact))
        edges.append(StateOperationEdge(move_by_detect, interact, status=SimUniMoveToInteractByDetect.STATUS_ARRIVAL))

        # 交互了之后开始事件判断
        event = StateOperationNode('黑塔', self._handle_event)
        edges.append(StateOperationEdge(interact, event))

        # 事件之后 识别下层入口
        check_entry = StateOperationNode('识别下层入口', self._check_next_entry)
        edges.append(StateOperationEdge(event, check_entry))
        # 识别不到事件、交互失败 也识别下层入口
        edges.append(StateOperationEdge(detect_screen, check_entry, status=SimUniRunRouteBase.STATUS_NO_DETECT_EVENT))
        edges.append(StateOperationEdge(interact, check_entry, success=False))
        # 之前已经处理过事件了 识别下层人口
        edges.append(StateOperationEdge(check_mm, check_entry, status=SimUniRunRouteBase.STATUS_HAD_EVENT))
        edges.append(StateOperationEdge(detect_screen, check_entry, status=SimUniRunRouteBase.STATUS_HAD_EVENT))
        # 找到了下层入口就开始移动
        move_to_next = StateOperationNode('向下层移动', self._move_to_next)
        edges.append(StateOperationEdge(check_entry, move_to_next, status=SimUniRunRouteBase.STATUS_WITH_ENTRY))
        # 找不到下层入口就转向找目标 重新开始
        turn = StateOperationNode('转动找目标', self._turn_when_nothing)
        edges.append(StateOperationEdge(check_entry, turn, status=SimUniRunRouteBase.STATUS_NO_ENTRY))
        edges.append(StateOperationEdge(turn, check_mm))

        super().__init__(ctx, level_type=level_type,
                         edges=edges,
                         specified_start_node=before_route
                         )

        self.mm_icon_pos: Optional[Point] = None  # 小地图上黑塔的坐标
        self.event_handled: bool = False  # 已经处理过事件了

    def _check_mm_icon(self) -> OperationOneRoundResult:
        """
        识别小地图上的黑塔图标
        :return:
        """
        if self.event_handled:  # 已经交互过事件了
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_HAD_EVENT)
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        mm_info: MiniMapInfo = mini_map.analyse_mini_map(mm)
        mrl = self.ctx.im.match_template(mm_info.origin_del_radio, template_id='mm_sp_herta', template_sub_dir='sim_uni')
        if mrl.max is not None:
            self.mm_icon_pos = mrl.max.center
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_WITH_MM_EVENT)
        else:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_NO_MM_EVENT)

    def _move_by_mm(self) -> OperationOneRoundResult:
        """
        按小地图的图标位置机械移动
        :return:
        """
        self.nothing_times = 0
        self.moved_to_target = True
        op = MoveWithoutPos(self.ctx, start=self.ctx.game_config.mini_map_pos.mm_center, target=self.mm_icon_pos)
        return Operation.round_by_op(op.execute())

    def _detect_screen(self) -> OperationOneRoundResult:
        """
        识别游戏画面上是否有事件牌
        :return:
        """
        if self.event_handled:  # 已经交互过事件了
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_HAD_EVENT)
        self._view_down()
        screen = self.screenshot()

        self.ctx.init_yolo()
        detect_results: List[DetectResult] = self.ctx.yolo.detect(screen)

        with_event: bool = False
        for result in detect_results:
            if result.detect_class.class_cate == '模拟宇宙黑塔':
                with_event = True
                break

        if with_event:
            return Operation.round_success(status=SimUniRunRouteBase.STATUS_WITH_DETECT_EVENT)
        else:
            if self.ctx.one_dragon_config.is_debug:
                self.save_screenshot()
                cv2_utils.show_image(draw_detections(screen, detect_results), win_name='respite_detect_screen')
            return Operation.round_success(SimUniRunRouteBase.STATUS_NO_DETECT_EVENT)

    def _move_by_detect(self) -> OperationOneRoundResult:
        """
        根据画面识别结果走向事件
        :return:
        """
        self.nothing_times = 0
        self.moved_to_target = True
        op = SimUniMoveToInteractByDetect(self.ctx,
                                          interact_class='模拟宇宙黑塔',
                                          interact_word='黑塔',
                                          interact_during_move=False)
        return Operation.round_by_op(op.execute())

    def _interact(self) -> OperationOneRoundResult:
        """
        尝试交互
        :return:
        """
        op = Interact(self.ctx, '黑塔', lcs_percent=0.1, single_line=True)
        return Operation.round_by_op(op.execute())

    def _handle_event(self) -> OperationOneRoundResult:
        """
        事件处理
        :return:
        """
        self.event_handled = True
        op = SimUniEvent(self.ctx, skip_first_screen_check=False)
        return Operation.round_by_op(op.execute())
