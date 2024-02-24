from typing import List, Optional

from basic.config import ConfigHolder
from basic.i18_utils import gt
from sr.app.app_description import AppDescriptionEnum, AppDescription
from sr.app.app_run_record import AppRunRecord
from sr.app.application_base import Application
from sr.app.assignments.assignments_app import AssignmentsApp
from sr.app.buy_xianzhou_parcel.buy_xianzhou_parcel_app import BuyXianzhouParcelApp
from sr.app.daily_training.daily_training_app import DailyTrainingApp
from sr.app.routine import support_character, nameless_honor, email_attachment
from sr.app.routine.echo_of_war import EchoOfWarApp
from sr.app.routine.email_attachment import Email, EMAIL
from sr.app.routine.nameless_honor import ClaimNamelessHonor, NAMELESS_HONOR
from sr.app.routine.support_character import SupportCharacter, SUPPORT_CHARACTER
from sr.app.sim_uni import sim_universe_app
from sr.app.trailblaze_power.trailblaze_power_app import TrailblazePower
from sr.app.treasures_lightward.treasures_lightward_app import TreasuresLightwardApp
from sr.app.world_patrol.world_patrol_app import WorldPatrol
from sr.context import Context
from sr.operation import Operation


class OneStopServiceConfig(ConfigHolder):

    def __init__(self):
        super().__init__('one_stop_service')

    def _init_after_read_file(self):
        current_list = self.order_app_id_list
        need_update: bool = False
        for app_enum in AppDescriptionEnum:
            app = app_enum.value
            if app.id not in current_list:
                current_list.append(app.id)
                need_update = True

        new_list = []
        for app_id in current_list:
            valid = False
            for app_enum in AppDescriptionEnum:
                app = app_enum.value
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
            OneStopService.update_app_run_record_before_start(app_id, self.ctx)
            record = OneStopService.get_app_run_record_by_id(app_id, self.ctx)

            if record.run_status_under_now != AppRunRecord.STATUS_SUCCESS:
                self.app_list.append(AppDescriptionEnum[app_id.upper()].value)

        self.app_idx: int = 0

    def _init_before_execute(self):
        super()._init_before_execute()
        self.app_idx = 0

    def _execute_one_round(self) -> int:
        if self.app_idx >= len(self.app_list):  # 有可能刚开始就所有任务都已经执行完了
            return Operation.SUCCESS
        app: Application = self.get_app_by_id(self.app_list[self.app_idx].id)
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

    @staticmethod
    def get_app_by_id(app_id: str, ctx: Context) -> Optional[Application]:
        if app_id == AppDescriptionEnum.WORLD_PATROL.value.id:
            return WorldPatrol(ctx)
        elif app_id == AppDescriptionEnum.ASSIGNMENTS.value.id:
            return AssignmentsApp(ctx)
        elif app_id == EMAIL.id:
            return Email(ctx)
        elif app_id == SUPPORT_CHARACTER.id:
            return SupportCharacter(ctx)
        elif app_id == NAMELESS_HONOR.id:
            return ClaimNamelessHonor(ctx)
        elif app_id == AppDescriptionEnum.DAILY_TRAINING.value.id:
            return DailyTrainingApp(ctx)
        elif app_id == AppDescriptionEnum.BUY_XIANZHOU_PARCEL.value.id:
            return BuyXianzhouParcelApp(ctx)
        elif app_id == AppDescriptionEnum.TRAILBLAZE_POWER.value.id:
            return TrailblazePower(ctx)
        elif app_id == AppDescriptionEnum.ECHO_OF_WAR.value.id:
            return EchoOfWarApp(ctx)
        elif app_id == AppDescriptionEnum.TREASURES_LIGHTWARD.value.id:
            return TreasuresLightwardApp(ctx)
        elif app_id == sim_universe_app.SIM_UNIVERSE.id:
            return sim_universe_app.SimUniverseApp(ctx)
        return None

    @staticmethod
    def get_app_run_record_by_id(app_id: str, ctx: Context) -> Optional[AppRunRecord]:
        if app_id == AppDescriptionEnum.WORLD_PATROL.value.id:
            return ctx.world_patrol_run_record
        elif app_id == AppDescriptionEnum.ASSIGNMENTS.value.id:
            return ctx.assignments_run_record
        elif app_id == EMAIL.id:
            return email_attachment.get_record()
        elif app_id == SUPPORT_CHARACTER.id:
            return support_character.get_record()
        elif app_id == NAMELESS_HONOR.id:
            return nameless_honor.get_record()
        elif app_id == AppDescriptionEnum.DAILY_TRAINING.value.id:
            return ctx.daily_training_run_record
        elif app_id == AppDescriptionEnum.BUY_XIANZHOU_PARCEL.value.id:
            return ctx.buy_xz_parcel_run_record
        elif app_id == AppDescriptionEnum.TRAILBLAZE_POWER.value.id:
            return ctx.tp_run_record
        elif app_id == AppDescriptionEnum.ECHO_OF_WAR.value.id:
            return ctx.echo_run_record
        elif app_id == AppDescriptionEnum.TREASURES_LIGHTWARD.value.id:
            return ctx.tl_run_record
        elif app_id == sim_universe_app.SIM_UNIVERSE.id:
            return sim_universe_app.get_record()
        return None

    @staticmethod
    def update_app_run_record_before_start(app_id: str, ctx: Context):
        """
        每次开始前 根据外部信息更新运行状态
        :param app_id:
        :return:
        """
        record: Optional[AppRunRecord] = OneStopService.get_app_run_record_by_id(app_id, ctx)
        if record is not None:
            record.check_and_update_status()
