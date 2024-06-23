from typing import ClassVar, List

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import MatchResult, cv2_utils
from sr.app.application_base import Application
from sr.const import phone_menu_const
from sr.context.context import Context
from sr.image.sceenshot import phone_menu
from sr.operation import StateOperationEdge, StateOperationNode, OperationOneRoundResult
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu


class EmailApp(Application):

    STATUS_WITH_ALERT: ClassVar[str] = '邮件红点'
    STATUS_NO_ALERT: ClassVar[str] = '无邮件红点'
    CLAIM_ALL_RECT: ClassVar[Rect] = Rect(390, 960, 520, 1000)  # 全部领取

    def __init__(self, ctx: Context):
        """
        收取邮件奖励 但不会删除邮件
        2023-11-12 中英文最高画质测试通过
        """
        edges: List[StateOperationEdge] = []

        world = StateOperationNode('返回大世界', op=BackToNormalWorldPlus(ctx))

        menu = StateOperationNode('打开菜单', op=OpenPhoneMenu(ctx))
        edges.append(StateOperationEdge(world, menu))

        click = StateOperationNode('点击邮件', self._click_email)
        edges.append(StateOperationEdge(menu, click))

        claim = StateOperationNode('领取委托奖励', self._claim)
        edges.append(StateOperationEdge(click, claim, status=EmailApp.STATUS_WITH_ALERT))

        back = StateOperationNode('完成后返回大世界', op=BackToNormalWorldPlus(ctx))
        edges.append(StateOperationEdge(claim, back))
        edges.append(StateOperationEdge(click, back, status=EmailApp.STATUS_NO_ALERT))

        super().__init__(ctx, op_name=gt('收取邮件奖励', 'ui'),
                         run_record=ctx.email_run_record,
                         edges=edges
                         )

    def _click_email(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()
        result: MatchResult = phone_menu.get_phone_menu_item_pos_at_right(screen,
                                                                          self.ctx.im,
                                                                          phone_menu_const.EMAILS,
                                                                          alert=True)
        if result is None:
            return self.round_success(EmailApp.STATUS_NO_ALERT)
        else:
            self.ctx.controller.click(result.center)
            return self.round_success(EmailApp.STATUS_WITH_ALERT, wait=1)

    def _claim(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()
        claim_all_part, _ = cv2_utils.crop_image(screen, EmailApp.CLAIM_ALL_RECT)
        ocr_result = self.ctx.ocr.ocr_for_single_line(claim_all_part, strict_one_line=True)
        if str_utils.find_by_lcs(gt('全部领取', 'ocr'), ocr_result, percent=0.5):
            self.ctx.controller.click(EmailApp.CLAIM_ALL_RECT.center)
            return self.round_success(wait=1)
        else:
            return self.round_fail()
