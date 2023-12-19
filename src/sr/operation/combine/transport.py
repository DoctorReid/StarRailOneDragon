from typing import List

from basic.i18_utils import gt
from basic.log_utils import log
from sr.const.map_const import TransportPoint
from sr.context import Context
from sr.operation import Operation, OperationResult
from sr.operation.combine import CombineOperation
from sr.operation.unit.choose_planet import ChoosePlanet
from sr.operation.unit.choose_region import ChooseRegion
from sr.operation.unit.choose_transport_point import ChooseTransportPoint
from sr.operation.unit.open_map import OpenMap
from sr.operation.unit.scale_large_map import ScaleLargeMap
from sr.operation.unit.wait_in_world import WaitInWorld


class Transport(CombineOperation):

    def __init__(self, ctx: Context, tp: TransportPoint):
        """
        :param ctx: 上下文
        :param tp: 传送点
        """
        ops: List[Operation] = []
        ops.append(OpenMap(ctx))
        if ctx.first_transport:
            ops.append(ScaleLargeMap(ctx, -5))
        ops.append(ChoosePlanet(ctx, tp.region.planet))
        ops.append(ChooseRegion(ctx, tp.region))
        ops.append(ChooseTransportPoint(ctx, tp))
        ops.append(WaitInWorld(ctx, 100))  # 传送部分加大超时限制 防止部分极低配置机型无法在限定时间内完成加载

        super().__init__(ctx, ops,
                         op_name=gt('传送 %s %s %s', 'ui') % (tp.planet.display_name, tp.region.display_name, tp.display_name))

    def _after_operation_done(self, result: OperationResult):
        """
        动作结算后的处理
        :param result:
        :return:
        """
        Operation._after_operation_done(self, result)
        if result.success:
            self.ctx.first_transport = False  # 后续传送不用缩放地图了
