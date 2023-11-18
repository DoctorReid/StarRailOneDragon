from typing import List

from basic.i18_utils import gt
from sr.const.map_const import TransportPoint
from sr.context import Context
from sr.operation import Operation
from sr.operation.combine import CombineOperation
from sr.operation.combine.transport import Transport
from sr.operation.unit.battle.choose_team import ChooseTeam
from sr.operation.unit.battle.click_challenge import ClickChallenge
from sr.operation.unit.battle.click_challenge_confirm import ClickChallengeConfirm
from sr.operation.unit.battle.click_start_challenge import ClickStartChallenge
from sr.operation.unit.battle.get_reward_and_retry import GetRewardAndRetry
from sr.operation.unit.interact import Interact
from sr.operation.unit.wait_in_world import WaitInWorld


class ChallengeEchoOfWar(CombineOperation):
    """
    挑战历战回响
    这里不关注有没有剩余次数 由调用方控制
    这里就算没有剩余次数也会进行挑战的
    """

    def __init__(self, ctx: Context, tp: TransportPoint, team_num: int, run_times: int,
                 on_battle_success=None):
        self.ctx: Context = ctx
        self.tp: TransportPoint = tp
        self.team_num: int = team_num
        self.run_times: int = run_times
        self.on_battle_success = on_battle_success

        ops: List[Operation] = [
            Transport(ctx, self.tp),  # 传送到对应位置
            Interact(self.ctx, self.tp.cn, 0.5),  # 交互进入副本
            ClickChallenge(self.ctx),  # 点击挑战
            ClickChallengeConfirm(self.ctx),  # 点击确认
            ChooseTeam(self.ctx, self.team_num),  # 选择配队
            ClickStartChallenge(self.ctx),  # 开始挑战
            GetRewardAndRetry(self.ctx, run_times, success_callback=on_battle_success, need_confirm=True),  # 领奖 重复挑战
            WaitInWorld(self.ctx),  # 等待主界面
        ]

        super().__init__(ctx, ops, op_name='%s %s %d' % (gt(tp.cn, 'ui'), gt('次数', 'ui'), run_times))