import cv2
from typing import Tuple

from one_dragon.base.geometry.point import Point
from sr_od.app.world_patrol.world_patrol_route import WorldPatrolRoute, WorldPatrolRouteOperation
from sr_od.config import operation_const
from sr_od.context.sr_context import SrContext
from sr_od.sr_map.sr_map_def import Region


def can_change_tp(route: WorldPatrolRoute) -> bool:
    """
    当前是否允许修改传送点
    :param route:
    :return:
    """
    return route is None or route.empty_op


def get_last_pos(ctx: SrContext, route: WorldPatrolRoute) -> Tuple[Region, Point]:
    """
    获取路线的最后一个点
    :param ctx: 上下文
    :param route: 路线
    :return:
    """
    region = route.tp.region
    pos = route.tp.tp_pos
    if route.route_list is None or len(route.route_list) == 0:
        return region, pos
    for op in route.route_list:
        if op.op in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE, operation_const.OP_UPDATE_POS]:
            pos = Point(op.data[0], op.data[1])
            if len(op.data) > 2:
                region = ctx.map_data.region_with_another_floor(region, op.data[2])
        elif op.op == operation_const.OP_ENTER_SUB:
            region = ctx.map_data.get_sub_region_by_cn(region, op.data[0], int(op.data[1]))
            pos = None

    return region, pos


def get_route_image(ctx: SrContext, route: WorldPatrolRoute):
    """
    获取路线的图片
    :param ctx: 上下文
    :param route: 路线 在传送点还没有选的时候 可能为空
    :return:
    """
    last_region, _ = get_last_pos(ctx, route)

    display_image = ctx.map_data.get_large_map_info(last_region).raw.copy()

    last_point = None
    if route.tp is not None:
        last_point = route.tp.tp_pos.tuple()
        cv2.circle(display_image, route.tp.lm_pos.tuple(), 15, color=(100, 255, 100), thickness=2)
        cv2.circle(display_image, route.tp.tp_pos.tuple(), 5, color=(0, 255, 0), thickness=2)
    for route_item in route.route_list:
        if route_item.op in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]:
            pos = route_item.data
            cv2.circle(display_image, pos[:2], 5, color=(0, 0, 255), thickness=-1)
            if last_point is not None:
                cv2.line(display_image, last_point[:2], pos[:2],
                         color=(255, 0, 0) if route_item.op == operation_const.OP_MOVE else (255, 255, 0),
                         thickness=2)
            cv2.putText(display_image, str(route_item.idx), (pos[0] - 5, pos[1] - 13),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1, cv2.LINE_AA)
            last_point = pos
        elif route_item.op == operation_const.OP_PATROL:
            if last_point is not None:
                cv2.circle(display_image, last_point[:2], 10, color=(0, 255, 255), thickness=2)
        elif route_item.op == operation_const.OP_DISPOSABLE:
            if last_point is not None:
                cv2.circle(display_image, last_point[:2], 10, color=(67, 34, 49), thickness=2)
        elif route_item.op == operation_const.OP_INTERACT or route_item.op == operation_const.OP_CATAPULT:
            if last_point is not None:
                cv2.circle(display_image, last_point[:2], 12, color=(255, 0, 255), thickness=2)
        elif route_item.op == operation_const.OP_WAIT:
            if last_point is not None:
                cv2.circle(display_image, last_point[:2], 14, color=(255, 255, 255), thickness=2)
        elif route_item.op == operation_const.OP_UPDATE_POS:
            pos = route_item.data
            cv2.circle(display_image, pos[:2], 5, color=(0, 0, 255), thickness=-1)
            cv2.putText(display_image, str(route_item.idx), (pos[0] - 5, pos[1] - 13),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1, cv2.LINE_AA)
            last_point = pos
        elif route_item.op == operation_const.OP_ENTER_SUB:
            last_region = ctx.map_data.get_sub_region_by_cn(cn=route_item.data[0], region=last_region, floor=int(route_item.data[1]))
            display_image = ctx.map_data.get_large_map_info(last_region).raw.copy()

    return display_image


def add_move(ctx: SrContext, route: WorldPatrolRoute, x: int, y: int, floor: int):
    """
    在最后添加一个移动的指令
    :param x: 横坐标
    :param y: 纵坐标
    :param floor: 楼层
    :return:
    """
    last_region, last_pos = get_last_pos(ctx, route)

    if last_region.floor == floor:
        to_add = WorldPatrolRouteOperation(op=operation_const.OP_MOVE, data=(x, y))
    else:
        to_add = WorldPatrolRouteOperation(op=operation_const.OP_MOVE, data=(x, y, floor))

    route.route_list.append(to_add)
    route.init_idx()


def pop_last(route: WorldPatrolRoute):
    """
    取消最后一个指令
    :return:
    """
    if len(route.route_list) > 0:
        route.route_list.pop()


def mark_last_move_as_slow(route: WorldPatrolRoute):
    """
    将最后一个移动标记成慢走 或从慢走标记成可疾跑
    :return:
    """
    if route.empty_op:
        return

    last_op = route.route_list[len(route.route_list) - 1]
    if last_op.op not in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]:
        return

    if last_op.op == operation_const.OP_MOVE:
        last_op.op = operation_const.OP_SLOW_MOVE
    else:
        last_op.op = operation_const.OP_MOVE


def mark_last_move_as_update(route: WorldPatrolRoute):
    """
    将最后一个指令变更为更新位置
    :return:
    """
    if route.empty_op:
        return

    idx = len(route.route_list) - 1
    if route.route_list[idx].op in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]:
        route.route_list[idx].op = operation_const.OP_UPDATE_POS
