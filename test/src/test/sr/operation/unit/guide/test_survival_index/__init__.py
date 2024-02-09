import test
from sr.context import get_context
from sr.operation.combine.transport import Transport
from sr.operation.unit.guide.survival_index import SurvivalIndexMissionEnum, SurvivalIndexCategoryEnum


class TestSurvivalIndex(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_tp(self):
        ctx = get_context()
        ctx.init_all(renew=True)
        ctx.start_running()
        start = False
        for enum in SurvivalIndexMissionEnum:
            if enum.value.cate == SurvivalIndexCategoryEnum.SIM_UNI.value:
                continue
            if enum == SurvivalIndexMissionEnum.ECHO_03:
                start = True
            if not start:
                continue
            tp = enum.value.tp
            op = Transport(ctx, tp)
            self.assertTrue(op.execute().success)
