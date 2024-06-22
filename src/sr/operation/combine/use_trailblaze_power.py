from typing import Optional, Callable, ClassVar

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.interastral_peace_guide.guide_const import GuideCategoryEnum, GuideMission
from sr.operation import Operation, StateOperation, OperationOneRoundResult, StateOperationNode, StateOperationEdge
from sr.operation.battle.choose_challenge_times import ChooseChallengeTimes
from sr.operation.battle.choose_support_in_team import ChooseSupportInTeam
from sr.operation.battle.choose_team import ChooseTeam
from sr.operation.battle.click_challenge import ClickChallenge
from sr.operation.battle.click_start_challenge import ClickStartChallenge
from sr.operation.combine.transport import Transport
from sr.operation.unit.interact import Interact
from sr.operation.unit.wait import WaitInWorld
from sr.screen_area.screen_battle import ScreenBattle


class UseTrailblazePower(StateOperation):

    STATUS_CHALLENGE_EXIT_AGAIN: ClassVar[str] = '退出关卡后再来一次'

    def __init__(self, ctx: Context, mission: GuideMission,
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

        wait_battle_result = StateOperationNode('等待战斗结果', self._wait_battle_result, timeout_seconds=600)
        edges.append(StateOperationEdge(after_start_challenge, wait_battle_result))

        after_battle_result = StateOperationNode('战斗结果处理', self._after_battle_result)
        edges.append(StateOperationEdge(wait_battle_result, after_battle_result, ignore_status=True))

        # 再来一次的确认 在有角色阵亡时候会弹出来
        confirm_again = StateOperationNode('确认再来一次', self._confirm_again)
        edges.append(StateOperationEdge(after_battle_result, confirm_again, status=ScreenBattle.AFTER_BATTLE_CHALLENGE_AGAIN_BTN.value.status))
        edges.append(StateOperationEdge(confirm_again, wait_battle_result))
        edges.append(StateOperationEdge(after_battle_result, interact, status=UseTrailblazePower.STATUS_CHALLENGE_EXIT_AGAIN))

        wait_esc = StateOperationNode('等待退出', op=WaitInWorld(ctx))
        edges.append(StateOperationEdge(after_battle_result, wait_esc, status=ScreenBattle.AFTER_BATTLE_EXIT_BTN.value.status))

        super().__init__(ctx, try_times=5,
                         op_name='%s %s %d' % (gt(mission.tp.cn, 'ui'), gt('次数', 'ui'), plan_times),
                         edges=edges
                         )

        self.mission: GuideMission = mission
        self.team_num: int = team_num
        self.support: Optional[str] = support
        self.plan_times: int = plan_times  # 计划挑战次数
        self.finish_times: int = 0  # 已经完成的次数
        self.current_challenge_times: int = 1  # 当前挑战的次数
        self.need_transport: bool = need_transport  # 是否需要传送
        self.on_battle_success: Optional[Callable[[int, int], None]] = on_battle_success
        self.battle_fail_times: int = 0  # 战斗失败次数

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        self.finish_times = 0
        self.battle_fail_times = 0

        return None

    def _transport(self) -> OperationOneRoundResult:
        """
        传送
        :return:
        """
        if not self.need_transport:
            return self.round_success()
        op = Transport(self.ctx, self.mission.tp)
        return self.round_by_op(op.execute())

    def _interact(self) -> OperationOneRoundResult:
        """
        交互进入副本
        :return:
        """
        op = Interact(self.ctx, self.mission.tp.cn, 0.5, single_line=True, no_move=True)  # 交互进入副本
        # 等待一定时间 副本加载
        return self.round_by_op(op.execute(), wait=1.5)

    def _get_current_challenge_times(self) -> int:
        """
        获取当前的挑战次数
        :return:
        """
        if self.mission.cate == GuideCategoryEnum.BUD_1.value or \
                self.mission.cate == GuideCategoryEnum.BUD_2.value:
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
        if self.mission.cate == GuideCategoryEnum.BUD_1.value or \
                self.mission.cate == GuideCategoryEnum.BUD_2.value:
            op = ChooseChallengeTimes(self.ctx, self.current_challenge_times)
            op_result = op.execute()
            return self.round_by_op(op_result)
        else:
            return self.round_success()

    def _click_challenge(self) -> OperationOneRoundResult:
        """
        点击挑战
        :return:
        """
        op = ClickChallenge(self.ctx)
        return self.round_by_op(op.execute())

    def _choose_team(self) -> OperationOneRoundResult:
        """
        选择配队
        :return:
        """
        op = ChooseTeam(self.ctx, self.team_num)
        return self.round_by_op(op.execute())

    def _choose_support(self):
        """
        选择支援
        :return:
        """
        if self.support is None:
            return self.round_success()
        op = ChooseSupportInTeam(self.ctx, self.support)
        return self.round_by_op(op.execute())

    def _start_challenge(self) -> OperationOneRoundResult:
        """
        开始挑战
        :return:
        """
        op = ClickStartChallenge(self.ctx)
        return self.round_by_op(op.execute())

    def _after_start_challenge(self) -> OperationOneRoundResult:
        """
        点击开始挑战后 进入战斗前
        :return:
        """
        if self.mission.cate == GuideCategoryEnum.SHAPE.value:
            op = WaitInWorld(self.ctx, wait_after_success=2)  # 等待怪物苏醒
            op_result = op.execute()
            if not op_result.success:
                return self.round_fail('未在大世界画面')
            self.ctx.controller.initiate_attack()
            return self.round_success(wait=1)
        else:
            return self.round_success()

    def _wait_battle_result(self) -> OperationOneRoundResult:
        """
        等待战斗结果
        :return:
        """
        screen = self.screenshot()

        state = screen_state.get_tp_battle_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                        battle_success=True,
                                                        battle_fail=True)

        if state == ScreenBattle.AFTER_BATTLE_FAIL_1.value.status:
            self.battle_fail_times += 1
            return self.round_success(state)
        elif state == ScreenBattle.AFTER_BATTLE_SUCCESS_1.value.status:
            self.finish_times += self.current_challenge_times
            if self.on_battle_success is not None:
                self.on_battle_success(self.current_challenge_times, self.mission.power * self.current_challenge_times)
            return self.round_success(state)
        else:
            return self.round_wait('等待战斗结束', wait=1)

    def _after_battle_result(self) -> OperationOneRoundResult:
        """
        战斗结果出来后 点击再来一次或退出
        :return:
        """
        screen = self.screenshot()
        if self.battle_fail_times >= 5 or self.finish_times >= self.plan_times:  # 失败过多或者完成指定次数了 退出
            area = ScreenBattle.AFTER_BATTLE_EXIT_BTN.value
            status = area.status
        else:  # 还需要继续挑战
            next_challenge_times = self._get_current_challenge_times()  # 看下一次挑战轮数是否跟当前一致
            if next_challenge_times != self.current_challenge_times:
                area = ScreenBattle.AFTER_BATTLE_EXIT_BTN.value
                status = UseTrailblazePower.STATUS_CHALLENGE_EXIT_AGAIN
            else:
                area = ScreenBattle.AFTER_BATTLE_CHALLENGE_AGAIN_BTN.value
                status = area.status

        click = self.find_and_click_area(area, screen)
        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(status, wait=2)
        else:
            return self.round_retry('点击%s失败' % area.status, wait=1)

    def _confirm_again(self) -> OperationOneRoundResult:
        """
        再来一次的确认 在有角色阵亡时候会弹出来
        :return:
        """
        screen = self.screenshot()
        area = ScreenBattle.AFTER_BATTLE_CONFIRM_AGAIN_BTN.value
        click = self.find_and_click_area(area, screen)
        if click in [Operation.OCR_CLICK_SUCCESS, Operation.OCR_CLICK_NOT_FOUND]:
            return self.round_success(wait=2)
        else:
            return self.round_retry('点击%s失败' % area.status, wait=1)
