from basic import Point
from basic.i18_utils import gt
from sr.const import map_const
from sr.const.traing_mission_const import MISSION_DESTRUCTIBLE_OBJECTS
from sr.context import Context
from sr.image.sceenshot import LargeMapInfo
from sr.operation.combine import CombineOperation
from sr.operation.combine.transport import Transport
from sr.operation.unit.world_patrol_battle import WorldPatrolEnterFight
from sr.operation.unit.move import MoveDirectly


class DestroyObjects(CombineOperation):

    def __init__(self, ctx: Context):
        """
        破坏3个可破坏物
        会传送到【空间站黑塔】-【支援舱段】-【月台】
        """
        tp = map_const.P01_R04_SP02
        lm_info: LargeMapInfo = ctx.ih.get_large_map(tp.region)

        ops = [
            Transport(ctx, tp),  # 传送
            MoveDirectly(ctx, lm_info, start=tp.tp_pos, target=Point(824, 405)),
            WorldPatrolEnterFight(ctx),
            MoveDirectly(ctx, lm_info, start=Point(824, 405), target=Point(730, 377)),
            WorldPatrolEnterFight(ctx),
            MoveDirectly(ctx, lm_info, start=Point(730, 377), target=Point(751, 373), stop_afterwards=False),
            MoveDirectly(ctx, lm_info, start=Point(751, 373), target=Point(733, 266)),
            WorldPatrolEnterFight(ctx),
        ]

        super().__init__(
            ctx, ops,
            op_name='%s %s' % (
                gt('每日实训', 'ui'),
                gt(MISSION_DESTRUCTIBLE_OBJECTS.id_cn, 'ui')
            )
        )
