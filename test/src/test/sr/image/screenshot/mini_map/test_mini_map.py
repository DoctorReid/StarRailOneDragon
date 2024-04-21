from typing import Optional

import test
from basic.img.os import get_debug_image
from sr.context import get_context, Context
from sr.image.sceenshot import mini_map


class TestMiniMap(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

        ctx = get_context()

    def test_with_enemy_nearby(self):
        ctx = get_context()
        ctx.init_image_matcher()

        mm = self.get_test_image_new('mm_no_enemy.png')
        self.assertFalse(mini_map.with_enemy_nearby(mm))

    def test_get_enemy_pos(self):
        ctx = get_context()
        ctx.init_image_matcher()

        mm = self.get_test_image_new('enemy_pos_1.png')
        mm_info = mini_map.analyse_mini_map(mm, ctx.im)
        pos_list = mini_map.get_enemy_pos(mm_info)
        print(pos_list)
        self.assertTrue(len(pos_list) > 0)
