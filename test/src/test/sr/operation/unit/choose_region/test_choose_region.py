import test
from basic.img.os import get_debug_image
from sr.const import map_const
from sr.const.map_const import Region
from sr.context import get_context
from sr.image.sceenshot import large_map
from sr.operation.unit.op_map import ChooseRegion


class TestChooseRegion(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_get_region_pos_list(self):
        ctx = get_context()
        ctx.init_ocr_matcher()

        op = ChooseRegion(ctx, map_const.P04_R03)

        screen = self.get_test_image_new('xzlf.png')
        op.region_to_choose_1 = map_const.P03_R01
        pos_list = op.get_region_pos_list(screen)
        region_set = set()
        for pos in pos_list:
            if pos.data is None:
                continue
            region: Region = pos.data
            region_set.add(region.pr_id)
        self.assertEquals(8, len(region_set))

        screen = self.get_test_image_new('pnkn.png')
        op.region_to_choose_1 = map_const.P04_R01_F1
        pos_list = op.get_region_pos_list(screen)
        region_set = set()
        for pos in pos_list:
            if pos.data is None:
                continue
            region: Region = pos.data
            region_set.add(region.pr_id)
        self.assertEquals(5, len(region_set))

    def test_choose_region(self):
        ctx = get_context()
        ctx.init_ocr_matcher()

        op = ChooseRegion(ctx, map_const.P04_R03)
        screen = get_debug_image('2')
        current_region_name = large_map.get_active_region_name(screen, ctx.ocr)

        screen = get_debug_image('_1718548755416')
        current_region_name = large_map.get_active_region_name(screen, ctx.ocr)
