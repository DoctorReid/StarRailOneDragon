from typing import Optional, Callable, ClassVar, List

from basic.i18_utils import gt
from sr.const.character_const import Character
from sr.context.context import Context
from sr.operation import OperationResult, StateOperation, OperationOneRoundResult, \
    StateOperationNode, StateOperationEdge
from sr.screen_area.screen_sim_uni import ScreenSimUni
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sr.sim_uni.op.sim_uni_exit import SimUniExit
from sr.sim_uni.op.sim_uni_run_level import SimUniRunLevel
from sr.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig
from sr.sim_uni.sim_uni_const import UNI_NUM_CN


class SimUniRunWorld(StateOperation):

    STATUS_SUCCESS: ClassVar[str] = '通关'

    def __init__(self, ctx: Context, world_num: int,
                 config: Optional[SimUniChallengeConfig] = None,
                 max_reward_to_get: int = 0,
                 get_reward_callback: Optional[Callable[[int, int], None]] = None,
                 op_callback: Optional[Callable[[OperationResult], None]] = None):
        """
        模拟宇宙 完成整个宇宙
        最后退出
        """
        op_name = '%s %s' % (
            gt('模拟宇宙', 'ui'),
            gt('第%s世界' % UNI_NUM_CN[world_num], 'ui')
        )


        super().__init__(ctx, op_name=op_name, op_callback=op_callback)

        self.world_num: int = world_num
        self.config: Optional[SimUniChallengeConfig] = config
        self.max_reward_to_get: int = max_reward_to_get  # 最多获取多少次奖励
        self.get_reward_callback: Optional[Callable[[int, int], None]] = get_reward_callback  # 获取奖励后的回调

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        # 逐层挑战
        run_level = StateOperationNode('挑战楼层', self._run_level)
        self.add_edge(run_level, run_level, ignore_status=True)

        # 通关后退出
        finished = StateOperationNode('结束', self._finish)
        self.add_edge(run_level, finished, status=SimUniRunLevel.STATUS_BOSS_CLEARED)

        # 失败后退出宇宙 继续下一次
        exit_world = StateOperationNode('退出宇宙', self._exit)
        self.add_edge(run_level, exit_world, success=False)

        # 战斗失败的情况 需要点击结算
        battle_fail_exit = StateOperationNode('战斗失败结算', self.battle_fail_exit)
        self.add_edge(run_level, battle_fail_exit, success=False, status=SimUniEnterFight.STATUS_BATTLE_FAIL)

        battle_fail_exit_confirm = StateOperationNode('战斗失败结算确认', self.battle_fail_exit_confirm, wait_after_op=5)
        self.add_edge(battle_fail_exit, battle_fail_exit_confirm)

        click_empty = StateOperationNode('战斗失败结算点击空白', self.click_empty)
        self.add_edge(battle_fail_exit_confirm, click_empty)

        self.param_start_node = run_level

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        self.get_reward_cnt = 0
        self.ctx.no_technique_recover_consumables = False  # 模拟宇宙重新开始时重置
        self.last_members: List[Character] = []  # 上一次识别的配队
        self.skip_check_members: bool = False  # 是否可跳过配队检测 当连续两次检测配队都一样之后 就可以跳过了

        return None

    def _run_level(self) -> OperationOneRoundResult:
        if self.ctx.team_info.same_as_current(self.last_members):
            self.skip_check_members = True
        op = SimUniRunLevel(self.ctx, self.world_num, config=self.config,
                            max_reward_to_get=self.max_reward_to_get - self.get_reward_cnt,
                            get_reward_callback=self._on_get_reward,
                            skip_check_members=self.skip_check_members)
        op_result = op.execute()
        self.last_members = self.ctx.team_info.character_list  # 每次运行后 保存上一次识别的结果
        return self.round_by_op(op_result)

    def _finish(self) -> OperationOneRoundResult:
        return self.round_success(status=SimUniRunWorld.STATUS_SUCCESS)

    def _exit(self) -> OperationOneRoundResult:
        if self.ctx.one_dragon_config.is_debug:  # 调试情况下 原地失败即可
            return self.round_fail()
        else:
            op = SimUniExit(self.ctx)
            return self.round_by_op(op.execute())

    def _on_get_reward(self, use_power: int, user_qty: int):
        """
        获取奖励后的回调
        :return:
        """
        self.get_reward_cnt += 1
        if self.get_reward_callback is not None:
            self.get_reward_callback(use_power, user_qty)

    def battle_fail_exit(self) -> OperationOneRoundResult:
        """
        战斗失败后 点击结算
        :return:
        """
        screen = self.screenshot()
        area = ScreenSimUni.BATTLE_FAIL_EXIT.value

        return self.round_by_find_and_click_area(screen, area, success_wait_round=1, retry_wait_round=1)

    def battle_fail_exit_confirm(self) -> OperationOneRoundResult:
        """
        战斗失败后 点击结算后 确认
        :return:
        """
        screen = self.screenshot()
        area = ScreenSimUni.BATTLE_FAIL_EXIT_CONFIRM.value

        return self.round_by_find_and_click_area(screen, area, success_wait_round=1, retry_wait_round=1)

    def click_empty(self) -> OperationOneRoundResult:
        """
        结算画面点击空白
        :return:
        """
        screen = self.screenshot()
        area = ScreenSimUni.EXIT_EMPTY_TO_CONTINUE.value

        return self.round_by_find_and_click_area(screen, area, success_wait_round=1, retry_wait_round=1)
