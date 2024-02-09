import unittest

import test
from sr.const.character_const import RUANMEI, TINGYUN, JINGLIU, LUOCHA
from sr.context import get_context
from sr.operation.unit.team import SwitchMember, CheckTeamMembersInWorld


class TestTeam(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_switch_op(self):
        ctx = get_context()
        ctx.start_running()

        op = SwitchMember(ctx, 1)
        op.execute()

    def test_check_members(self):
        ctx = get_context()
        ctx.init_image_matcher()
        ctx.init_ocr_matcher()

        op = CheckTeamMembersInWorld(ctx)

        screen = self.get_test_image('members_1')
        answer = [RUANMEI, TINGYUN, JINGLIU, LUOCHA]

        op.character_list = [None, None, None, None]
        op._check_by_avatar(screen)
        for i in range(4):
            self.assertEqual(answer[i], op.character_list[i])

        op.character_list = [None, None, None, None]
        op._check_by_name(screen)
        for i in range(4):
            self.assertEqual(answer[i], op.character_list[i])
