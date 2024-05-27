import time
from typing import ClassVar, Optional, List, Callable

from cv2.typing import MatLike

from basic.i18_utils import gt
from sr.const import STANDARD_RESOLUTION_W
from sr.context import Context
from sr.image.sceenshot import mini_map
from sr.operation import StateOperation, StateOperationNode, StateOperationEdge, OperationResult, \
    OperationOneRoundResult, Operation
from sr.screen_area.screen_normal_world import ScreenNormalWorld
from sr.sim_uni import sim_uni_screen_state
from sr.sim_uni.op.move_in_sim_uni import MoveToNextLevel
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sr.sim_uni.op.v2.sim_uni_move_v2 import MoveToNextLevelV2
from sr.sim_uni.sim_uni_const import SimUniLevelType, SimUniLevelTypeEnum


class SimUniRunRouteBaseV2(StateOperation):

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
    STATUS_WRONG_LEVEL_TYPE: ClassVar[str] = '楼层识别错误'

    def __init__(self, ctx: Context, level_type: SimUniLevelType,
                 try_times: int = 2,
                 nodes: Optional[List[StateOperationNode]] = None,
                 edges: Optional[List[StateOperationEdge]] = None,
                 specified_start_node: Optional[StateOperationNode] = None,
                 timeout_seconds: float = -1,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        StateOperation.__init__(self,
                                ctx=ctx, try_times=try_times,
                                op_name=gt(f'区域-{level_type.type_name}-v2', 'ui'),
                                nodes=nodes, edges=edges, specified_start_node=specified_start_node,
                                timeout_seconds=timeout_seconds, op_callback=op_callback)

        self.level_type: SimUniLevelType = level_type  # 楼层类型
        self.moved_to_target: bool = False  # 是否已经产生了朝向目标的移动
        self.nothing_times: int = 0  # 识别不到任何内容的次数
        self.previous_angle: float = 0  # 之前的朝向 识别到目标时应该记录下来 后续可以在这个方向附近找下一个目标
        self.turn_direction_when_nothing: int = 1  # 没有目标时候的转动方向 正数向右 负数向左
        self.detect_move_timeout_times: int = 0  # 识别移动的超时失败次数

    def _init_before_execute(self):
        super()._init_before_execute()

    def _before_route(self) -> OperationOneRoundResult:
        """
        路线开始前
        1. 按照小地图识别初始的朝向
        :return:
        """
        screen = self.screenshot()
        self._check_angle(screen)
        return self.round_success()

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
        return self.round_success(wait=0.2)

    def _check_next_entry(self) -> OperationOneRoundResult:
        """
        找下层入口 主要判断能不能找到
        :return:
        """
        if self.level_type == SimUniLevelTypeEnum.BOSS.value:
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_BOSS_EXIT)
        self._view_up()
        screen: MatLike = self.screenshot()
        entry_list = MoveToNextLevel.get_next_level_type(screen, self.ctx.ih)
        if len(entry_list) == 0:
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_NO_ENTRY)
        else:
            self.nothing_times = 0
            return self.round_success(status=SimUniRunRouteBaseV2.STATUS_WITH_ENTRY)

    def _move_to_next(self):
        """
        朝下层移动
        :return:
        """
        self.nothing_times = 0
        self.moved_to_target = True

        self._view_up()
        op = MoveToNextLevelV2(self.ctx, level_type=self.level_type)
        return self.round_by_op(op.execute())

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
            return self.round_success()

        if self.nothing_times >= 23:
            return self.round_fail(SimUniRunRouteBaseV2.STATUS_NOTHING)

        # angle = (25 + 10 * self.nothing_times) * (1 if self.nothing_times % 2 == 0 else -1)  # 来回转动视角
        # 由于攻击之后 人物可能朝反方向了 因此要转动多一点
        # 不要被360整除 否则转一圈之后还是被人物覆盖了看不到
        angle = 35 * self.turn_direction_when_nothing
        self.ctx.controller.turn_by_angle(angle)
        time.sleep(0.5)

        if self.nothing_times % 11 == 0:
            # 大概转了一圈之后还没有找到东西 就往之前的方向走一点
            self.moved_to_target = False
            return self._turn_to_previous_angle()

        return self.round_success()

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

    def _after_detect_timeout(self) -> OperationOneRoundResult:
        """
        识别移动超时后的处理
        1. 可能被可破坏物卡住了
        2. 被路挡住了
        :return:
        """
        self.detect_move_timeout_times += 1
        if self.detect_move_timeout_times >= 4:
            return self.round_fail(status=Operation.STATUS_TIMEOUT)

        # 先尝试攻击破坏物
        op = SimUniEnterFight(self.ctx, disposable=True, first_state=ScreenNormalWorld.CHARACTER_ICON.value.status)
        op_result = op.execute()
        if not op_result.success:
            return self.round_by_op(op_result)

        # 看上一帧识别结果
        frame_result = self.ctx.sim_uni_yolo.last_detect_result
        min_x = STANDARD_RESOLUTION_W
        max_x = 0
        for r in frame_result.results:
            if r.x1 < min_x:
                min_x = r.x1
            if r.x2 > max_x:
                max_x = r.x2

        mid_x = STANDARD_RESOLUTION_W // 2
        if min_x >= mid_x:  # 都在右边
            to_right = True
        elif max_x <= mid_x:  # 都在左边
            to_right = False
        elif mid_x - min_x >= max_x - mid_x:  # 左边偏移更多
            to_right = False
        else:  # 右边偏移更多
            to_right = True

        if to_right:
            self.ctx.controller.move('d', 1)
        else:
            self.ctx.controller.move('a', 1)

        return self.round_success()

    def is_level_type_correct(self, screen: MatLike) -> bool:
        """
        当前识别的楼层类型是否正确
        :param screen: 游戏画面
        :return:
        """
        level_type = sim_uni_screen_state.get_level_type(screen, self.ctx.ocr)
        return level_type is not None and self.level_type.type_id == level_type.type_id
