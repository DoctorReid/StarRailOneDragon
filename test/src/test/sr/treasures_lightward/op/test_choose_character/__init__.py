import test
from sr.const import character_const
from sr.context import get_context
from sr.treasures_lightward.op.choose_character import TlChooseCharacter


class TestTlChooseCharacter(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_get_character_pos(self):
        ctx = get_context()
        ctx.init_image_matcher()

        op = TlChooseCharacter(ctx, 'tingyun')

        screen = self.get_test_image_new('character_list_1.png')

        op.character = character_const.HANYA
        self.assertIsNone(op._get_character_pos(screen))

        op.character = character_const.LUKA
        self.assertIsNotNone(op._get_character_pos(screen))
