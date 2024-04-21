from typing import List, ClassVar

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot import mini_map, screen_state, MiniMapInfo
from sr.operation import StateOperation, StateOperationEdge, StateOperationNode, OperationOneRoundResult, Operation
from sr.sim_uni.op.move_in_sim_uni import MoveToNextLevel
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sr.sim_uni.op.v2.sim_uni_move_v2 import SimUniMoveToEnemyByMiniMap, SimUniMoveToEnemyByDetect
from sr.sim_uni.sim_uni_const import SimUniLevelTypeEnum
from sryolo.detector import DetectResult


class SimUniRunCombatRouteV2(StateOperation):

    STATUS_WITH_RED: ClassVar[str] = '小地图无红点'
    STATUS_NO_RED: ClassVar[str] = '小地图无红点'
    STATUS_WITH_ENEMY: ClassVar[str] = '识别到敌人'
    STATUS_NO_ENEMY: ClassVar[str] = '识别不到敌人'
    STATUS_WITH_ENTRY: ClassVar[str] = '识别到下层入口'
    STATUS_NO_ENTRY: ClassVar[str] = '识别不到下层入口'
    STATUS_NOTHING: ClassVar[str] = '识别不到任何内容'

    def __init__(self, ctx: Context):
        """
        1. 检测地图是否有红点
        2. 如果有红点 移动到最近的红点 并进行攻击。攻击一次后回到步骤1判断。
        3. 如果没有红点 识别敌对物种位置，向最大的移动，并进行攻击。攻击一次后回到步骤1判断。
        4. 如果没有红点也没有识别到敌对物种，检测下层入口位置，发现后进入下层移动。未发现则选择视角返回步骤1判断。
        """
        edges: List[StateOperationEdge] = []

        check = StateOperationNode('画面检测', self._check_screen)
        move_by_red = StateOperationNode('小地图向红点移动', self._move_by_red)
        edges.append(StateOperationEdge(check, move_by_red, status=SimUniRunCombatRouteV2.STATUS_WITH_RED))

        fight = StateOperationNode('进入战斗', self._enter_fight)
        # 到达红点
        edges.append(StateOperationEdge(move_by_red, fight, status=SimUniMoveToEnemyByMiniMap.STATUS_ARRIVAL))
        # 进行了战斗 就重新开始
        edges.append(StateOperationEdge(fight, check))
        edges.append(StateOperationEdge(move_by_red, check, status=SimUniMoveToEnemyByMiniMap.STATUS_FIGHT))

        # 小地图没有红点 就在画面上找敌人
        detect_enemy = StateOperationNode('识别敌人', self._detect_enemy_in_screen)
        edges.append(StateOperationEdge(check, detect_enemy, status=SimUniRunCombatRouteV2.STATUS_NO_RED))
        # 找到了敌人就开始移动
        move_by_detect = StateOperationNode('向敌人移动', self._move_by_detect)
        edges.append(StateOperationEdge(detect_enemy, move_by_detect, status=SimUniRunCombatRouteV2.STATUS_WITH_ENEMY))
        # 进入了战斗 就重新开始
        edges.append(StateOperationEdge(move_by_detect, check, status=SimUniMoveToEnemyByDetect.STATUS_FIGHT))

        # 画面上也找不到敌人 就找下层入口
        check_entry = StateOperationNode('识别下层入口', self._check_next_entry)
        edges.append(StateOperationEdge(detect_enemy, check_entry, status=SimUniRunCombatRouteV2.STATUS_NO_ENEMY))
        # 找到了下层入口就开始移动
        move_to_next = StateOperationNode('向下层移动', self._move_to_next)
        edges.append(StateOperationEdge(check_entry, move_to_next, status=SimUniRunCombatRouteV2.STATUS_WITH_ENTRY))
        # 找不到下层入口就转向找目标
        turn = StateOperationNode('转动找目标', self._turn_when_nothing)
        edges.append(StateOperationEdge(check_entry, turn, status=SimUniRunCombatRouteV2.STATUS_NO_ENTRY))
        # 转动完重新开始目标识别
        edges.append(StateOperationEdge(turn, check))

        super().__init__(ctx,
                         op_name=gt('区域-战斗', 'ui'),
                         edges=edges)

        self.last_state: str = ''  # 上一次的画面状态
        self.current_state: str = ''  # 这一次的画面状态
        self.nothing_times: int = 0  # 识别不到任何内容的次数

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
        mm_info: MiniMapInfo = mini_map.analyse_mini_map(mm, self.ctx.im)

        if mini_map.is_under_attack_new(mm_info):
            op = SimUniEnterFight(self.ctx)
            return Operation.round_wait_by_op(op.execute())

        pos_list = mini_map.get_enemy_pos(mm_info.origin_del_radio)

        if len(pos_list) == 0:
            return Operation.round_success(SimUniRunCombatRouteV2.STATUS_NO_RED)
        else:
            return Operation.round_success(SimUniRunCombatRouteV2.STATUS_WITH_RED)

    def _move_by_red(self) -> OperationOneRoundResult:
        """
        朝小地图红点走去
        :return:
        """
        self.nothing_times = 0
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
        return Operation.round_wait_by_op(op.execute())

    def _move_to_next(self):
        """
        朝下层移动
        :return:
        """
        op = MoveToNextLevel(self.ctx, level_type=SimUniLevelTypeEnum.COMBAT.value)
        return Operation.round_by_op(op.execute())

    def _detect_enemy_in_screen(self, screen: MatLike) -> OperationOneRoundResult:
        """
        没有红点时 判断当前画面是否有怪
        TODO 之后可以把入口识别也放到这里
        :param screen: 游戏画面截图
        :return:
        """
        self.ctx.init_yolo()

        detect_results: List[DetectResult] = self.ctx.yolo.detect(screen)

        with_enemy: bool = False
        for result in detect_results:
            if result.detect_class.class_cate == '普通怪':
                with_enemy = True
                break

        if with_enemy:
            return Operation.round_success(SimUniRunCombatRouteV2.STATUS_WITH_ENEMY)
        else:
            return Operation.round_success(SimUniRunCombatRouteV2.STATUS_NO_ENEMY)

    def _move_by_detect(self) -> OperationOneRoundResult:
        """
        识别到敌人人开始移动
        :return:
        """
        self.nothing_times = 0
        op = SimUniMoveToEnemyByDetect(self.ctx)
        return Operation.round_by_op(op.execute())

    def _check_next_entry(self) -> OperationOneRoundResult:
        """
        找下层入口 主要判断能不能找到
        :return:
        """
        screen: MatLike = self.screenshot()
        entry_list = MoveToNextLevel.get_next_level_type(screen, self.ctx.ih)
        if len(entry_list) == 0:
            return Operation.round_success(SimUniRunCombatRouteV2.STATUS_NO_ENTRY)
        else:
            self.nothing_times = 0
            return Operation.round_success(SimUniRunCombatRouteV2.STATUS_WITH_ENTRY)

    def _turn_when_nothing(self) -> OperationOneRoundResult:
        """
        当前画面识别不到任何内容时候 转动一下
        :return:
        """
        self.nothing_times += 1
        if self.nothing_times >= 10:
            return Operation.round_fail(SimUniRunCombatRouteV2.STATUS_NOTHING)

        angle = (25 + 10 * self.nothing_times) * (1 if self.nothing_times % 2 == 0 else -1)  # 来回转动视角
        self.ctx.controller.turn_by_angle(angle)
        return Operation.round_success()