from typing import List, Optional, Callable

from basic.i18_utils import gt
from sr.const.map_const import TransportPoint
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, StateOperation, StateOperationEdge, StateOperationNode, OperationOneRoundResult
from sr.operation.battle.choose_support import ChooseSupport
from sr.operation.battle.choose_team import ChooseTeam
from sr.operation.battle.click_challenge import ClickChallenge
from sr.operation.battle.click_challenge_confirm import ClickChallengeConfirm
from sr.operation.battle.click_start_challenge import ClickStartChallenge
from sr.operation.combine.transport import Transport
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus
from sr.operation.unit.interact import Interact
from sr.operation.unit.wait import WaitInWorld
from sr.screen_area.screen_battle import ScreenBattle


class ChallengeEchoOfWar(StateOperation):

    def __init__(self, ctx: Context, tp: TransportPoint,
                 team_num: int, plan_times: int,
                 support: Optional[str] = None,
                 on_battle_success: Optional[Callable[[], None]]=None):
        """
        挑战历战余响
        这里不关注有没有剩余次数 由调用方控制
        这里就算没有剩余次数也会进行挑战的
        """
        edges: List[StateOperationEdge] = []

        transport = StateOperationNode('传送', op=Transport(ctx, tp))
        interact = StateOperationNode('交互进入副本', op=Interact(ctx, tp.cn, 0.5, single_line=True))
        edges.append(StateOperationEdge(transport, interact))

        click_challenge = StateOperationNode('点击挑战', op=ClickChallenge(ctx))
        edges.append(StateOperationEdge(interact, click_challenge))

        # 没有剩余次数时 会弹出一个确认对话框
        challenge_confirm = StateOperationNode('挑战后点击确认', op=ClickChallengeConfirm(ctx))
        edges.append(StateOperationEdge(click_challenge, challenge_confirm))

        choose_team = StateOperationNode('选择配队', op=ChooseTeam(ctx, team_num))
        edges.append(StateOperationEdge(challenge_confirm, choose_team))

        choose_support = StateOperationNode('选择支援', op=ChooseSupport(ctx, support))
        edges.append(StateOperationEdge(choose_team, choose_support))

        start_challenge = StateOperationNode('开始挑战', op=ClickStartChallenge(ctx))
        edges.append(StateOperationEdge(choose_support, start_challenge))

        wait_battle_result = StateOperationNode('等待战斗结果', self._wait_battle_result)
        edges.append(StateOperationEdge(start_challenge, wait_battle_result))

        after_battle_result = StateOperationNode('战斗结果处理', self._after_battle_result)
        edges.append(StateOperationEdge(wait_battle_result, after_battle_result, ignore_status=True))

        # 再来一次的确认 在有角色阵亡时候会弹出来
        confirm_again = StateOperationNode('确认再来一次', self._confirm_again)
        edges.append(StateOperationEdge(after_battle_result, confirm_again, status=ScreenBattle.AFTER_BATTLE_CHALLENGE_AGAIN_BTN.value.status))
        edges.append(StateOperationEdge(confirm_again, wait_battle_result))

        # 退出时 有可能弹出光锥 因此使用加强版返回
        wait_esc = StateOperationNode('等待退出', op=BackToNormalWorldPlus(ctx))
        edges.append(StateOperationEdge(after_battle_result, wait_esc, status=ScreenBattle.AFTER_BATTLE_EXIT_BTN.value.status))

        self.ctx: Context = ctx
        self.tp: TransportPoint = tp
        self.team_num: int = team_num
        self.on_battle_success = on_battle_success

        ops: List[Operation] = [
            WaitInWorld(self.ctx),  # 等待主界面
        ]

        super().__init__(ctx, ops, op_name='%s %s %d' % (gt(tp.cn, 'ui'), gt('次数', 'ui'), plan_times))

        self.plan_times: int = plan_times  # 计划挑战次数
        self.battle_fail_times: int = 0  # 战斗失败次数
        self.battle_success_times: int = 0  # 战斗成功次数

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
            return Operation.round_success(state)
        elif state == ScreenBattle.AFTER_BATTLE_SUCCESS_1.value.status:
            self.battle_success_times += 1
            if self.on_battle_success is not None:
                self.on_battle_success()
            return Operation.round_success(state)
        else:
            return Operation.round_wait('等待战斗结束', wait=1)

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
            return Operation.round_success(status, wait=2)
        else:
            return Operation.round_retry('点击%s失败' % area.status, wait=1)

    def _confirm_again(self) -> OperationOneRoundResult:
        """
        再来一次的确认 在有角色阵亡时候会弹出来
        :return:
        """
        screen = self.screenshot()
        area = ScreenBattle.AFTER_BATTLE_CONFIRM_AGAIN_BTN.value
        click = self.find_and_click_area(area, screen)
        if click in [Operation.OCR_CLICK_SUCCESS, Operation.OCR_CLICK_NOT_FOUND]:
            return Operation.round_success(wait=2)
        else:
            return Operation.round_retry('点击%s失败' % area.status, wait=1)
