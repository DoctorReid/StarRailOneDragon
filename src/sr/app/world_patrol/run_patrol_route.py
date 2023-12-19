from typing import List

import sr.const.operation_const
from basic import Point
from basic.i18_utils import gt
from basic.log_utils import log
from sr.app.world_patrol import WorldPatrolRouteId, WorldPatrolRoute
from sr.const import operation_const, map_const
from sr.context import Context
from sr.image.sceenshot import LargeMapInfo
from sr.operation import Operation
from sr.operation.combine import CombineOperation
from sr.operation.combine.transport import Transport
from sr.operation.unit.enter_auto_fight import EnterAutoFight
from sr.operation.unit.interact import Interact
from sr.operation.unit.move_directly import MoveDirectly
from sr.operation.unit.wait_in_seconds import WaitInSeconds
from sr.operation.unit.wait_in_world import WaitInWorld
from sr.operation.unit.use_recipe import UseRecipe


class RunPatrolRoute(CombineOperation):

    def __init__(self, ctx: Context, route_id: WorldPatrolRouteId):
        """
        运行一条锄地路线
        :param ctx:
        :param route_id: 路线ID
        """
        route: WorldPatrolRoute = WorldPatrolRoute(route_id)
        log.info('准备执行线路 %s', route_id.display_name)
        log.info('感谢以下人员提供本路线 %s', route.author_list)
        super().__init__(ctx, self.init_ops(ctx, route), op_name=gt('锄地路线 %s', 'ui') % route.display_name)

    def init_ops(self, ctx: Context, route: WorldPatrolRoute) -> List[Operation]:
        """
        执行这条路线的所有指令
        :param ctx:
        :param route: 路线实体
        :return:
        """
        ops: List[Operation] = []

        ops.append(Transport(ctx, route.tp))

        current_pos: Point = route.tp.tp_pos
        current_lm_info = ctx.ih.get_large_map(route.route_id.region)
        for i in range(len(route.route_list)):
            route_item = route.route_list[i]
            next_route_item = route.route_list[i + 1] if i + 1 < len(route.route_list) else None
            op: Operation = None
            if route_item['op'] in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]:
                op, next_pos, next_lm_info = self.move(ctx, route_item, next_route_item, current_pos, current_lm_info)
                current_pos = next_pos
                if next_lm_info is not None:
                    current_lm_info = next_lm_info
            elif route_item['op'] == operation_const.OP_PATROL:
                op = self.patrol(ctx)
            elif route_item['op'] == operation_const.OP_INTERACT:
                op = self.interact(ctx, route_item['data'])
            elif route_item['op'] == operation_const.OP_WAIT:
                op = self.wait(ctx, route_item['data'][0], float(route_item['data'][1]))
            elif route_item['op'] == operation_const.OP_UPDATE_POS:
                next_pos = Point(route_item['data'][0], route_item['data'][1])
                if len(route_item['data']) > 2:
                    next_region = map_const.region_with_another_floor(current_lm_info.region, route_item['data'][2])
                    current_lm_info = ctx.ih.get_large_map(next_region)
                current_pos = next_pos
            else:
                log.error('错误的锄大地指令 %s', route_item['op'])

            if op is not None:
                ops.append(op)
        
        new_ops = []
        for op in ops:
            # 比较粗糙，不打算优化了，在雅利洛使用秘技进入战斗，足够托帕使用
            # 托帕满级后也不会带托帕锄大地了
            if op.op_name == gt('进入战斗', 'ui') and route.route_id.planet.num == 2:
                new_ops.append(self.recipe(ctx))
            new_ops.append(op)
        return new_ops

    def move(self, ctx: Context, route_item, next_route_item,
             current_pos: Point, current_lm_info: LargeMapInfo):
        """
        移动到某个点
        :param ctx:
        :param route_item: 本次指令
        :param next_route_item: 下次指令
        :param current_pos: 当前位置
        :param current_lm_info: 当前楼层大地图信息
        :return:
        """
        target_pos = Point(route_item['data'][0], route_item['data'][1])
        next_lm_info = None
        if len(route_item['data']) > 2:  # 需要切换层数
            next_region = map_const.region_with_another_floor(current_lm_info.region, route_item['data'][2])
            next_lm_info = ctx.ih.get_large_map(next_region)

        stop_afterwards = next_route_item is None or next_route_item['op'] not in [operation_const.OP_MOVE,
                                                                                   operation_const.OP_SLOW_MOVE]
        no_run = route_item['op'] == operation_const.OP_SLOW_MOVE

        op = MoveDirectly(ctx, current_lm_info, next_lm_info=next_lm_info,
                          target=target_pos, start=current_pos,
                          stop_afterwards=stop_afterwards, no_run=no_run)

        return op, target_pos, next_lm_info

    def patrol(self, ctx: Context) -> Operation:
        """
        攻击
        :param ctx:
        :return:
        """
        return EnterAutoFight(ctx)

    def interact(self, ctx: Context, cn: str) -> Operation:
        """
        交互
        :param ctx:
        :param cn: 交互文本
        :return:
        """
        return Interact(ctx, cn)

    def wait(self, ctx: Context, wait_type: str, seconds: float) -> Operation:
        """
        等待
        :param ctx:
        :param wait_type: 等待类型
        :param seconds: 等待秒数
        :return:
        """
        op: Operation = None
        if wait_type == 'in_world':
            op = WaitInWorld(ctx, seconds)
        elif wait_type == sr.const.operation_const.WAIT_TYPE_SECONDS:
            op = WaitInSeconds(ctx, seconds)
        else:
            log.error('错误的wait类型 %s', wait_type)

        return op
    
    def recipe(self, ctx: Context) -> Operation:
        """
        使用秘技
        :param ctx:
        :return:
        """
        return UseRecipe(ctx)


if __name__ == '__main__':
    '''
    测试单条路线, 运行前需要校准
    '''
    from sr.context import get_context

    ctx = get_context()
    ctx.init_all(renew=True)
    ctx.controller.init()
    ctx.running = 1
    P02 = map_const.P02
    app = RunPatrolRoute(ctx=ctx, route_id=WorldPatrolRouteId(P02, "R12_JXJL_R01_TXZL"))
    app.execute()