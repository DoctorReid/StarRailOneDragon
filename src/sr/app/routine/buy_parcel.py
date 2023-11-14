from typing import Optional

from basic import Point
from basic.i18_utils import gt
from sr.app import Application, AppRunRecord, app_const
from sr.config import game_config
from sr.const import game_config_const, map_const
from sr.context import Context
from sr.operation import Operation
from sr.operation.combine import CombineOperation
from sr.operation.combine.transport import Transport
from sr.operation.unit.back_to_world import BackToWorld
from sr.operation.unit.interact import Interact, TalkInteract
from sr.operation.unit.move_directly import MoveDirectly
from sr.operation.unit.store.buy_store_item import BuyStoreItem
from sr.operation.unit.store.click_store_item import ClickStoreItem
from sr.operation.unit.wait_in_seconds import WaitInSeconds


class BuyParcelRecord(AppRunRecord):

    def __init__(self):
        super().__init__(app_const.BUY_XIANZHOU_PARCEL.id)


buy_parcel_record: Optional[BuyParcelRecord] = None


def get_record() -> BuyParcelRecord:
    global buy_parcel_record
    if buy_parcel_record is None:
        buy_parcel_record = BuyParcelRecord()
    return buy_parcel_record


class BuyXianzhouParcel(Application):

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('购买过期包裹', 'ui'))

    def _execute_one_round(self) -> int:
        ops = [
            Transport(self.ctx, map_const.P03_R02_SP02),
            MoveDirectly(self.ctx,
                         lm_info=self.ctx.ih.get_large_map(map_const.P03_R02_SP02.region),
                         target=Point(390, 780),
                         start=map_const.P03_R02_SP02.tp_pos),
            Interact(self.ctx, '茂贞'),
            TalkInteract(self.ctx, '我想买个过期邮包试试手气', lcs_percent=0.55),
            WaitInSeconds(self.ctx, 1),
            ClickStoreItem(self.ctx, '逾期未取的贵重邮包', 0.8),
            WaitInSeconds(self.ctx, 1),
            BuyStoreItem(self.ctx, buy_max=True),
            BackToWorld(self.ctx)
        ]

        op = CombineOperation(self.ctx, ops=ops,
                              op_name=gt('购买过期包裹', 'ui'))

        if op.execute():
            return Operation.SUCCESS
        else:
            return Operation.FAIL

    def get_item_name_lcs_percent(self) -> 0.8:
        lang = game_config.get().lang
        if lang == game_config_const.LANG_CN:
            return 0.8
        elif lang == game_config_const.LANG_EN:
            return 0.8
        return 0.8

    def _after_stop(self, result: bool):
        get_record().update_status(AppRunRecord.STATUS_SUCCESS if result else AppRunRecord.STATUS_FAIL)
