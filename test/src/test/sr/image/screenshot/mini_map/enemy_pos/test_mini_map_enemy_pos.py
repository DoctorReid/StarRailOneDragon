from typing import List

from cv2.typing import MatLike

import test
from basic import Point
from basic.img import cv2_utils, MatchResult, MatchResultList
from sr.context.context import get_context
from sr.image.sceenshot import mini_map


class TestMiniMapEnemyPos(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_with_enemy_nearby(self):
        ctx = get_context()
        ctx.init_image_matcher()

        mm = self.get_test_image_new('mm_no_enemy.png')
        self.assertFalse(mini_map.with_enemy_nearby(mm))

    def test_get_enemy_pos(self):
        ctx = get_context()
        ctx.init_image_matcher()

        mm = self.get_test_image_new('enemy_pos_1.png')
        mm_info = mini_map.analyse_mini_map(mm)
        pos_list = mini_map.get_enemy_pos(mm_info)
        print(pos_list)
        self.assertEquals(1, len(pos_list))
        # self.show_enemy_pos(mm, pos_list)

        mm = self.get_test_image_new('enemy_pos_2.png')
        mm_info = mini_map.analyse_mini_map(mm)
        pos_list = mini_map.get_enemy_pos(mm_info)
        print(pos_list)
        self.assertEquals(2, len(pos_list))

        mm = self.get_test_image_new('enemy_pos_3.png')
        mm_info = mini_map.analyse_mini_map(mm)
        pos_list = mini_map.get_enemy_pos(mm_info)
        print(pos_list)
        self.assertEquals(1, len(pos_list))

    def show_enemy_pos(self, mm: MatLike, pos_list: List[Point]):
        cx = mm.shape[1] // 2
        cy = mm.shape[0] // 2
        mrl = MatchResultList(only_best=False)
        for pos in pos_list:
            mrl.append(MatchResult(1, cx + pos.x - 3, cy + pos.y - 3, 7, 7))

        cv2_utils.show_image(mm, mrl, win_name='show_enemy_pos', wait=0)