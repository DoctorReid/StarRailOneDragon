from typing import List, Optional


from basic.i18_utils import gt
from sr.app import Application, AppRunRecord, AppDescription, register_app
from sr.const import phone_menu_const
from sr.context import Context
from sr.image.sceenshot import secondary_ui
from sr.operation import Operation, OperationSuccess, OperationFail
from sr.operation.combine import CombineOperation, StatusCombineOperationEdge
from sr.operation.unit import guide
from sr.operation.unit.forgotten_hall.check_forgotten_hall_star import CheckForgottenHallStar
from sr.operation.unit.guide import survival_index
from sr.operation.unit.guide.choose_guide_tab import ChooseGuideTab
from sr.operation.unit.guide.survival_index import ChooseSurvivalIndexCategory, ChooseSurvivalIndexMission
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.operation.unit.wait_in_seconds import WaitInSeconds

FORGOTTEN_HALL = AppDescription(cn='遗忘之庭', id='forgotten_hall')
register_app(FORGOTTEN_HALL)


class ForgottenHallRecord(AppRunRecord):

    def __init__(self):
        super().__init__(FORGOTTEN_HALL.id)

    def check_and_update_status(self):
        super().check_and_update_status()
        self.update_status(AppRunRecord.STATUS_WAIT)


_forgotten_hall_record: Optional[ForgottenHallRecord] = None


def get_record() -> ForgottenHallRecord:
    global _forgotten_hall_record
    if _forgotten_hall_record is None:
        _forgotten_hall_record = ForgottenHallRecord()
    return _forgotten_hall_record


class ForgottenHallApp(Application):

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('遗忘之庭', 'ui'),
                         run_record=get_record())

    def _init_before_execute(self):
        record = get_record()
        record.update_status(AppRunRecord.STATUS_RUNNING)

    def _execute_one_round(self) -> int:
        ops: List[Operation] = []
        edges: List[StatusCombineOperationEdge] = []

        op_success = OperationSuccess(self.ctx)  # 操作成功的终点
        ops.append(op_success)

        op1 = OpenPhoneMenu(self.ctx)  # 打开菜单
        op2 = ClickPhoneMenuItem(self.ctx, phone_menu_const.INTERASTRAL_GUIDE)  # 选择【指南】
        ops.append(op1)
        ops.append(op2)
        edges.append(StatusCombineOperationEdge(op_from=op1, op_to=op2))

        op3 = ChooseGuideTab(self.ctx, guide.GUIDE_TAB_3)  # 选择【生存索引】
        ops.append(op3)
        edges.append(StatusCombineOperationEdge(op_from=op2, op_to=op3))

        op4 = ChooseSurvivalIndexCategory(self.ctx, survival_index.CATEGORY_FORGOTTEN_HALL)  # 左边选择忘却之庭
        ops.append(op4)
        edges.append(StatusCombineOperationEdge(op_from=op3, op_to=op4))

        op5 = ChooseSurvivalIndexMission(self.ctx, survival_index.MISSION_FORGOTTEN_HALL)  # 右侧选择忘却之庭传送
        ops.append(op5)
        edges.append(StatusCombineOperationEdge(op_from=op4, op_to=op5))

        op6 = CheckForgottenHallStar(self.ctx, self._update_star)  # 检测星数并更新
        ops.append(op6)
        edges.append(StatusCombineOperationEdge(op_from=op5, op_to=op6))
        edges.append(StatusCombineOperationEdge(op_from=op6, op_to=op_success, status='30'))  # 满星的时候直接设置为成功

        edges.append(StatusCombineOperationEdge(op_from=op6, op_to=op_success, status='30'))

        combine_op: CombineOperation = CombineOperation(self.ctx, ops, op_name=gt('遗忘之庭', 'ui'))

        if combine_op.execute().result:
            return Operation.SUCCESS

        return Operation.FAIL

    def _update_star(self, star: int):
        pass