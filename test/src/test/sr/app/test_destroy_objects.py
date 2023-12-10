import unittest

import cv2

import test
from basic.img.os import get_debug_image
from sr import cal_pos
from sr.const import map_const
from sr.context import get_context
from sr.image.sceenshot import mini_map, LargeMapInfo, large_map
from sr.operation.combine.destory_objects import DestroyObjects


class TestDestroyObjects(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

        ctx = get_context()
        ctx.init_image_matcher()

        self.op = DestroyObjects(ctx)

    def test_move_pos(self):
        img_names = [
            '_1702196339303',
            '_1702196353099',
            '_1702196364335',
            '_1702196379532',
        ]

        lm_info: LargeMapInfo = self.op.ctx.ih.get_large_map(map_const.P01_R04_SP02.region)
        tp = map_const.P01_R04_SP02.lm_pos.tuple()
        possible_pos = (tp[0], tp[1], 200)
        im = self.op.ctx.im

        for idx in range(len(img_names)):
            screen = get_debug_image(img_names[idx])
            mm = mini_map.cut_mini_map(screen)
            path = self._get_test_image_path(str(idx + 1))

            cv2.imwrite(path, mm)

            lm_rect = large_map.get_large_map_rect_by_pos(lm_info.gray.shape, mm.shape[:2], possible_pos)

            sp_map = map_const.get_sp_type_in_rect(lm_info.region, lm_rect)
            mm_info = mini_map.analyse_mini_map(mm, im, sp_types=set(sp_map.keys()))
            result = cal_pos.cal_character_pos(im, lm_info, mm_info, lm_rect=lm_rect, show=True,
                                               retry_without_rect=False, running=False)
            print(result)