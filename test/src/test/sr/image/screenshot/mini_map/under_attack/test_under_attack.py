from typing import List

from cv2.typing import MatLike

import test
from basic import Point
from basic.img import cv2_utils, MatchResult, MatchResultList
from sr.context import get_context
from sr.image.sceenshot import mini_map


class TestMiniMapUnderAttack(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_under_attack(self):
        mm = self.get_test_image_new('under_1.png')
        self.assertTrue(mini_map.is_under_attack(mm, show=False, strict=False))

        mm = self.get_test_image_new('under_2.png')
        self.assertTrue(mini_map.is_under_attack(mm, show=False, strict=True))

        mm = self.get_test_image_new('under_3.png')
        self.assertFalse(mini_map.is_under_attack(mm, show=False))

        mm = self.get_test_image_new('under_4.png')
        self.assertFalse(mini_map.is_under_attack(mm, show=False, strict=True))

        mm = self.get_test_image_new('under_5.png')
        self.assertFalse(mini_map.is_under_attack(mm, show=False, strict=True))

    def test_under_attack_new(self):
        ctx = get_context()
        ctx.init_image_matcher()

        mm = self.get_test_image_new('under_1.png')
        mm_info = mini_map.analyse_mini_map(mm)
        self.assertFalse(mini_map.is_under_attack_new(mm_info, danger=True, enemy=True))

        mm = self.get_test_image_new('under_2.png')
        mm_info = mini_map.analyse_mini_map(mm)
        self.assertTrue(mini_map.is_under_attack_new(mm_info, danger=True, enemy=True))

        mm = self.get_test_image_new('under_3.png')
        mm_info = mini_map.analyse_mini_map(mm)
        self.assertFalse(mini_map.is_under_attack_new(mm_info, enemy=True))

        mm = self.get_test_image_new('under_4.png')
        mm_info = mini_map.analyse_mini_map(mm)
        self.assertFalse(mini_map.is_under_attack_new(mm_info, enemy=True))

        mm = self.get_test_image_new('under_5.png')
        mm_info = mini_map.analyse_mini_map(mm)
        self.assertFalse(mini_map.is_under_attack_new(mm_info, enemy=True))

        mm = self.get_test_image_new('under_6.png')
        mm_info = mini_map.analyse_mini_map(mm)
        self.assertTrue(mini_map.is_under_attack_new(mm_info, enemy=True))

