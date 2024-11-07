def draw_route_in_image(ctx: SrContext, region: Region, route: WorldPatrolRoute):
    """
    画一个
    :param ctx:
    :param region: 区域
    :param route: 路线 在传送点还没有选的时候 可能为空
    :return:
    """
    last_region = region

    if route is not None:
        last_region, _ = route.last_pos

    display_image = ctx.ih.get_large_map(last_region).origin.copy()

    if route is None:
        return display_image

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
            last_region = get_sub_region_by_cn(cn=route_item.data[0], region=region, floor=int(route_item.data[1]))
            display_image = ctx.ih.get_large_map(last_region).origin.copy()

    return display_image