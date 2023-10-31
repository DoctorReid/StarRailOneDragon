from basic.i18_utils import gt
from basic.log_utils import log
from sr.const.map_const import TransportPoint, Region, Planet
from sr.context import Context
from sr.operation import Operation
from sr.operation.unit.choose_planet import ChoosePlanet
from sr.operation.unit.choose_region import ChooseRegion
from sr.operation.unit.choose_transport_point import ChooseTransportPoint
from sr.operation.unit.open_map import OpenMap
from sr.operation.unit.scale_large_map import ScaleLargeMap
from sr.operation.unit.wait_in_world import WaitInWorld


class Transport(Operation):

    def __init__(self, ctx: Context, tp: TransportPoint, first: bool = True):
        """
        :param ctx:
        :param tp:
        :param first: 是否第一次传送
        """
        self.ops = []
        self.ops.append(OpenMap(ctx))
        if first:
            self.ops.append(ScaleLargeMap(ctx, -5))
        self.ops.append(ChoosePlanet(ctx, tp.region.planet))
        self.ops.append(ChooseRegion(ctx, tp.region))
        self.ops.append(ChooseTransportPoint(ctx, tp))
        self.ops.append(WaitInWorld(ctx))

        super().__init__(ctx, len(self.ops))
        self.tp: TransportPoint = tp
        self.region: Region = self.tp.region
        self.planet: Planet = self.region.planet

        log.info('准备传送 %s %s %s', gt(self.planet.cn, 'ui'), gt(self.region.cn, 'ui'), gt(self.tp.cn, 'ui'))

    def run(self) -> int:
        r = self.ops[self.op_round - 1].execute()
        if not r:
            return Operation.FAIL

        return Operation.SUCCESS if self.op_round == len(self.ops) else Operation.RETRY
