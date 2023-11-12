from typing import List

from basic.i18_utils import gt
from sr.app import Application, app_const
from sr.app.app_const import AppDescription
from sr.app.routine.assignments import Assignments
from sr.app.routine.buy_xianzhoue_parcel import BuyXianzhouParcel
from sr.app.routine.claim_training import ClaimTraining
from sr.app.routine.email import Email
from sr.app.routine.nameless_honor import ClaimNamelessHonor
from sr.app.routine.support_character import SupportCharacter
from sr.app.world_patrol.world_patrol_app import WorldPatrol
from sr.context import Context
from sr.operation import Operation


class OneStopService(Application):

    def __init__(self, ctx: Context, app_list: List[AppDescription]):
        super().__init__(ctx, op_name=gt('一条龙', 'ui'))
        self.app_list: List[AppDescription] = app_list
        self.app_idx: int = 0

    def _init_before_execute(self):
        self.app_idx = 0

    def _execute_one_round(self) -> int:
        app: Application = get_app_by_id(self.app_list[self.app_idx]['id'], self.ctx)
        app.init_context_before_start = False  # 一条龙开始时已经初始化了
        app.stop_context_after_stop = self.app_idx >= len(self.app_list)  # 只有最后一个任务结束会停止context

        result = app.execute()  # 暂时忽略结果 直接全部运行
        self.app_idx += 1

        if self.app_idx >= len(self.app_list):
            return Operation.SUCCESS
        else:
            return Operation.WAIT

    def current_execution_desc(self) -> str:
        """
        当前运行的描述 用于UI展示
        :return:
        """
        return gt(self.app_list[self.app_idx]['cn'], 'ui')

    def next_execution_desc(self) -> str:
        """
        下一步运行的描述 用于UI展示
        :return:
        """
        if self.app_idx >= len(self.app_list) - 1:
            return gt('无', 'ui')
        else:
            return gt(self.app_list[self.app_idx + 1]['cn'], 'ui')


def get_app_by_id(app_id: str, ctx: Context) -> Application:
    if app_id == app_const.WORLD_PATROL['id']:
        return WorldPatrol(ctx)
    elif app_id == app_const.ASSIGNMENTS['id']:
        return Assignments(ctx)
    elif app_id == app_const.EMAIL['id']:
        return Email(ctx)
    elif app_id == app_const.SUPPORT_CHARACTER['id']:
        return SupportCharacter(ctx)
    elif app_id == app_const.NAMELESS_HONOR['id']:
        return ClaimNamelessHonor(ctx)
    elif app_id == app_const.CLAIM_TRAINING['id']:
        return ClaimTraining(ctx)
    elif app_id == app_const.BUY_XIANZHOU_PARCEL['id']:
        return BuyXianzhouParcel(ctx)
    return None