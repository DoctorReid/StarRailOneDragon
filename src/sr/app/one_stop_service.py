from typing import List, Optional

from basic.i18_utils import gt
from sr.app import Application, app_const, AppRunRecord, world_patrol
from sr.app.app_const import AppDescription
from sr.app.routine import assignments, email, support_character, nameless_honor, claim_training, buy_parcel
from sr.app.routine.assignments import Assignments
from sr.app.routine.buy_parcel import BuyXianzhouParcel
from sr.app.routine.claim_training import ClaimTraining
from sr.app.routine.email import Email
from sr.app.routine.nameless_honor import ClaimNamelessHonor
from sr.app.routine.support_character import SupportCharacter
from sr.app.world_patrol.world_patrol_app import WorldPatrol
from sr.config import ConfigHolder
from sr.context import Context
from sr.operation import Operation


class OneStopServiceConfig(ConfigHolder):

    def __init__(self):
        super().__init__('one_stop_service')

    def _init_after_read_file(self):
        current_list = self.order_app_id_list
        need_update: bool = False
        for app in app_const.ROUTINE_APP_LIST:
            if app['id'] not in current_list:
                current_list.append(app['id'])
                need_update = True
        if need_update:
            self.order_app_id_list = current_list

    @property
    def order_app_id_list(self) -> List[str]:
        return self.get('app_order')

    @order_app_id_list.setter
    def order_app_id_list(self, new_list: List[str]):
        self.update('app_order', new_list)
        self.save()


one_stop_service_config: OneStopServiceConfig = None


def get_config():
    global one_stop_service_config
    if one_stop_service_config is None:
        one_stop_service_config = OneStopServiceConfig()
    return one_stop_service_config


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

    @property
    def current_execution_desc(self) -> str:
        """
        当前运行的描述 用于UI展示
        :return:
        """
        return gt(self.app_list[self.app_idx]['cn'], 'ui')

    @property
    def next_execution_desc(self) -> str:
        """
        下一步运行的描述 用于UI展示
        :return:
        """
        if self.app_idx >= len(self.app_list) - 1:
            return gt('无', 'ui')
        else:
            return gt(self.app_list[self.app_idx + 1]['cn'], 'ui')


def get_app_by_id(app_id: str, ctx: Context) -> Optional[Application]:
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


def get_app_run_record_by_id(app_id: str) -> Optional[AppRunRecord]:
    if app_id == app_const.WORLD_PATROL['id']:
        return world_patrol.get_record()
    elif app_id == app_const.ASSIGNMENTS['id']:
        return assignments.get_record()
    elif app_id == app_const.EMAIL['id']:
        return email.get_record()
    elif app_id == app_const.SUPPORT_CHARACTER['id']:
        return support_character.get_record()
    elif app_id == app_const.NAMELESS_HONOR['id']:
        return nameless_honor.get_record()
    elif app_id == app_const.CLAIM_TRAINING['id']:
        return claim_training.get_record()
    elif app_id == app_const.BUY_XIANZHOU_PARCEL['id']:
        return buy_parcel.get_record()
    return None
