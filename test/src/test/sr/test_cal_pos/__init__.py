from typing import List

import cv2

import test
from basic import Point, cal_utils
from basic.img import MatchResult, cv2_utils
from basic.img.os import get_debug_image, save_debug_image
from basic.log_utils import log
from sr import cal_pos, performance_recorder
from sr.const import map_const
from sr.const.map_const import Region
from sr.context import get_context
from sr.image.sceenshot import mini_map, large_map


class TestCase:

    def __init__(self, region: Region, pos: Point, num: int, running: bool, possible_pos: tuple = None):
        self.region: Region = region
        self.pos: Point = pos
        self.num: int = num
        self.running: bool = running
        self.possible_pos: tuple = (*pos.tuple(), 25) if possible_pos is None else possible_pos

    @property
    def unique_id(self) -> str:
        return '%s_%02d' % (self.region.prl_id, self.num)

    @property
    def image_name(self) -> str:
        return '%s_%02d.png' % (self.region.prl_id, self.num)


standard_case_list: List[TestCase] = [
    TestCase(map_const.P01_R04_F2, Point(777, 388), 1, running=False, possible_pos=(804, 388, 30)),

    TestCase(map_const.P04_R05_F3, Point(585, 587), 1, running=False, possible_pos=(544, 594, 72))
]


class TestCalPos(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_cal_pos(self):
        fail_cnt = 0
        for case in standard_case_list:
            # if case.region != map_const.P02_R11_F1 and case.num != 1:
            #     continue
            result = self.run_one_test_case(case, show=False)
            if not result:
                fail_cnt += 1
                log.info('%s 计算坐标失败', case.unique_id)

        performance_recorder.log_all_performance()
        self.assertTrue(fail_cnt == 0)

    def test_init_case(self):
        ctx = get_context()
        screen = get_debug_image('_1708869998042')
        mm = mini_map.cut_mini_map(screen, ctx.game_config.mini_map_pos)
        for case in standard_case_list:
            if case.region != map_const.P01_R04_F2 and case.num != 1:
                continue
            self.save_test_image(mm, case.image_name)
            self.run_one_test_case(case, show=True)

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
        lm_rect = large_map.get_large_map_rect_by_pos(lm_info.gray.shape, mm.shape[:2], case.possible_pos)
        sp_map = map_const.get_sp_type_in_rect(lm_info.region, lm_rect)
        mm_info = mini_map.analyse_mini_map(mm, ctx.im, sp_types=set(sp_map.keys()))

        pos = cal_pos.sim_uni_cal_pos(ctx.im,
                                      lm_info=lm_info,
                                      mm_info=mm_info,
                                      possible_pos=case.possible_pos,
                                      running=case.running,
                                      lm_rect=lm_rect,
                                      show=show
                                      )
        if show:
            cv2.waitKey(0)

        log.info('%s 当前计算坐标为 %s', case.unique_id, pos)

        dis = cal_utils.distance_between(pos, case.pos)

        return dis < 5
