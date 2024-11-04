from cv2.typing import MatLike
from typing import ClassVar

from one_dragon.base.matcher.match_result import MatchResult, MatchResultList
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils
from one_dragon.utils.i18_utils import gt
from sr_od.app.sr_application import SrApplication
from sr_od.context.sr_context import SrContext
from sr_od.operations.back_to_normal_world_plus import BackToNormalWorldPlus
from sr_od.operations.menu import phone_menu_utils, phone_menu_const
from sr_od.operations.menu.open_phone_menu import OpenPhoneMenu


class AssignmentsApp(SrApplication):

    STATUS_WITH_ALERT: ClassVar[str] = '委托红点'
    STATUS_NO_ALERT: ClassVar[str] = '无委托红点'
    STATUS_NO_ALL_CLAIM: ClassVar[str] = '无一键领取'
    STATUS_NO_CLAIM: ClassVar[str] = '无领取'

    def __init__(self, ctx: SrContext):
        SrApplication.__init__(self, ctx, 'assignments', op_name=gt('委托', 'ui'),
                               run_record=ctx.assignments_run_record,)

    @operation_node(name='开始前返回', is_start_node=True)
    def back_at_first(self) -> OperationRoundResult:
        op = BackToNormalWorldPlus(self.ctx)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='开始前返回')
    @operation_node(name='打开菜单')
    def open_menu(self) -> OperationRoundResult:
        op = OpenPhoneMenu(self.ctx)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='打开菜单')
    @operation_node(name='点击委托')
    def _click_assignment(self) -> OperationRoundResult:
        screen: MatLike = self.screenshot()
        result: MatchResult = phone_menu_utils.get_phone_menu_item_pos(self.ctx, screen, phone_menu_const.ASSIGNMENTS, alert=True)
        if result is None:
            return self.round_success(AssignmentsApp.STATUS_NO_ALERT)
        else:
            self.ctx.controller.click(result.center)
            return self.round_success(AssignmentsApp.STATUS_WITH_ALERT, wait=2)

    @node_from(from_name='点击委托', status=STATUS_WITH_ALERT)
    @node_from(from_name='点击红点')  # 红点之后 回到一键委托
    @operation_node(name='一键领取')
    def _claim_all(self) -> OperationRoundResult:
        screen = self.screenshot()
        result = self.round_by_find_area(screen, '菜单', '委托-一键领取')
        if result.is_success:
            return self.round_by_find_and_click_area(screen, '菜单', '委托-一键领取',
                                                     success_wait=1, retry_wait=1)
        else:
            return self.round_success(status=AssignmentsApp.STATUS_NO_ALL_CLAIM)

    @node_from(from_name='一键领取')
    @operation_node(name='再次派遣')
    def _send(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '菜单', '委托-再次派遣',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='点击委托', status=STATUS_NO_ALL_CLAIM)  # 可能有活动 导致没有一键领取
    @node_from(from_name='点击空白')
    @operation_node(name='领取')
    def _claim(self) -> OperationRoundResult:
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '菜单', '委托-领取')
        if result.is_success:
            return self.round_by_find_and_click_area(screen, '菜单', '委托-领取',
                                                     success_wait=1, retry_wait=1)
        else:
            return self.round_success(status=AssignmentsApp.STATUS_NO_CLAIM)

    @node_from(from_name='领取')
    @operation_node(name='点击空白')
    def _click_empty(self):
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '菜单', '委托-点击空白区域继续',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='领取', status=STATUS_NO_CLAIM)  # 活动的领取完了 找红点到普通委托
    @operation_node(name='点击红点')
    def _click_alert_category(self):
        screen = self.screenshot()
        area = self.ctx.screen_loader.get_area('菜单', '委托-任务列表')
        category_part = cv2_utils.crop_image_only(screen, area.rect)
        result_list: MatchResultList = self.ctx.tm.match_template(category_part, 'phone_menu', 'ui_alert')

        if len(result_list) > 0:  # 有红点
            self.ctx.controller.click(area.rect.left_top + result_list.max.center)
            return self.round_success(wait=1)

        return self.round_retry('无红点')

    @node_from(from_name='再次派遣')
    @node_from(from_name='点击委托', status=STATUS_NO_ALERT)
    @node_from(from_name='点击红点', success=False)
    @operation_node(name='完成后返回大世界')
    def back_at_last(self) -> OperationRoundResult:
        op = BackToNormalWorldPlus(self.ctx)
        return self.round_by_op_result(op.execute())