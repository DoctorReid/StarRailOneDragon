from typing import List, Optional, Callable, ClassVar

from basic.i18_utils import gt
from sr.app.sim_uni.sim_uni_route_holder import match_best_sim_uni_route
from sr.context import Context
from sr.image.sceenshot import mini_map
from sr.operation import Operation, OperationResult, StateOperation, StateOperationEdge, \
    StateOperationNode, OperationOneRoundResult
from sr.operation.unit.move import MoveDirectly
from sr.operation.unit.team import CheckTeamMembersInWorld, SwitchMember
from sr.sim_uni import sim_uni_screen_state
from sr.sim_uni.op.move_in_sim_uni import MoveToNextLevel
from sr.sim_uni.op.reset_sim_uni_level import ResetSimUniLevel
from sr.sim_uni.op.sim_uni_run_route import SimUniRunCombatRoute
from sr.sim_uni.op.sim_uni_wait import SimUniWaitLevelStart
from sr.sim_uni.op.v2.sim_uni_run_combat_route_v2 import SimUniRunCombatRouteV2
from sr.sim_uni.op.v2.sim_uni_run_elite_route_v2 import SimUniRunEliteRouteV2
from sr.sim_uni.op.v2.sim_uni_run_event_route_v2 import SimUniRunEventRouteV2
from sr.sim_uni.op.v2.sim_uni_run_respite_route_v2 import SimUniRunRespiteRouteV2
from sr.sim_uni.op.v2.sim_uni_run_route_base_v2 import SimUniRunRouteBaseV2
from sr.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig
from sr.sim_uni.sim_uni_const import UNI_NUM_CN, SimUniLevelType, SimUniLevelTypeEnum
from sr.sim_uni.sim_uni_route import SimUniRoute


class SimUniRunLevel(StateOperation):

    STATUS_BOSS_CLEARED: ClassVar[str] = '首领通关'
    STATUS_NO_RESET: ClassVar[str] = '失败到达重置上限'

    def __init__(self, ctx: Context, world_num: int,
                 config: Optional[SimUniChallengeConfig] = None,
                 max_reward_to_get: int = 0,
                 get_reward_callback: Optional[Callable[[int, int], None]] = None,
                 op_callback: Optional[Callable[[OperationResult], None]] = None,
                 skip_check_members: bool = False):
        """
        模拟宇宙中 识别楼层类型并运行
        完整通过整个楼层 进入下个楼层或通关后退出
        异常情况交由外层处理
        - 战斗失败
        """
        op_name = '%s %s %s' % (
            gt('模拟宇宙', 'ui'),
            gt('第%s世界' % UNI_NUM_CN[world_num], 'ui'),
            gt('挑战楼层', 'ui')
        )

        edges: List[StateOperationEdge] = []

        wait_start = StateOperationNode('等待加载', self._wait)

        check_members = StateOperationNode('识别组队成员', self._check_members)
        edges.append(StateOperationEdge(wait_start, check_members))

        switch = StateOperationNode('切换1号位', self._switch_first)
        edges.append(StateOperationEdge(check_members, switch))

        check_level_type = StateOperationNode('识别楼层类型', self._check_level_type)
        edges.append(StateOperationEdge(switch, check_level_type, ignore_status=True))  # 1号位切换成功与否都可以继续

        check_route = StateOperationNode('匹配路线', self._check_route)
        edges.append(StateOperationEdge(check_level_type, check_route))

        route = StateOperationNode('区域', self._route_op)
        edges.append(StateOperationEdge(check_route, route, ignore_status=True))
        edges.append(StateOperationEdge(check_route, route, success=False, ignore_status=True))  # 没有设置路线也尝试使用v2算法

        # 部分v1的失败情况 可以使用v2兜底
        route_v2 = StateOperationNode('区域v2', self._route_op_v2)
        edges.append(StateOperationEdge(route, route_v2, success=False, status=MoveDirectly.STATUS_NO_POS))

        # 有可能是楼层类型判断错了
        edges.append(StateOperationEdge(route, check_level_type, success=False, status=SimUniRunRouteBaseV2.STATUS_WRONG_LEVEL_TYPE))
        edges.append(StateOperationEdge(route_v2, check_level_type, success=False, status=SimUniRunRouteBaseV2.STATUS_WRONG_LEVEL_TYPE))

        # 最终还是失败时 部分场景可以尝试重置
        reset = StateOperationNode('重置', self._reset)
        edges.append(StateOperationEdge(route, reset, success=False, status=MoveToNextLevel.STATUS_ENTRY_NOT_FOUND))
        edges.append(StateOperationEdge(route_v2, reset, success=False, status=MoveToNextLevel.STATUS_ENTRY_NOT_FOUND))
        # 之前失败有可能是类型或者路线匹配错了 重进的话完全重新来一遍
        edges.append(StateOperationEdge(reset, check_level_type))

        super().__init__(ctx, op_name=op_name, edges=edges, specified_start_node=wait_start, op_callback=op_callback)

        self.world_num: int = world_num
        self.level_type: Optional[SimUniLevelType] = None
        self.route: Optional[SimUniRoute] = None
        self.config: Optional[SimUniChallengeConfig] = config
        self.max_reward_to_get: int = max_reward_to_get  # 最多获取多少次奖励
        self.get_reward_callback: Optional[Callable[[int, int], None]] = get_reward_callback  # 获取奖励后的回调
        self.reset_times: int = 0  # 重置次数
        self.skip_check_members: bool = skip_check_members  # 是否跳过配队检测

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self.level_type = None
        self.route = None
        self.reset_times = 0

    def _wait(self) -> OperationOneRoundResult:
        op = SimUniWaitLevelStart(self.ctx, config=self.config)
        return self.round_by_op(op.execute())

    def _check_members(self) -> OperationOneRoundResult:
        if self.skip_check_members:
            return self.round_success('跳过')
        op = CheckTeamMembersInWorld(self.ctx)
        return self.round_by_op(op.execute())

    def _switch_first(self) -> OperationOneRoundResult:
        """
        切换1号位
        :return:
        """
        op = SwitchMember(self.ctx, 1)
        return self.round_by_op(op.execute())

    def _check_level_type(self) -> OperationOneRoundResult:
        """
        识别楼层类型
        防止识别错误 两次识别一样时才认为是正确 牺牲一点时间换取稳定性
        :return:
        """
        screen = self.screenshot()

        level_type = sim_uni_screen_state.get_level_type(screen, self.ctx.ocr)

        if level_type is None:
            self.level_type = None
            return self.round_retry('匹配楼层类型失败', wait=1)

        another_type = False  # 是否匹配到另一钟类型
        if self.level_type is None or self.level_type != level_type:
            self.level_type = level_type
            another_type = True

        # OCR运行需要时间 下面这些就不等待了
        if another_type:
            return self.round_wait()
        else:
            return self.round_success()

    def _check_route(self) -> OperationOneRoundResult:
        """
        根据小地图匹配路线
        防止匹配错误 两次匹配一样时才认为是正确 牺牲一点时间换取稳定性
        :return:
        """
        # 只有3~8宇宙的战斗楼层需要
        if (self.world_num > 8
                or self.level_type != SimUniLevelTypeEnum.COMBAT.value):
            return self.round_success()

        screen = self.screenshot()

        another_route = False  # 是否匹配到另一条路线
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        target_route = match_best_sim_uni_route(self.world_num, self.level_type, mm)

        if target_route is None:
            self.route = None
            return self.round_retry('匹配路线失败', wait=1)
        elif self.route is None or self.route.uid != target_route.uid:
            self.route = target_route
            another_route = True

        if another_route:
            return self.round_wait(wait=0.2)
        else:
            return self.round_success()

    def _route_op(self, only_v2: bool = False) -> OperationOneRoundResult:
        """
        获取路线指令
        :return:
        """
        op: Operation = self._get_route_op(only_v2=only_v2)

        if op is None:
            return self.round_fail(status='未支持的楼层类型 %s' % self.level_type)

        op_result = op.execute()
        if op_result.success and self.level_type == SimUniLevelTypeEnum.BOSS.value:
            return self.round_success(status=SimUniRunLevel.STATUS_BOSS_CLEARED)
        else:
            return self.round_by_op(op_result)

    def _route_op_v2(self) -> OperationOneRoundResult:
        """
        获取路线指令
        :return:
        """
        return self._route_op(only_v2=True)

    def _get_route_op(self, only_v2: bool = False) -> Optional[Operation]:
        """
        1. 匹配路线失败时 使用v2算法
        2. 根据匹配路线中的配置 选择使用的算法
        :return:
        """
        if self.level_type == SimUniLevelTypeEnum.COMBAT.value:
            if self.route is None or self.route.algo == 2 or only_v2:
                return SimUniRunCombatRouteV2(self.ctx, self.level_type)
            else:
                return SimUniRunCombatRoute(self.ctx, self.world_num, self.level_type, self.route, config=self.config)
        elif self.level_type == SimUniLevelTypeEnum.EVENT.value or \
                self.level_type == SimUniLevelTypeEnum.TRANSACTION.value or \
                self.level_type == SimUniLevelTypeEnum.ENCOUNTER.value:
            return SimUniRunEventRouteV2(self.ctx, self.level_type)
        elif self.level_type == SimUniLevelTypeEnum.RESPITE.value:
            return SimUniRunRespiteRouteV2(self.ctx, self.level_type)
        elif self.level_type == SimUniLevelTypeEnum.ELITE.value or \
                self.level_type == SimUniLevelTypeEnum.BOSS.value:
            return SimUniRunEliteRouteV2(self.ctx, self.level_type,
                                         max_reward_to_get=self.max_reward_to_get,
                                         get_reward_callback=self.get_reward_callback)
        else:
            return None

    def _reset(self) -> OperationOneRoundResult:
        """
        重置再来
        :return:
        """
        if self.reset_times >= 1:  # 最多重置1次
            return self.round_fail(SimUniRunLevel.STATUS_NO_RESET)

        self.reset_times += 1
        op = ResetSimUniLevel(self.ctx)
        return self.round_by_op(op.execute())
