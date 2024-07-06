from typing import Optional

from basic.i18_utils import gt
from sr.const import map_const
from sr.const.map_const import TransportPoint
from sr.context.context import Context
from sr.operation import StateOperation, StateOperationNode
from sr.operation.combine.transport import Transport
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus


class TransportToRecover(StateOperation):

    def __init__(self, ctx: Context, tp: Optional[TransportPoint] = None):
        """
        到一个传送点恢复
        :param ctx: 上下文
        :param tp: 当前传送点
        """
        self.tp: TransportPoint = map_const.P01_R01_SP02
        if tp is not None:  # 如果已经当前传送点 就找一个近的恢复
            nearby_list = map_const.REGION_2_SP.get(tp.region.pr_id, [])
            if len(nearby_list) > 0:
                for tp2 in nearby_list:
                    if tp2.region == tp.region and tp2.template_id == self.tp.template_id:
                        self.tp = tp2
                        break

        super().__init__(ctx,
                         op_name='%s %s %s %s' % (
                             gt('传送恢复', 'ui'),
                             self.tp.planet.display_name,
                             self.tp.region.display_name,
                             self.tp.display_name
                         ))

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        _back = StateOperationNode('返回大世界', op=BackToNormalWorldPlus(self.ctx))
        _tp = StateOperationNode('传送', op=Transport(self.ctx, self.tp))
        self.add_edge(_back, _tp)
