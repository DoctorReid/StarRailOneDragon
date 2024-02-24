from typing import Optional, Callable, ClassVar

from basic import Rect
from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, StateOperation, OperationOneRoundResult, StateOperationNode, StateOperationEdge
from sr.operation.battle.choose_challenge_times import ChooseChallengeTimes
from sr.operation.battle.choose_support import ChooseSupport
from sr.operation.battle.choose_team import ChooseTeam
from sr.operation.battle.click_challenge import ClickChallenge
from sr.operation.battle.click_start_challenge import ClickStartChallenge
from sr.operation.battle.wait_battle_reward import WaitBattleReward
from sr.operation.combine.transport import Transport
from sr.interastral_peace_guide.survival_index_mission import SurvivalIndexCategoryEnum, SurvivalIndexMission
from sr.operation.unit.interact import Interact
from sr.operation.unit.wait import WaitInWorld


class UseTrailblazePower(StateOperation):

    AFTER_BATTLE_CHALLENGE_AGAIN_BTN: ClassVar[Rect] = Rect(1180, 930, 1330, 960)  # 战斗结束后领奖励页面 【再来一次】按钮
    AFTER_BATTLE_EXIT_BTN_RECT = Rect(640, 930, 780, 960)  # 战斗结束后领奖励页面 【退出关卡】按钮

    STATUS_BATTLE_FAIL: ClassVar[str] = '挑战失败'
    STATUS_CHALLENGE_AGAIN: ClassVar[str] = '再来一次'
    STATUS_CHALLENGE_EXIT_AGAIN: ClassVar[str] = '退出关卡后再来一次'
    STATUS_FINISH_EXIT: ClassVar[str] = '挑战完成'

    def __init__(self, ctx: Context, mission: SurvivalIndexMission,
                 team_num: int, plan_times: int, support: Optional[str] = None,
                 on_battle_success: Optional[Callable[[int, int], None]] = None,
                 need_transport: bool = True):
        """
        使用开拓力刷本
        :param ctx: 上下文
        :param mission: 挑战关卡
        :param team_num: 使用配队编号
        :param support: 使用支援 传入角色ID
        :param plan_times: 计划挑战次数
        :param on_battle_success: 战斗成功的回调 用于记录、扣体力等
        :param need_transport: 是否需要传送 如果出现连续两次都要挑战同一个副本 可以不传送
        """
        edges = []

        transport = StateOperationNode('传送', self._transport)
        interact = StateOperationNode('交互', self._interact)
        edges.append(StateOperationEdge(transport, interact))

        before_challenge = StateOperationNode('挑战前', self._before_click_challenge)
        edges.append(StateOperationEdge(interact, before_challenge))

        click_challenge = StateOperationNode('点击挑战', self._click_challenge)
        edges.append(StateOperationEdge(before_challenge, click_challenge))

        choose_team = StateOperationNode('选择配队', self._choose_team)
        edges.append(StateOperationEdge(click_challenge, choose_team))

        choose_support = StateOperationNode('选择支援', self._choose_support)
        edges.append(StateOperationEdge(choose_team, choose_support))

        click_start = StateOperationNode('开始挑战', self._start_challenge)
        edges.append(StateOperationEdge(choose_support, click_start))

        after_start_challenge = StateOperationNode('开始挑战后', self._after_start_challenge)
        edges.append(StateOperationEdge(click_start, after_start_challenge))

        battle = StateOperationNode('战斗', self._battle)
        edges.append(StateOperationEdge(after_start_challenge, battle))

        edges.append(StateOperationEdge(battle, battle, status=UseTrailblazePower.STATUS_CHALLENGE_AGAIN))
        edges.append(StateOperationEdge(battle, interact, status=UseTrailblazePower.STATUS_CHALLENGE_EXIT_AGAIN))

        wait_esc = StateOperationNode('等待退出', op=WaitInWorld(ctx))
        edges.append(StateOperationEdge(battle, wait_esc, status=UseTrailblazePower.STATUS_FINISH_EXIT))

        super().__init__(ctx, try_times=5,
                         op_name='%s %s %d' % (gt(mission.tp.cn, 'ui'), gt('次数', 'ui'), plan_times),
                         edges=edges
                         )

        self.mission: SurvivalIndexMission = mission
        self.team_num: int = team_num
        self.support: Optional[str] = support
        self.plan_times: int = plan_times  # 计划挑战次数
        self.finish_times: int = 0  # 已经完成的次数
        self.current_challenge_times: int = 1  # 当前挑战的次数
        self.need_transport: bool = need_transport  # 是否需要传送
        self.on_battle_success: Optional[Callable[[int, int], None]] = on_battle_success
        self.battle_fail_times: int = 0  # 战斗失败次数

    def _init_before_execute(self):
        super()._init_before_execute()
        self.finish_times = 0
        self.battle_fail_times = 0

    def _transport(self) -> OperationOneRoundResult:
        """
        传送
        :return:
        """
        if not self.need_transport:
            return Operation.round_success()
        op = Transport(self.ctx, self.mission.tp)
        return Operation.round_by_op(op.execute())

    def _interact(self) -> OperationOneRoundResult:
        """
        交互进入副本
        :return:
        """
        op = Interact(self.ctx, self.mission.tp.cn, 0.5, single_line=True, no_move=True)  # 交互进入副本
        # 等待一定时间 副本加载
        return Operation.round_by_op(op.execute(), wait=1.5)

    def _get_current_challenge_times(self) -> int:
        """
        获取当前的挑战次数
        :return:
        """
        if self.mission.cate == SurvivalIndexCategoryEnum.BUD_1.value or \
                self.mission.cate == SurvivalIndexCategoryEnum.BUD_2.value:
            current_challenge_times = self.plan_times - self.finish_times
            if current_challenge_times > 6:
                current_challenge_times = 6
            return current_challenge_times
        else:
            return 1

    def _before_click_challenge(self) -> OperationOneRoundResult:
        """
        点击挑战之前的初始化 由不同副本自行实现
        :return:
        """
        self.current_challenge_times = self._get_current_challenge_times()
        if self.mission.cate == SurvivalIndexCategoryEnum.BUD_1.value or \
                self.mission.cate == SurvivalIndexCategoryEnum.BUD_2.value:
            op = ChooseChallengeTimes(self.ctx, self.current_challenge_times)
            op_result = op.execute()
            return Operation.round_by_op(op_result)
        else:
            return Operation.round_success()

    def _click_challenge(self) -> OperationOneRoundResult:
        """
        点击挑战
        :return:
        """
        op = ClickChallenge(self.ctx)
        return Operation.round_by_op(op.execute())

    def _choose_team(self) -> OperationOneRoundResult:
        """
        选择配队
        :return:
        """
        op = ChooseTeam(self.ctx, self.team_num)
        return Operation.round_by_op(op.execute())

    def _choose_support(self):
        """
        选择支援
        :return:
        """
        if self.support is None:
            return Operation.round_success()
        op = ChooseSupport(self.ctx, self.support)
        return Operation.round_by_op(op.execute())

    def _start_challenge(self) -> OperationOneRoundResult:
        """
        开始挑战
        :return:
        """
        op = ClickStartChallenge(self.ctx)
        return Operation.round_by_op(op.execute())

    def _after_start_challenge(self) -> OperationOneRoundResult:
        """
        点击开始挑战后 进入战斗前
        :return:
        """
        if self.mission.cate == SurvivalIndexCategoryEnum.SHAPE.value:
            op = WaitInWorld(self.ctx, wait_after_success=2)  # 等待怪物苏醒
            op_result = op.execute()
            if not op_result.success:
                return Operation.round_fail('未在大世界画面')
            self.ctx.controller.initiate_attack()
            return Operation.round_success()
        else:
            return Operation.round_success()

    def _battle(self) -> OperationOneRoundResult:
        """
        战斗
        :return:
        """
        op = WaitBattleReward(self.ctx)
        op_result = op.execute()
        if not op_result.success:
            return Operation.round_by_op(op_result)

        if op_result.status == screen_state.ScreenState.TP_BATTLE_FAIL.value:
            self.battle_fail_times += 1
            if self.battle_fail_times >= 5:  # 失败次数过多 退出
                return Operation.round_fail(UseTrailblazePower.STATUS_BATTLE_FAIL)

            click = self.ocr_and_click_one_line('再来一次', UseTrailblazePower.AFTER_BATTLE_CHALLENGE_AGAIN_BTN, lcs_percent=0.1)
            if click == Operation.OCR_CLICK_SUCCESS:
                return Operation.round_success(UseTrailblazePower.STATUS_CHALLENGE_AGAIN, wait=2)  # 要等待画面加载
            else:
                return Operation.round_retry('点击再来一次失败')
        else:
            self.finish_times += self.current_challenge_times
            if self.on_battle_success is not None:
                self.on_battle_success(self.current_challenge_times, self.mission.power * self.current_challenge_times)

            if self.finish_times >= self.plan_times:
                click = self.ocr_and_click_one_line('退出关卡', UseTrailblazePower.AFTER_BATTLE_EXIT_BTN_RECT,
                                                    lcs_percent=0.1)
                if click == Operation.OCR_CLICK_SUCCESS:
                    return Operation.round_success(UseTrailblazePower.STATUS_FINISH_EXIT)
                else:
                    return Operation.round_retry('点击退出关卡失败')

            next_challenge_times = self._get_current_challenge_times()
            if next_challenge_times != self.current_challenge_times:
                click = self.ocr_and_click_one_line('退出关卡', UseTrailblazePower.AFTER_BATTLE_EXIT_BTN_RECT, lcs_percent=0.1)
                if click == Operation.OCR_CLICK_SUCCESS:
                    return Operation.round_success(UseTrailblazePower.STATUS_CHALLENGE_EXIT_AGAIN)
                else:
                    return Operation.round_retry('点击退出关卡失败')
            else:
                click = self.ocr_and_click_one_line('再来一次', UseTrailblazePower.AFTER_BATTLE_CHALLENGE_AGAIN_BTN, lcs_percent=0.1)
                if click == Operation.OCR_CLICK_SUCCESS:
                    return Operation.round_success(UseTrailblazePower.STATUS_CHALLENGE_AGAIN, wait=2)  # 要等待画面加载
                else:
                    return Operation.round_retry('点击再来一次失败')
