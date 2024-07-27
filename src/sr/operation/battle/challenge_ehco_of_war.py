from typing import Optional, Callable, ClassVar

from basic.i18_utils import gt
from sr.const.map_const import TransportPoint
from sr.context.context import Context
from sr.image.sceenshot import screen_state
from sr.interastral_peace_guide.guide_const import GuideMission
from sr.operation import Operation, StateOperation, StateOperationNode, OperationOneRoundResult
from sr.operation.battle.choose_support_in_team import ChooseSupportInTeam
from sr.operation.battle.choose_team import ChooseTeam
from sr.operation.battle.click_challenge import ClickChallenge
from sr.operation.battle.click_challenge_confirm import ClickChallengeConfirm
from sr.operation.battle.click_start_challenge import ClickStartChallenge
from sr.operation.battle.use_trailblaze_power import UseTrailblazePower
from sr.operation.combine.transport import Transport
from sr.operation.combine.transport_to_recover import TransportToRecover
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus
from sr.operation.unit.interact import Interact
from sr.screen_area.dialog import ScreenDialog
from sr.screen_area.screen_battle import ScreenBattle


class ChallengeEchoOfWar(StateOperation):

    STATUS_WITH_DEAD: ClassVar[str] = '有阵亡角色'

    def __init__(self, ctx: Context, mission: GuideMission,
                 team_num: int, plan_times: int,
                 support: Optional[str] = None,
                 on_battle_success: Optional[Callable[[int, int], None]]=None):
        """
        挑战历战余响
        这里不关注有没有剩余次数 由调用方控制
        这里就算没有剩余次数也会进行挑战的
        """
        super().__init__(ctx,
                         op_name='%s %s %s %d' % (
                             gt('历战回响', 'ui'),
                             mission.tp.display_name,
                             gt('次数', 'ui'),
                             plan_times
                         ))

        self.mission: GuideMission = mission
        self.team_num: int = team_num
        self.support: str = support
        self.on_battle_success = on_battle_success
        self.plan_times: int = plan_times  # 计划挑战次数

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        self.no_challenge_dialog: int = 0  # 没有阵亡的统计次数
        self.battle_fail_times: int = 0  # 战斗失败次数
        self.battle_success_times: int = 0  # 战斗成功次数

        return None

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        transport = StateOperationNode('传送', op=Transport(self.ctx, self.mission.tp))
        interact = StateOperationNode('交互进入副本', op=Interact(self.ctx, self.mission.tp.cn, 0.5, single_line=True))
        self.add_edge(transport, interact)

        click_challenge = StateOperationNode('点击挑战', op=ClickChallenge(self.ctx))
        self.add_edge(interact, click_challenge)

        # 开始挑战之后的对话框判断
        _first_challenge_confirm = StateOperationNode('点击挑战后确认', self.start_challenge_confirm)
        self.add_edge(click_challenge, _first_challenge_confirm)

        # 如果开拓力不足（之前识别错误了）
        _exit_without_tp_1 = StateOperationNode('点击挑战后开拓力不足', self.exit_first_challenge_without_tp)
        self.add_edge(_first_challenge_confirm, _exit_without_tp_1, status=ScreenDialog.CHALLENGE_WITHOUT_TP_CANCEL.value.status)

        # 挑战次数用完
        _exit_with_full = StateOperationNode('点击挑战后次数用完', self.exit_first_challenge_with_full)
        self.add_edge(_first_challenge_confirm, _exit_with_full, status=ScreenDialog.CHALLENGE_ECHO_FULL_CANCEL.value.status)

        choose_team = StateOperationNode('选择配队', op=ChooseTeam(self.ctx, self.team_num))
        self.add_edge(_first_challenge_confirm, choose_team)

        choose_support = StateOperationNode('选择支援', op=ChooseSupportInTeam(self.ctx, self.support))
        self.add_edge(choose_team, choose_support)

        start_challenge = StateOperationNode('开始挑战', op=ClickStartChallenge(self.ctx), wait_after_op=1)
        self.add_edge(choose_support, start_challenge)

        # 开始挑战之后的对话框判断
        _start_challenge_confirm = StateOperationNode('开始挑战后确认', self.start_challenge_confirm)
        self.add_edge(start_challenge, _start_challenge_confirm)

        # 如果有阵亡角色 退出恢复
        _tp_to_recover = StateOperationNode('传送恢复', op=TransportToRecover(self.ctx, self.mission.tp))
        self.add_edge(_start_challenge_confirm, _tp_to_recover, status=ScreenDialog.CHALLENGE_WITH_DEAD_CANCEL.value.status)
        self.add_edge(_tp_to_recover, transport)

        wait_battle_result = StateOperationNode('等待战斗结果', self._wait_battle_result)
        self.add_edge(_start_challenge_confirm, wait_battle_result)

        after_battle_result = StateOperationNode('战斗结果处理', self._after_battle_result)
        self.add_edge(wait_battle_result, after_battle_result, ignore_status=True)

        # 再来一次之后的对话框判断
        _challenge_again_confirm = StateOperationNode('再来一次后确认', self.start_challenge_confirm)
        self.add_edge(after_battle_result, _challenge_again_confirm, status=ScreenBattle.AFTER_BATTLE_CHALLENGE_AGAIN_BTN.value.status)

        # 正常再来一次进入战斗
        self.add_edge(_challenge_again_confirm, wait_battle_result)

        # 如果有阵亡角色 退出恢复
        _exit_to_recover = StateOperationNode('阵亡退出恢复', self.exit_to_recover)
        self.add_edge(_challenge_again_confirm, _exit_to_recover, status=ScreenDialog.CHALLENGE_WITH_DEAD_CANCEL.value.status)
        self.add_edge(_exit_to_recover, _tp_to_recover)

        # 如果开拓力不足（之前识别错误了）
        # 挑战前不会出现 只有再次挑战时出现 出现则直接退出
        _exit_without_tp = StateOperationNode('开拓力不足', self.self_exit_without_tp)
        self.add_edge(_challenge_again_confirm, _tp_to_recover, status=ScreenDialog.CHALLENGE_WITHOUT_TP_CANCEL.value.status)

        # 退出时 有可能弹出光锥 因此使用加强版返回
        wait_esc = StateOperationNode('等待退出', op=BackToNormalWorldPlus(self.ctx))
        self.add_edge(after_battle_result, wait_esc, status=ScreenBattle.AFTER_BATTLE_EXIT_BTN.value.status)
        self.add_edge(_exit_without_tp, wait_esc)

        self.param_start_node = transport

    def start_challenge_confirm(self) -> OperationOneRoundResult:
        """
        点击挑战后 判断当前有没有对话框 需保证点击挑战1秒后再触发
        :return:
        """
        screen = self.screenshot()
        no_tp_dialog = ScreenDialog.CHALLENGE_WITHOUT_TP_TITLE.value

        # 开拓力不足
        if self.find_area(screen=screen, area=no_tp_dialog):
            area = ScreenDialog.CHALLENGE_WITHOUT_TP_CANCEL.value
            return self.round_by_find_and_click_area(screen, area, retry_wait_round=1)

        # 挑战次数用完
        full_dialog_title = ScreenDialog.CHALLENGE_ECHO_FULL_TITLE.value
        full_dialog_content = ScreenDialog.CHALLENGE_ECHO_FULL_CONTENT.value
        if self.find_area(screen=screen, area=full_dialog_title) and self.find_area(screen=screen, area=full_dialog_content):
            area = ScreenDialog.CHALLENGE_ECHO_FULL_CANCEL.value
            return self.round_by_find_and_click_area(screen, area, retry_wait_round=1)

        # 有阵亡
        dead_dialog = ScreenDialog.CHALLENGE_WITH_DEAD_TITLE.value
        if self.find_area(screen=screen, area=dead_dialog):
            area = ScreenDialog.CHALLENGE_WITH_DEAD_CANCEL.value
            return self.round_by_find_and_click_area(screen, area, retry_wait_round=1)

        return self.round_success()

    def exit_first_challenge_without_tp(self) -> OperationOneRoundResult:
        """
        点击挑战后 开拓力不足退出
        说明之前识别开拓力错了
        :return:
        """
        if self.on_battle_success is not None:
            self.on_battle_success(0, 200)  # 清空开拓力
        op = BackToNormalWorldPlus(self.ctx)
        return self.round_by_op(op.execute())

    def exit_first_challenge_with_full(self) -> OperationOneRoundResult:
        """
        点击挑战后 奖励次数用完退出
        :return:
        """
        self.ctx.echo_run_record.left_times = 0  # 清空剩余次数
        op = BackToNormalWorldPlus(self.ctx)
        return self.round_by_op(op.execute())

    def _wait_battle_result(self) -> OperationOneRoundResult:
        """
        等待战斗结果
        :return:
        """
        screen = self.screenshot()

        state = screen_state.get_tp_battle_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                        battle_success=True,
                                                        battle_fail=True
                                                        )

        if state == ScreenBattle.AFTER_BATTLE_FAIL_1.value.status:
            self.battle_fail_times += 1
            return self.round_success(state)
        elif state == ScreenBattle.AFTER_BATTLE_SUCCESS_1.value.status:
            self.battle_success_times += 1
            if self.on_battle_success is not None:
                self.on_battle_success(1, self.mission.power)
            return self.round_success(state)
        else:
            return self.round_wait('等待战斗结束', wait=1)

    def _after_battle_result(self) -> OperationOneRoundResult:
        """
        战斗结果出来后 点击再来一次或退出
        :return:
        """
        screen = self.screenshot()
        if self.battle_fail_times >= 5 or self.battle_success_times >= self.plan_times:  # 失败过多或者完成指定次数了 退出
            area = ScreenBattle.AFTER_BATTLE_EXIT_BTN.value
            status = area.status
        else:  # 还需要继续挑战
            area = ScreenBattle.AFTER_BATTLE_CHALLENGE_AGAIN_BTN.value
            status = area.status

        click = self.find_and_click_area(area, screen)
        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(status, wait=2)
        else:
            return self.round_retry('点击%s失败' % area.status, wait=1)

    def challenge_again_confirm(self) -> OperationOneRoundResult:
        """
        再来一次的确认 在有角色阵亡时候会弹出来
        :return:
        """
        screen = self.screenshot()
        area = ScreenDialog.CHALLENGE_WITH_DEAD_CANCEL.value
        click = self.find_and_click_area(area, screen)
        if click in [Operation.OCR_CLICK_SUCCESS, Operation.OCR_CLICK_NOT_FOUND]:
            return self.round_success(wait=2)
        else:
            return self.round_retry('点击%s失败' % area.status, wait=1)

    def exit_to_recover(self) -> OperationOneRoundResult:
        """
        退出先恢复
        :return:
        """
        screen = self.screenshot()
        area = ScreenBattle.AFTER_BATTLE_EXIT_BTN.value
        return self.round_by_find_and_click_area(screen, area, retry_wait_round=1)

    def self_exit_without_tp(self) -> OperationOneRoundResult:
        if self.on_battle_success is not None:
            self.on_battle_success(0, 200)  # 清空开拓力
        return UseTrailblazePower.exit_without_tp(self)
