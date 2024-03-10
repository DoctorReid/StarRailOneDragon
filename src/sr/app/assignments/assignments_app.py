from typing import List, ClassVar

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import MatchResult
from sr.app.application_base import Application2
from sr.const import phone_menu_const
from sr.context import Context
from sr.image.sceenshot import phone_menu
from sr.operation import Operation, StateOperationNode, StateOperationEdge, OperationOneRoundResult
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus
from sr.operation.unit.claim_assignment import ClaimAssignment
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu


class AssignmentsApp(Application2):

    STATUS_WITH_ALERT: ClassVar[str] = '委托红点'
    STATUS_NO_ALERT: ClassVar[str] = '无委托红点'

    def __init__(self, ctx: Context):
        edges: List[StateOperationEdge] = []

        world = StateOperationNode('返回大世界', op=BackToNormalWorldPlus(ctx))
        menu = StateOperationNode('打开菜单', op=OpenPhoneMenu(ctx))
        edges.append(StateOperationEdge(world, menu))

        click = StateOperationNode('点击委托', self._click_assignment)
        edges.append(StateOperationEdge(menu, click))

        claim = StateOperationNode('领取委托奖励', self._claim)
        edges.append(StateOperationEdge(click, claim, status=AssignmentsApp.STATUS_WITH_ALERT))

        back = StateOperationNode('完成后返回大世界', op=BackToNormalWorldPlus(ctx))
        edges.append(StateOperationEdge(claim, back))
        edges.append(StateOperationEdge(click, back, status=AssignmentsApp.STATUS_NO_ALERT))

        super().__init__(ctx, op_name=gt('委托', 'ui'),
                         run_record=ctx.assignments_run_record,
                         edges=edges
                         )

    def _click_assignment(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()
        result: MatchResult = phone_menu.get_phone_menu_item_pos(screen,
                                                                 self.ctx.im,
                                                                 phone_menu_const.ASSIGNMENTS,
                                                                 alert=True)
        if result is None:
            return Operation.round_success(AssignmentsApp.STATUS_NO_ALERT)
        else:
            self.ctx.controller.click(result.center)
            return Operation.round_success(AssignmentsApp.STATUS_WITH_ALERT, wait=1)

    def _claim(self) -> OperationOneRoundResult:
        op = ClaimAssignment(self.ctx)
        op_result = op.execute()
        if op_result.success:
            self.ctx.assignments_run_record.claim_dt = self.ctx.assignments_run_record.get_current_dt()

        return Operation.round_by_op(op_result)

    @property
    def current_execution_desc(self) -> str:
        """
        当前运行的描述 用于UI展示
        :return:
        """
        return gt('委托', 'ui')
