import os

import cv2

import test
from basic import Point, cal_utils
from basic.log_utils import log
from sr import cal_pos, performance_recorder
from sr.cal_pos import VerifyPosInfo
from sr.context import get_context
from sr.image.image_holder import ImageHolder
from sr.image.sceenshot import mini_map, large_map
from test.sr.cal_pos.cal_pos_test_case import TestCase, read_test_cases


class TestCalPos(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

        ih = ImageHolder()
        # 预热 方便后续统计耗时
        ih.preheat_for_world_patrol()
        mini_map.preheat()

    @property
    def cases_path(self) -> str:
        return os.path.join(self.sub_package_path, 'test_cases.yml')

    def test_cal_pos(self):
        fail_cnt = 0
        self.cases = read_test_cases(self.cases_path)
        for case in self.cases:
            result = self.run_one_test_case(case, show=False)
            if not result:
                fail_cnt += 1
                log.info('%s 计算坐标失败', case.unique_id)

        performance_recorder.log_all_performance()
        self.assertEqual(0, fail_cnt)

    def run_one_test_case(self, case: TestCase, show: bool = False) -> bool:
        """
        执行一个测试样例
        :param case: 测试样例
        :param show: 显示
        :return: 是否与预期一致
        """
        ctx = get_context()
        ctx.init_image_matcher()

        mm = self.get_test_image_new(case.image_name)

        lm_info = ctx.ih.get_large_map(case.region)
        possible_pos = tuple(case.possible_pos)
        lm_rect = large_map.get_large_map_rect_by_pos(lm_info.gray.shape, mm.shape[:2], possible_pos)

        mm_info = mini_map.analyse_mini_map(mm)
        verify = VerifyPosInfo(last_pos=Point(case.possible_pos[0], case.possible_pos[1]),
                               max_distance=case.possible_pos[1])

        pos = cal_pos.cal_character_pos(ctx.im,
                                        lm_info=lm_info,
                                        mm_info=mm_info,
                                        running=case.running,
                                        real_move_time=case.real_move_time,
                                        lm_rect=lm_rect,
                                        retry_without_rect=False,
                                        show=show,
                                        verify=verify
                                        )
        if show:
            cv2.waitKey(0)

        if pos is None:
            log.error('%s 当前计算坐标为空', case.unique_id)
            return False
        else:
            dis = cal_utils.distance_between(pos.center, case.pos)
            log.info('%s 当前计算坐标为 %s 与目标点 %s 距离 %.2f', case.unique_id, pos.center, case.pos, dis)
            return dis < 5
