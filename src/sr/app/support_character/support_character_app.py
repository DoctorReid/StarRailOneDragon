from typing import List, ClassVar

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import MatchResult
from sr.app.application_base import Application
from sr.context import Context
from sr.image.sceenshot import phone_menu
from sr.operation import Operation, StateOperationEdge, StateOperationNode, OperationOneRoundResult
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu


class SupportCharacterApp(Application):

    STATUS_WITH_ALERT: ClassVar[str] = '红点'
    STATUS_NO_ALERT: ClassVar[str] = '无红点'

    def __init__(self, ctx: Context):
        """
        收取支援角色奖励
        2023-11-12 中英文最高画质测试通过
        """
        edges: List[StateOperationEdge] = []

        world = StateOperationNode('返回大世界', op=BackToNormalWorldPlus(ctx))

        menu = StateOperationNode('打开菜单', op=OpenPhoneMenu(ctx))
        edges.append(StateOperationEdge(world, menu))

        ellipsis = StateOperationNode('点击省略号', self._click_ellipsis)
        edges.append(StateOperationEdge(menu, ellipsis))

        profile = StateOperationNode('点击漫游签证', self._click_profile)
        edges.append(StateOperationEdge(ellipsis, profile, status=SupportCharacterApp.STATUS_WITH_ALERT))

        character = StateOperationNode('领取奖励', self._click_character)
        edges.append(StateOperationEdge(profile, character, status=SupportCharacterApp.STATUS_WITH_ALERT))

        back = StateOperationNode('完成后返回大世界', op=BackToNormalWorldPlus(ctx))
        edges.append(StateOperationEdge(ellipsis, back, status=SupportCharacterApp.STATUS_NO_ALERT)) # 省略号无红点
        edges.append(StateOperationEdge(profile, back, status=SupportCharacterApp.STATUS_NO_ALERT)) # 漫游签证无红点
        edges.append(StateOperationEdge(character, back, ignore_status=True))

        super().__init__(ctx, op_name=gt('支援角色奖励', 'ui'),
                         run_record=ctx.support_character_run_record,
                         edges=edges
                         )

    def _click_ellipsis(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()
        result: MatchResult = phone_menu.get_phone_menu_ellipsis_pos(screen, self.ctx.im, alert=True)
        if result is None:
            return Operation.round_success(SupportCharacterApp.STATUS_NO_ALERT)
        else:
            self.ctx.controller.click(result.center)
            return Operation.round_success(SupportCharacterApp.STATUS_WITH_ALERT, wait=1)

    def _click_profile(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()
        result: MatchResult = phone_menu.get_phone_menu_ellipsis_item_pos(screen, self.ctx.im, self.ctx.ocr, '漫游签证', alert=True)
        if result is None:
            return Operation.round_success(SupportCharacterApp.STATUS_NO_ALERT)
        else:
            self.ctx.controller.click(result.center)
            return Operation.round_success(SupportCharacterApp.STATUS_WITH_ALERT, wait=1)

    def _click_character(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()
        result: MatchResult = phone_menu.get_alert_pos(screen, self.ctx.im, phone_menu.SUPPORT_CHARACTER_PART).max
        if result is None:
            return Operation.round_success(SupportCharacterApp.STATUS_NO_ALERT)
        else:
            self.ctx.controller.click(result.center + phone_menu.SUPPORT_CHARACTER_PART.left_top)
            return Operation.round_success(SupportCharacterApp.STATUS_WITH_ALERT, wait=1)
