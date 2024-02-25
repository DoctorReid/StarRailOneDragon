import test
from sr.context import get_context
from sr.operation.unit.enter_game import LoginWithAnotherAccount


class TestEnterGame(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

    def test_op_login_with_active_account(self):
        ctx = get_context()
        ctx.init_all()
        ctx.start_running()

        op = LoginWithAnotherAccount(ctx)
        op.execute()
