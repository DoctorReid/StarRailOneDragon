from typing import List, ClassVar

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import MatchResult, cv2_utils, MatchResultList
from sr.app.application_base import Application
from sr.const import phone_menu_const
from sr.context.context import Context
from sr.image.sceenshot import phone_menu
from sr.operation import Operation, StateOperationNode, StateOperationEdge, OperationOneRoundResult
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.screen_area.screen_phone_menu import ScreenPhoneMenu


class AssignmentsApp(Application):

    STATUS_WITH_ALERT: ClassVar[str] = '委托红点'
    STATUS_NO_ALERT: ClassVar[str] = '无委托红点'
    STATUS_NO_ALL_CLAIM: ClassVar[str] = '无一键领取'
    STATUS_NO_CLAIM: ClassVar[str] = '无领取'

    def __init__(self, ctx: Context):
        edges: List[StateOperationEdge] = []

        world = StateOperationNode('返回大世界', op=BackToNormalWorldPlus(ctx))
        menu = StateOperationNode('打开菜单', op=OpenPhoneMenu(ctx))
        edges.append(StateOperationEdge(world, menu))

        click = StateOperationNode('点击委托', self._click_assignment)
        edges.append(StateOperationEdge(menu, click))

        claim_all = StateOperationNode('一键领取', self._claim_all)
        edges.append(StateOperationEdge(click, claim_all, status=AssignmentsApp.STATUS_WITH_ALERT))

        send = StateOperationNode('再次派遣', self._send)
        edges.append(StateOperationEdge(claim_all, send))

        # 可能有活动 导致没有一键领取
        claim = StateOperationNode('领取', self._claim)
        edges.append(StateOperationEdge(claim_all, claim, status=AssignmentsApp.STATUS_NO_ALL_CLAIM))

        # 领取后出现空白
        click_empty = StateOperationNode('点击空白', self._click_empty)
        edges.append(StateOperationEdge(claim, click_empty))
        # 空白后继续领取
        edges.append(StateOperationEdge(click_empty, claim))

        # 活动的领取完了 找红点到普通委托
        click_alert = StateOperationNode('点击红点', self._click_alert_category)
        edges.append(StateOperationEdge(claim, click_alert, status=AssignmentsApp.STATUS_NO_CLAIM))

        # 红点之后 回到一键委托
        edges.append(StateOperationEdge(click_alert, claim_all))

        back = StateOperationNode('完成后返回大世界', op=BackToNormalWorldPlus(ctx))
        edges.append(StateOperationEdge(send, back))
        edges.append(StateOperationEdge(click, back, status=AssignmentsApp.STATUS_NO_ALERT))
        edges.append(StateOperationEdge(click_alert, back, success=False))  # 没有红点也返回

        super().__init__(ctx, op_name=gt('委托', 'ui'),
                         run_record=ctx.assignments_run_record,
                         edges=edges,
                         )

    def _click_assignment(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()
        result: MatchResult = phone_menu.get_phone_menu_item_pos(screen,
                                                                 self.ctx.im,
                                                                 phone_menu_const.ASSIGNMENTS,
                                                                 alert=True)
        if result is None:
            return self.round_success(AssignmentsApp.STATUS_NO_ALERT)
        else:
            self.ctx.controller.click(result.center)
            return self.round_success(AssignmentsApp.STATUS_WITH_ALERT, wait=2)

    def _claim_all(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        area = ScreenPhoneMenu.ASSIGNMENTS_CLAIM_ALL.value
        click = self.find_and_click_area(area, screen)
        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success()
        elif click == Operation.OCR_CLICK_NOT_FOUND:
            return self.round_success(status=AssignmentsApp.STATUS_NO_ALL_CLAIM)
        else:
            return self.round_retry(status='点击%s失败' % area.status, wait=1)

    def _send(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        area = ScreenPhoneMenu.ASSIGNMENTS_SEND_AGAIN.value
        if self.find_and_click_area(area, screen) == Operation.OCR_CLICK_SUCCESS:
            return self.round_success()
        else:
            return self.round_retry(status='点击%s失败' % area.status, wait=1)

    def _claim(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        area = ScreenPhoneMenu.ASSIGNMENTS_CLAIM.value
        click = self.find_and_click_area(area, screen)
        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(wait=1)
        elif click == Operation.OCR_CLICK_NOT_FOUND:
            return self.round_success(status=AssignmentsApp.STATUS_NO_CLAIM)
        else:
            return self.round_retry(status='点击%s失败' % area.status, wait=1)

    def _click_empty(self):
        screen = self.screenshot()
        area = ScreenPhoneMenu.ASSIGNMENTS_CLICK_EMPTY.value
        click = self.find_and_click_area(area, screen)
        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(wait=1)
        else:
            return self.round_retry(status='点击%s失败' % area.status, wait=1)

    def _click_alert_category(self):
        screen = self.screenshot()
        area = ScreenPhoneMenu.ASSIGNMENTS_CATEGORY_RECT.value
        category_part = cv2_utils.crop_image_only(screen, area.rect)
        result_list: MatchResultList = self.ctx.im.match_template(category_part, 'ui_alert')

        if len(result_list) > 0:  # 有红点
            self.ctx.controller.click(area.rect.left_top + result_list.max.center)
            return self.round_success(wait=1)

        return self.round_retry('无红点')

    @property
    def current_execution_desc(self) -> str:
        """
        当前运行的描述 用于UI展示
        :return:
        """
        return gt('委托', 'ui')
