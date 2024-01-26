import unittest

import cv2

import test
from basic import Point
from basic.img import MatchResult, cv2_utils
from basic.img.os import get_debug_image
from basic.log_utils import log
from sr import cal_pos
from sr.const import map_const
from sr.context import get_context
from sr.image.sceenshot import mini_map, large_map


class TestCalPosForSimUni(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

    def test_for_debug(self):
        ctx = get_context()
        ctx.init_image_matcher()

        screen = get_debug_image('_1706279191929')
        mm = mini_map.cut_mini_map(screen)
        mm_info = mini_map.analyse_mini_map(mm, ctx.im)

        for _, region_list in map_const.PLANET_2_REGION.items():
            for region in region_list:
                if region != map_const.P02_R04:
                    continue
                lm_info = ctx.ih.get_large_map(region)
                pos: MatchResult = cal_pos.cal_character_pos_by_gray_2(ctx.im, lm_info, mm_info,
                                                                       scale_list=[1], match_threshold=0.3,
                                                                       show=True)
                log.info('匹配 %s 结果 %s', region.display_name, pos)
                if pos is not None:
                    cv2_utils.show_overlap(lm_info.origin, mm_info.origin, pos.left_top.x, pos.left_top.y, win_name='overlap')
                cv2.waitKey(0)

    def test_cal_for_debug(self):
        ctx = get_context()
        ctx.init_image_matcher()

        screen = get_debug_image('_1706279191929')
        mm = mini_map.cut_mini_map(screen)
        mm_info = mini_map.analyse_mini_map(mm, ctx.im)

        possible_pos = (272, 1272, 25)
        region = map_const.P02_R05
        lm_info = ctx.ih.get_large_map(region)
        lm_rect = large_map.get_large_map_rect_by_pos(lm_info.gray.shape, mm.shape[:2], possible_pos)
        pos: Point = cal_pos.cal_character_pos_for_sim_uni(ctx.im, lm_info, mm_info,
                                                           lm_rect=lm_rect, running=True,
                                                           show=True)
        log.info('匹配 %s 结果 %s', region.display_name, pos)
        cv2.waitKey(0)