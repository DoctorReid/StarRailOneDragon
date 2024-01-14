from typing import List, Optional

import sr.app
import sr.app.routine.assignments
from basic.i18_utils import gt
from sr.app import Application, AppRunRecord, world_patrol, AppDescription
from sr.app.sim_uni import sim_universe_app
from sr.app.routine import assignments, support_character, nameless_honor, daily_training_app, buy_parcel, \
    trailblaze_power, email_attachment, echo_of_war, forgotten_hall_app
from sr.app.routine.assignments import Assignments, ASSIGNMENTS
from sr.app.routine.buy_parcel import BuyXianzhouParcel, BUY_XIANZHOU_PARCEL
from sr.app.routine.echo_of_war import ECHO_OF_WAR, EchoOfWar
from sr.app.routine.email_attachment import Email, EMAIL
from sr.app.routine.nameless_honor import ClaimNamelessHonor, NAMELESS_HONOR
from sr.app.routine.support_character import SupportCharacter, SUPPORT_CHARACTER
from sr.app.routine.trailblaze_power import TrailblazePower, TRAILBLAZE_POWER
from sr.app.world_patrol import WORLD_PATROL
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
        for app in sr.app.ALL_APP_LIST:
            if app.id not in current_list:
                current_list.append(app.id)
                need_update = True

        new_list = []
        for app_id in current_list:
            valid = False
            for app in sr.app.ALL_APP_LIST:
                if app_id == app.id:
                    valid = True
                    break
            if valid:
                new_list.append(app_id)
            else:
                need_update = True

        if need_update:
            self.order_app_id_list = new_list

    @property
    def order_app_id_list(self) -> List[str]:
        return self.get('app_order')

    @order_app_id_list.setter
    def order_app_id_list(self, new_list: List[str]):
        self.update('app_order', new_list)
        self.save()

    @property
    def run_app_id_list(self) -> List[str]:
        return self.get('app_run')

    @run_app_id_list.setter
    def run_app_id_list(self, new_list: List[str]):
        self.update('app_run', new_list)
        self.save()

    @property
    def schedule_hour_1(self):
        return self.get('schedule_hour_1', 'none')

    @schedule_hour_1.setter
    def schedule_hour_1(self, new_value: str):
        self.update('schedule_hour_1', new_value)

    @property
    def schedule_hour_2(self):
        return self.get('schedule_hour_2', 'none')

    @schedule_hour_2.setter
    def schedule_hour_2(self, new_value: str):
        self.update('schedule_hour_2', new_value)


one_stop_service_config: OneStopServiceConfig = None


def get_config() -> OneStopServiceConfig:
    global one_stop_service_config
    if one_stop_service_config is None:
        one_stop_service_config = OneStopServiceConfig()
    return one_stop_service_config


class OneStopService(Application):

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('一条龙', 'ui'))
        self.app_list: List[AppDescription] = []
        run_app_list = get_config().run_app_id_list
        for app_id in get_config().order_app_id_list:
            if app_id not in run_app_list:
                continue
            update_app_run_record_before_start(app_id)
            record = get_app_run_record_by_id(app_id)

            if record.run_status_under_now != AppRunRecord.STATUS_SUCCESS:
                self.app_list.append(sr.app.get_app_desc_by_id(app_id))

        self.app_idx: int = 0

    def _init_before_execute(self):
        super()._init_before_execute()
        self.app_idx = 0

    def _execute_one_round(self) -> int:
        if self.app_idx >= len(self.app_list):  # 有可能刚开始就所有任务都已经执行完了
            return Operation.SUCCESS
        app: Application = get_app_by_id(self.app_list[self.app_idx].id, self.ctx)
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
        if self.app_idx >= len(self.app_list):
            return gt('无', 'ui')
        else:
            return gt(self.app_list[self.app_idx].cn, 'ui')

    @property
    def next_execution_desc(self) -> str:
        """
        下一步运行的描述 用于UI展示
        :return:
        """
        if self.app_idx >= len(self.app_list) - 1:
            return gt('无', 'ui')
        else:
            return gt(self.app_list[self.app_idx + 1].cn, 'ui')


def get_app_by_id(app_id: str, ctx: Context) -> Optional[Application]:
    if app_id == WORLD_PATROL.id:
        return WorldPatrol(ctx)
    elif app_id == ASSIGNMENTS.id:
        return Assignments(ctx)
    elif app_id == EMAIL.id:
        return Email(ctx)
    elif app_id == SUPPORT_CHARACTER.id:
        return SupportCharacter(ctx)
    elif app_id == NAMELESS_HONOR.id:
        return ClaimNamelessHonor(ctx)
    elif app_id == daily_training_app.DAILY_TRAINING.id:
        return daily_training_app.DailyTrainingApp(ctx)
    elif app_id == BUY_XIANZHOU_PARCEL.id:
        return BuyXianzhouParcel(ctx)
    elif app_id == TRAILBLAZE_POWER.id:
        return TrailblazePower(ctx)
    elif app_id == ECHO_OF_WAR.id:
        return EchoOfWar(ctx)
    elif app_id == forgotten_hall_app.FORGOTTEN_HALL.id:
        return forgotten_hall_app.ForgottenHallApp(ctx)
    elif app_id == sim_universe_app.SIM_UNIVERSE.id:
        return sim_universe_app.SimUniverseApp(ctx)
    return None


def get_app_run_record_by_id(app_id: str) -> Optional[AppRunRecord]:
    if app_id == WORLD_PATROL.id:
        return world_patrol.get_record()
    elif app_id == ASSIGNMENTS.id:
        return assignments.get_record()
    elif app_id == EMAIL.id:
        return email_attachment.get_record()
    elif app_id == SUPPORT_CHARACTER.id:
        return support_character.get_record()
    elif app_id == NAMELESS_HONOR.id:
        return nameless_honor.get_record()
    elif app_id == daily_training_app.DAILY_TRAINING.id:
        return daily_training_app.get_record()
    elif app_id == BUY_XIANZHOU_PARCEL.id:
        return buy_parcel.get_record()
    elif app_id == TRAILBLAZE_POWER.id:
        return trailblaze_power.get_record()
    elif app_id == ECHO_OF_WAR.id:
        return echo_of_war.get_record()
    elif app_id == forgotten_hall_app.FORGOTTEN_HALL.id:
        return forgotten_hall_app.get_record()
    elif app_id == sim_universe_app.SIM_UNIVERSE.id:
        return sim_universe_app.get_record()
    return None


def update_app_run_record_before_start(app_id: str):
    """
    每次开始前 根据外部信息更新运行状态
    :param app_id:
    :return:
    """
    record: Optional[AppRunRecord] = get_app_run_record_by_id(app_id)
    if record is not None:
        record.check_and_update_status()
