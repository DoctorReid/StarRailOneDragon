import test
from sr.app.world_patrol import load_all_route_id, WorldPatrolRoute
from sr.const import map_const, operation_const


class TestCalPosForSimUni(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_fix_route_after_map_record(self):
        """
        大地图重新绘制后 修改对应的路线
        :return:
        """
        region = map_const.P03_R07
        dx = 0
        dy = 10
        to_fix_op = [
            operation_const.OP_MOVE,
            operation_const.OP_SLOW_MOVE,
            operation_const.OP_NO_POS_MOVE,
            operation_const.OP_UPDATE_POS
        ]

        for floor in [-1, 0, 1, 2, 3]:
            floor_region = map_const.region_with_another_floor(region, floor)
            if floor_region is None:
                continue

            all_route_id_list = load_all_route_id()

            for route_id in all_route_id_list:
                route = WorldPatrolRoute(route_id)
                if route.tp.region != floor_region:
                    continue
                for route_item in route.route_list:
                    if route_item['op'] in to_fix_op:
                        route_item['data'][0] += dx
                        route_item['data'][1] += dy
                route.save()
