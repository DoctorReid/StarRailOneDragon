import unittest

import test
from sr.const.character_const import LUOCHA, TINGYUN, HERTA, DANHENGIMBIBITORLUNAE
from sr.context import get_context
from sr.operation.unit.team import GetTeamMemberInWorld


class TestGetTeamMemberInWorld(unittest.TestCase, test.SrTestBase):

    def setUp(self):
        test.SrTestBase.__init__(self, __file__)

        ctx = get_context()
        ctx.init_ocr_matcher()

        self.op = GetTeamMemberInWorld(ctx, 1)

    def test_get_character_id(self):
        screen = self.get_test_image('1')

        self.op.character_num = 1
        self.assertEquals(TINGYUN.id, self.op._get_character_id(screen))

        self.op.character_num = 2
        self.assertEquals(LUOCHA.id, self.op._get_character_id(screen))

        self.op.character_num = 3
        self.assertEquals(HERTA.id, self.op._get_character_id(screen))

        self.op.character_num = 4
        self.assertEquals(DANHENGIMBIBITORLUNAE.id, self.op._get_character_id(screen))
