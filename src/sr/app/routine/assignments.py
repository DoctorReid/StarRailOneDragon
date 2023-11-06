from basic.i18_utils import gt
from sr.app import Application
from sr.const import phone_menu_const
from sr.context import Context
from sr.operation import Operation
from sr.operation.combine import CombineOperation
from sr.operation.unit.claim_assignment import ClaimAssignment
from sr.operation.unit.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.open_phone_menu import OpenPhoneMenu


class Assignments(Application):

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('委托', 'ui'))

    def init_app(self):
        pass

    def run(self) -> int:
        ops = [OpenPhoneMenu(self.ctx), ClickPhoneMenuItem(self.ctx, phone_menu_const.ASSIGNMENTS), ClaimAssignment(self.ctx)]

        op = CombineOperation(self.ctx, ops, op_name=gt('委托', 'ui'))

        if op.execute():
            return Operation.SUCCESS
        else:
            return Operation.FAIL
