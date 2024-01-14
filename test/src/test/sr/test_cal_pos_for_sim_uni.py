import unittest

import cv2

import test
from basic.img import MatchResult, cv2_utils
from basic.img.os import get_debug_image
from sr import cal_pos
from sr.const import map_const
from sr.context import get_context
from sr.image.sceenshot import mini_map


class TestCalPosForSimUni(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

    def test_for_debug(self):
        ctx = get_context()
        ctx.init_image_matcher()

        screen = get_debug_image('_1705217147030')
        mm = mini_map.cut_mini_map(screen)
        mm_info = mini_map.analyse_mini_map(mm, ctx.im)

        for _, region_list in map_const.PLANET_2_REGION.items():
            for region in region_list:
                if region.planet != map_const.P02:
                    continue
                lm_info = ctx.ih.get_large_map(region)
                pos: MatchResult = cal_pos.cal_character_pos_by_gray_2(ctx.im, lm_info, mm_info,
                                                                       scale_list=[1], match_threshold=0.5,
                                                                       show=True)
                if pos is not None:
                    cv2_utils.show_overlap(lm_info.origin, mm_info.origin, pos.left_top.x, pos.left_top.y, win_name='overlap')
                cv2.waitKey(0)
