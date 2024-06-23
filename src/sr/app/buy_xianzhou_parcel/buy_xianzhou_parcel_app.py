from basic.i18_utils import gt
from sr.app.application_base import Application
from sr.const import map_const
from sr.context.context import Context
from sr.operation import StateOperationNode
from sr.operation.combine.transport import Transport
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus
from sr.operation.unit.interact import Interact, TalkInteract
from sr.operation.unit.move import MoveDirectly
from sr.operation.unit.store.buy_store_item import BuyStoreItem
from sr.operation.unit.store.click_store_item import ClickStoreItem


class BuyXianzhouParcelApp(Application):

    def __init__(self, ctx: Context):
        nodes = [
            StateOperationNode('返回大世界', op=BackToNormalWorldPlus(ctx)),
            StateOperationNode('传送', op=Transport(ctx, map_const.P03_R02_SP02)),
            StateOperationNode('移动',
                               op=MoveDirectly(
                                   ctx,
                                   lm_info=ctx.ih.get_large_map(map_const.P03_R02_SP02.region),
                                   target=map_const.P03_R02_SP08.lm_pos,
                                   start=map_const.P03_R02_SP02.tp_pos)
                               ),
            StateOperationNode('茂贞', op=Interact(ctx, '茂贞', single_line=True), wait_after_op=1),
            StateOperationNode('对话', op=TalkInteract(ctx, '我想买个过期邮包试试手气', lcs_percent=0.55),
                               wait_after_op=1),
            StateOperationNode('点击商品', op=ClickStoreItem(ctx, '逾期未取的贵重邮包', 0.8), wait_after_op=1),
            StateOperationNode('购买', op=BuyStoreItem(ctx, buy_max=True)),
            StateOperationNode('完成后返回大世界', op=BackToNormalWorldPlus(ctx)),
        ]

        super().__init__(ctx,
                         op_name=gt('购买过期邮包', 'ui'),
                         run_record=ctx.buy_xz_parcel_run_record,
                         nodes=nodes
                         )
