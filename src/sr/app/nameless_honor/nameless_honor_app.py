import time
from typing import List, ClassVar

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import MatchResult
from sr.app.application_base import Application
from sr.const import phone_menu_const
from sr.context import Context
from sr.image.sceenshot import phone_menu
from sr.image.sceenshot.screen_state import in_secondary_ui, ScreenState
from sr.operation import Operation, StateOperationEdge, StateOperationNode, OperationOneRoundResult
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.screen_area.screen_namess_honor import ScreenNamelessHonor


class NamelessHonorApp(Application):

    STATUS_WITH_ALERT: ClassVar[str] = '红点'
    STATUS_NO_ALERT: ClassVar[str] = '无红点'

    def __init__(self, ctx: Context):
        """
        1. 从菜单打开无名勋礼 如果有红点的话
        2. 到Tab-2领取点数 如果有红点的话
        3. 到Tab-1领取奖励 如果有的话
        4. 返回菜单
        """
        edges: List[StateOperationEdge] = []

        world = StateOperationNode('返回大世界', op=BackToNormalWorldPlus(ctx))

        menu = StateOperationNode('打开菜单', op=OpenPhoneMenu(ctx))
        edges.append(StateOperationEdge(world, menu))

        click = StateOperationNode('点击无名勋礼', self._click_honor)
        edges.append(StateOperationEdge(menu, click))

        tab_2 = StateOperationNode('点击任务', self._click_tab_2)
        edges.append(StateOperationEdge(click, tab_2, status=NamelessHonorApp.STATUS_WITH_ALERT))

        claim_task = StateOperationNode('领取任务奖励', self._claim_task)
        edges.append(StateOperationEdge(tab_2, claim_task, status=NamelessHonorApp.STATUS_WITH_ALERT))

        tab_1 = StateOperationNode('点击奖励', self._click_tab_1)
        edges.append(StateOperationEdge(tab_2, tab_1, status=NamelessHonorApp.STATUS_NO_ALERT))  # 任务没有红点时 返回奖励
        edges.append(StateOperationEdge(claim_task, tab_1))  # 领取任务奖励后 返回奖励
        edges.append(StateOperationEdge(claim_task, tab_1, success=False))  # 有新任务的时候这里会有红点 但不会有领取按钮 因此失败也继续

        claim_reward = StateOperationNode('领取奖励', self._claim_reward)
        edges.append(StateOperationEdge(tab_1, claim_reward, status=NamelessHonorApp.STATUS_WITH_ALERT))

        after_reward = StateOperationNode('领取奖励后', self._check_screen_after_reward)
        edges.append(StateOperationEdge(claim_reward, after_reward))

        back = StateOperationNode('完成后返回大世界', op=BackToNormalWorldPlus(ctx))
        edges.append(StateOperationEdge(click, back, status=NamelessHonorApp.STATUS_NO_ALERT))  # 无名勋礼没有红点
        edges.append(StateOperationEdge(tab_1, back, status=NamelessHonorApp.STATUS_NO_ALERT))  # 奖励没有红点
        edges.append(StateOperationEdge(after_reward, back))  # 领取奖励后

        super().__init__(ctx, op_name=gt('收取无名勋礼', 'ui'),
                         run_record=ctx.nameless_honor_run_record,
                         edges=edges
                         )

    def _click_honor(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()
        result: MatchResult = phone_menu.get_phone_menu_item_pos(screen, self.ctx.im, phone_menu_const.NAMELESS_HONOR, alert=True)
        if result is None:
            return self.round_success(NamelessHonorApp.STATUS_NO_ALERT)
        else:
            self.ctx.controller.click(result.center)
            return self.round_success(NamelessHonorApp.STATUS_WITH_ALERT, wait=1)

    def _click_tab_2(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()
        result: MatchResult = phone_menu.get_nameless_honor_tab_pos(screen, self.ctx.im, 2, alert=True)
        if result is None:
            return self.round_success(NamelessHonorApp.STATUS_NO_ALERT)
        else:
            self.ctx.controller.click(result.center)
            return self.round_success(NamelessHonorApp.STATUS_WITH_ALERT, wait=1)

    def _claim_task(self) -> OperationOneRoundResult:
        area = ScreenNamelessHonor.TAB_2_CLAIM_PART.value
        screen: MatLike = self.screenshot()
        click = self.find_and_click_area(area, screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            time.sleep(2)
            self.ctx.controller.click(area.center)  # 可能会出现一个升级的画面 多点击一次
            time.sleep(1)
            return self.round_success()
        else:
            return self.round_retry(wait=1)

    def _click_tab_1(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()
        result: MatchResult = phone_menu.get_nameless_honor_tab_pos(screen, self.ctx.im, 1, alert=True)
        if result is None:
            return self.round_success(NamelessHonorApp.STATUS_NO_ALERT)
        else:
            self.ctx.controller.click(result.center)
            return self.round_success(NamelessHonorApp.STATUS_WITH_ALERT, wait=1)

    def _claim_reward(self) -> OperationOneRoundResult:
        area = ScreenNamelessHonor.TAB_1_CLAIM_PART.value
        screen: MatLike = self.screenshot()
        click = self.find_and_click_area(area, screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(wait=2)
        elif click == Operation.OCR_CLICK_FAIL:
            return self.round_retry(wait=1)
        else:  # 没有奖励领取时也返回成功
            return self.round_success()

    def _check_screen_after_reward(self) -> OperationOneRoundResult:
        """
        可能出现选择奖励的框 通过判断左上角标题判断
        :return:
        """
        screen = self.screenshot()
        if in_secondary_ui(screen, self.ctx.ocr, ScreenState.NAMELESS_HONOR.value):
            return self.round_success(wait=0.2)

        area_list = [
            ScreenNamelessHonor.TAB_1_DIALOG_CANCEL_BTN.value,
            ScreenNamelessHonor.EMPTY_TO_CLOSE.value
        ]
        for area in area_list:
            click = self.find_and_click_area(area, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                return self.round_wait(wait=1)

        return self.round_retry('未知画面状态', wait=1)
