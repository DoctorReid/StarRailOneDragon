from typing import Optional

from basic import os_utils
from basic.i18_utils import gt
from sr.app import Application, AppRunRecord, AppDescription, register_app
from sr.const import game_config_const, map_const
from sr.context import Context
from sr.operation import Operation
from sr.operation.combine import CombineOperation
from sr.operation.combine.transport import Transport
from sr.operation.unit.back_to_world import BackToWorld
from sr.operation.unit.interact import Interact, TalkInteract
from sr.operation.unit.move import MoveDirectly
from sr.operation.unit.store.buy_store_item import BuyStoreItem
from sr.operation.unit.store.click_store_item import ClickStoreItem
from sr.operation.unit.wait import WaitInSeconds

BUY_XIANZHOU_PARCEL = AppDescription(cn='过期邮包', id='buy_xianzhou_parcel')
register_app(BUY_XIANZHOU_PARCEL)


class BuyParcelRecord(AppRunRecord):

    def __init__(self):
        super().__init__(BUY_XIANZHOU_PARCEL.id)

    def _should_reset_by_dt(self) -> bool:
        """
        根据时间判断是否应该重置状态 每周重置一次
        :return:
        """
        current_dt = self.get_current_dt()
        sunday_dt = os_utils.get_sunday_dt(self.dt)
        return current_dt > sunday_dt

    @property
    def run_status_under_now(self):
        """
        基于当前时间显示的运行状态
        :return:
        """
        current_dt = self.get_current_dt()
        sunday_dt = os_utils.get_sunday_dt(self.dt)
        if current_dt > sunday_dt:
            return AppRunRecord.STATUS_WAIT
        else:
            return self.run_status


buy_parcel_record: Optional[BuyParcelRecord] = None


def get_record() -> BuyParcelRecord:
    global buy_parcel_record
    if buy_parcel_record is None:
        buy_parcel_record = BuyParcelRecord()
    return buy_parcel_record


class BuyXianzhouParcel(Application):

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('购买过期邮包', 'ui'),
                         run_record=get_record())

    def _execute_one_round(self) -> int:
        ops = [
            Transport(self.ctx, map_const.P03_R02_SP02),
            MoveDirectly(self.ctx,
                         lm_info=self.ctx.ih.get_large_map(map_const.P03_R02_SP02.region),
                         target=map_const.P03_R02_SP08.lm_pos,
                         start=map_const.P03_R02_SP02.tp_pos),
            Interact(self.ctx, '茂贞', single_line=True),
            TalkInteract(self.ctx, '我想买个过期邮包试试手气', lcs_percent=0.55),
            WaitInSeconds(self.ctx, 1),
            ClickStoreItem(self.ctx, '逾期未取的贵重邮包', 0.8),
            WaitInSeconds(self.ctx, 1),
            BuyStoreItem(self.ctx, buy_max=True),
            BackToWorld(self.ctx)
        ]

        op = CombineOperation(self.ctx, ops=ops,
                              op_name=gt('购买过期包裹', 'ui'))

        if op.execute().success:
            return Operation.SUCCESS
        else:
            return Operation.FAIL

    def get_item_name_lcs_percent(self) -> float:
        lang = self.ctx.game_config.lang
        if lang == game_config_const.LANG_CN:
            return 0.8
        elif lang == game_config_const.LANG_EN:
            return 0.8
        return 0.8
