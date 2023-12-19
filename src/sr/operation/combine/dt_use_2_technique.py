from typing import List

from basic.i18_utils import gt
from sr.const.traing_mission_const import MISSION_USE_TECHNIQUE
from sr.context import Context
from sr.operation import Operation, OperationFail
from sr.operation.combine import StatusCombineOperation, StatusCombineOperationEdge
from sr.operation.unit.back_to_world import BackToWorld
from sr.operation.unit.check_technique_point import CheckTechniquePoint
from sr.operation.unit.use_technique import UseTechnique
from sr.operation.unit.wait_in_seconds import WaitInSeconds


class Use2Technique(StatusCombineOperation):

    def __init__(self, ctx: Context):
        """
        每日实训 - 累次使用2次秘技
        :param ctx: 上下文
        """
        ops: List[Operation] = []
        edges: List[StatusCombineOperationEdge] = []

        back = BackToWorld(ctx)  # 回到大世界界面
        ops.append(back)

        check = CheckTechniquePoint(ctx)  # 检测秘技点数
        ops.append(check)
        edges.append(StatusCombineOperationEdge(back, check))

        fail = OperationFail(ctx)  # 失败结束
        ops.append(fail)
        edges.append(StatusCombineOperationEdge(check, fail, status='0'))
        edges.append(StatusCombineOperationEdge(check, fail, status='1'))

        use1 = UseTechnique(ctx)  # 使用秘技1
        ops.append(use1)
        edges.append(StatusCombineOperationEdge(check, use1, ignore_status=True))

        wait = WaitInSeconds(ctx, 2)  # 略作等待
        ops.append(wait)
        edges.append(StatusCombineOperationEdge(use1, wait))

        use2 = UseTechnique(ctx)  # 使用秘技2
        ops.append(use2)
        edges.append(StatusCombineOperationEdge(wait, use2))

        super().__init__(ctx, ops, edges,
                         op_name='%s %s' % (gt('实训任务', 'ui'), gt(MISSION_USE_TECHNIQUE.id_cn, 'ui'))
                         )
