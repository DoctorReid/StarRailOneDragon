import unittest

import test
from sr.context import get_context
from sr.image.sceenshot import mini_map


class TestGetTeamMemberInWorld(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

        ctx = get_context()

    def test_with_enemy_nearby(self):
        ctx = get_context()
        ctx.init_image_matcher()

        mm = self.get_test_image_new('mm_no_enemy.png')
        self.assertFalse(mini_map.with_enemy_nearby(ctx.im, mm))
