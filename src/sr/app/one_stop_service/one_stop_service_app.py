from typing import List, Optional, ClassVar

from basic.i18_utils import gt
from sr.app.app_description import AppDescriptionEnum
from sr.app.app_run_record import AppRunRecord
from sr.app.application_base import Application
from sr.app.assignments.assignments_app import AssignmentsApp
from sr.app.buy_xianzhou_parcel.buy_xianzhou_parcel_app import BuyXianzhouParcelApp
from sr.app.claim_email.email_app import EmailApp
from sr.app.daily_training.daily_training_app import DailyTrainingApp
from sr.app.echo_of_war.echo_of_war_app import EchoOfWarApp
from sr.app.mys.mys_app import MysApp
from sr.app.nameless_honor.nameless_honor_app import NamelessHonorApp
from sr.app.sim_uni.sim_uni_app import SimUniApp
from sr.app.support_character.support_character_app import SupportCharacterApp
from sr.app.trailblaze_power.trailblaze_power_app import TrailblazePower
from sr.app.treasures_lightward.treasures_lightward_app import TreasuresLightwardApp
from sr.app.world_patrol.world_patrol_app import WorldPatrol
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult, StateOperationEdge, StateOperationNode
from sr.operation.unit.enter_game import LoginWithAnotherAccount


class OneStopServiceApp(Application):

    STATUS_ACCOUNT_FINISHED: ClassVar[str] = '所有账号已完成'
    STATUS_ACCOUNT_APP_FINISHED: ClassVar[str] = '当前账号所有应用已完成'

    def __init__(self, ctx: Context):
        edges: List[StateOperationEdge] = []

        init_account = StateOperationNode('初始化账号列表', self._init_account_order)

        next_account = StateOperationNode('切换账号运行', self._next_account)
        edges.append(StateOperationEdge(init_account, next_account))

        next_app = StateOperationNode('运行应用', self._run_app_in_current_account)
        edges.append(StateOperationEdge(next_account, next_app, ignore_status=True))
        edges.append(StateOperationEdge(next_app, next_account, status=OneStopServiceApp.STATUS_ACCOUNT_APP_FINISHED))
        edges.append(StateOperationEdge(next_app, next_app, ignore_status=True))
        edges.append(StateOperationEdge(next_app, next_app, success=False))  # 失败的时候也继续下一个应用

        back = StateOperationNode('切换原启用账号', self._switch_original_account)
        edges.append(StateOperationEdge(next_account, back, status=OneStopServiceApp.STATUS_ACCOUNT_FINISHED))

        super().__init__(ctx, op_name=gt('一条龙', 'ui'),
                         edges=edges)

        self.account_idx_list: Optional[List[int]] = None  # 需要运行的账号
        self.original_account_idx: Optional[int] = None  # 最初启用的账号
        self.current_account_idx: Optional[int] = None  # 当前运行的账号
        self.current_app_id: Optional[str] = None  # 当前运行的应用ID

    def _init_before_execute(self):
        super()._init_before_execute()
        self.account_idx_list = None
        self.original_account_idx = None
        self.current_account_idx = None
        self.current_app_id = None

    def _init_account_order(self) -> OperationOneRoundResult:
        """
        初始化需要运行一条龙的账号列表
        :return:
        """
        self.account_idx_list = []

        for account in self.ctx.one_dragon_config.account_list:
            if account.active:
                self.account_idx_list.append(account.idx)
                self.original_account_idx = account.idx
                break

        for account in self.ctx.one_dragon_config.account_list:
            if not account.active and account.active_in_od:
                self.account_idx_list.append(account.idx)

        return self.round_success()

    def _next_account(self):
        """
        选择下一个启用的账号
        :return:
        """
        next_account_idx = self._get_next_account_idx()

        if self.current_account_idx is None and next_account_idx is None:
            return self.round_retry('未找到可运行账号')

        if next_account_idx is None:
            return self.round_success(OneStopServiceApp.STATUS_ACCOUNT_FINISHED)

        self.current_account_idx = next_account_idx
        self.current_app_id = None

        if self.ctx.one_dragon_config.current_active_account.idx != next_account_idx:
            self.ctx.active_account(self.current_account_idx)
            op = LoginWithAnotherAccount(self.ctx)
            return self.round_by_op(op.execute())

        return self.round_success()

    def _get_next_account_idx(self) -> Optional[int]:
        """
        获取下一个启用的账号ID
        :return:
        """
        next_account_idx: Optional[int] = None
        if self.current_account_idx is None:
            next_account_idx = self.original_account_idx
        else:
            after_current: bool = False
            for account_idx in self.account_idx_list:
                if account_idx == self.current_account_idx:
                    after_current = True
                    continue
                if after_current:
                    next_account_idx = account_idx
                    break

        return next_account_idx

    def _run_app_in_current_account(self):
        """
        运行账号对应的应用
        :return:
        """
        next_app_id = self._get_next_app_id()

        if self.current_app_id is None and next_app_id is None:
            return self.round_retry('未找到可运行的应用')

        if next_app_id is None:
            return self.round_success(OneStopServiceApp.STATUS_ACCOUNT_APP_FINISHED)

        self.current_app_id = next_app_id
        record = OneStopServiceApp.get_app_run_record_by_id(self.current_app_id, self.ctx)
        if record.run_status_under_now == AppRunRecord.STATUS_SUCCESS:
            return self.round_success()

        OneStopServiceApp.update_app_run_record_before_start(self.current_app_id, self.ctx)
        app: Application = self.get_app_by_id(self.current_app_id, self.ctx)

        if app is None:
            return self.round_retry('非法的app_id %s' % self.current_app_id)

        app.init_context_before_start = False  # 一条龙开始时已经初始化了
        app.stop_context_after_stop = False

        return self.round_by_op(app.execute())

    def _get_next_app_id(self) -> Optional[str]:
        """
        获取下一个要运行的应用ID
        :return:
        """
        next_app_id: Optional[str] = None
        if self.current_account_idx is None:
            return None

        run_app_list = self.ctx.one_stop_service_config.run_app_id_list
        after_current_app: bool = False
        for app_id in self.ctx.one_stop_service_config.order_app_id_list:
            if app_id not in run_app_list:
                continue
            if self.current_app_id is not None and self.current_app_id == app_id:
                after_current_app = True
                continue
            if self.current_app_id is None or after_current_app:
                record = OneStopServiceApp.get_app_run_record_by_id(app_id, self.ctx)
                if record.run_status_under_now == AppRunRecord.STATUS_SUCCESS:
                    continue
                next_app_id = app_id
                break

        return next_app_id

    def _switch_original_account(self) -> OperationOneRoundResult:
        """
        切换回原来启用的账号
        :return:
        """
        if self.original_account_idx is not None:
            self.ctx.active_account(self.original_account_idx)

            if self.original_account_idx != self.current_account_idx:
                op = LoginWithAnotherAccount(self.ctx)
                return self.round_by_op(op.execute())

        return self.round_success()

    @property
    def current_execution_desc(self) -> str:
        """
        当前运行的描述 用于UI展示
        :return:
        """
        if self.current_app_id is None:
            return gt('无', 'ui')
        else:
            app_desc = AppDescriptionEnum[self.current_app_id.upper()]
            return gt(app_desc.value.cn, 'ui')

    @property
    def next_execution_desc(self) -> str:
        """
        下一步运行的描述 用于UI展示
        :return:
        """
        next_app_id = self._get_next_app_id()
        if next_app_id is None:
            return gt('无', 'ui')
        else:
            app_desc = AppDescriptionEnum[next_app_id.upper()]
            return gt(app_desc.value.cn, 'ui')

    @staticmethod
    def get_app_by_id(app_id: str, ctx: Context) -> Optional[Application]:
        if app_id == AppDescriptionEnum.WORLD_PATROL.value.id:
            return WorldPatrol(ctx)
        elif app_id == AppDescriptionEnum.ASSIGNMENTS.value.id:
            return AssignmentsApp(ctx)
        elif app_id == AppDescriptionEnum.EMAIL.value.id:
            return EmailApp(ctx)
        elif app_id == AppDescriptionEnum.SUPPORT_CHARACTER.value.id:
            return SupportCharacterApp(ctx)
        elif app_id == AppDescriptionEnum.NAMELESS_HONOR.value.id:
            return NamelessHonorApp(ctx)
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
        elif app_id == AppDescriptionEnum.SIM_UNIVERSE.value.id:
            return SimUniApp(ctx)
        elif app_id == AppDescriptionEnum.MYS.value.id:
            return MysApp(ctx)
        return None

    @staticmethod
    def get_app_run_record_by_id(app_id: str, ctx: Context) -> Optional[AppRunRecord]:
        if app_id == AppDescriptionEnum.WORLD_PATROL.value.id:
            return ctx.world_patrol_run_record
        elif app_id == AppDescriptionEnum.ASSIGNMENTS.value.id:
            return ctx.assignments_run_record
        elif app_id == AppDescriptionEnum.EMAIL.value.id:
            return ctx.email_run_record
        elif app_id == AppDescriptionEnum.SUPPORT_CHARACTER.value.id:
            return ctx.support_character_run_record
        elif app_id == AppDescriptionEnum.NAMELESS_HONOR.value.id:
            return ctx.nameless_honor_run_record
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
        elif app_id == AppDescriptionEnum.SIM_UNIVERSE.value.id:
            return ctx.sim_uni_run_record
        elif app_id == AppDescriptionEnum.MYS.value.id:
            return ctx.mys_run_record
        return None

    @staticmethod
    def update_app_run_record_before_start(app_id: str, ctx: Context):
        """
        每次开始前 根据外部信息更新运行状态
        :param app_id:
        :return:
        """
        record: Optional[AppRunRecord] = OneStopServiceApp.get_app_run_record_by_id(app_id, ctx)
        if record is not None:
            record.check_and_update_status()
