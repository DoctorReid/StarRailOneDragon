from typing import List

from basic.i18_utils import gt
from sr.const.rogue_const import UNI_NUM_CN
from sr.context import Context
from sr.operation import StateOperation
from sr.operation.combine import StatusCombineOperation2, StatusCombineOperationEdge2


class RunSimUniNormalBattleLevel(StatusCombineOperation2):

    def __init__(self, ctx: Context, world_num: int, level: int):
        """
        模拟宇宙中 普通战斗楼层
        :param ctx:
        :param world_num: 第几宇宙
        :param level: 第几层
        """
        op_name = '%s %s %s %s' % (
            gt('模拟宇宙', 'ui'),
            gt('第%s世界' % UNI_NUM_CN[world_num], 'ui'),
            gt('第%d层' % level, 'ui'),
            gt('普通战斗', 'ui')
        )

        edges: List[StatusCombineOperationEdge2] = []

        super().__init__()
