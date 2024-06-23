from typing import List

from basic.i18_utils import gt
from sr.const.map_const import TransportPoint
from sr.context.context import Context
from sr.operation import Operation
from sr.operation.combine import CombineOperation
from sr.operation.unit.op_map import ChoosePlanet, ChooseRegion, ChooseTransportPoint
from sr.operation.unit.open_map import OpenMap
from sr.operation.unit.wait import WaitInWorld


class Transport(CombineOperation):

    def __init__(self, ctx: Context, tp: TransportPoint):
        """
        :param ctx: 上下文
        :param tp: 传送点
        """
        ops: List[Operation] = []
        ops.append(OpenMap(ctx))
        ops.append(ChoosePlanet(ctx, tp.region.planet))
        ops.append(ChooseRegion(ctx, tp.region))
        ops.append(ChooseTransportPoint(ctx, tp))
        ops.append(WaitInWorld(ctx, 100))  # 传送部分加大超时限制 防止部分极低配置机型无法在限定时间内完成加载

        super().__init__(ctx, ops,
                         op_name=gt('传送 %s %s %s', 'ui') % (tp.planet.display_name, tp.region.display_name, tp.display_name))
