import time
from typing import List, ClassVar

from sr.app.trailblaze_power.trailblaze_power_config import TrailblazePowerPlanItem
from sr.const import phone_menu_const
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.operation import StateOperation, StateOperationEdge, OperationOneRoundResult, StateOperationNode, Operation
from sr.interastral_peace_guide.guide_const import GuideTabEnum, GuideCategoryEnum
from sr.interastral_peace_guide.choose_guide_tab import ChooseGuideTab
from sr.interastral_peace_guide.choose_guide_category import ChooseGuideCategory
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.screen_area.interastral_peace_guide import ScreenGuide
from sr.screen_area.screen_normal_world import ScreenNormalWorld


class ChallengeOrnamentExtraction(StateOperation):

    DIFF_MAP: ClassVar[dict[int, str]] = {
        1: '第一难度',
        2: '第二难度',
        3: '第三难度',
        4: '第四难度',
        5: '第五难度',
    }

    def __init__(self, ctx: Context, plan: TrailblazePowerPlanItem):
        edges: List[StateOperationEdge] = []

        _check_screen = StateOperationNode('识别画面', self.check_screen)

        _open_menu = StateOperationNode('打开菜单', op=OpenPhoneMenu(ctx))
        edges.append(StateOperationEdge(_check_screen, _open_menu, status=ScreenNormalWorld.CHARACTER_ICON.value.status))

        _open_guide = StateOperationNode('打开指南', op=ClickPhoneMenuItem(ctx, phone_menu_const.INTERASTRAL_GUIDE))
        edges.append(StateOperationEdge(_open_menu, _open_guide))

        _choose_survival_index = StateOperationNode('选择生存索引', op=ChooseGuideTab(ctx, GuideTabEnum.TAB_2.value))
        edges.append(StateOperationEdge(_open_guide, _choose_survival_index))
        edges.append(StateOperationEdge(_check_screen, _choose_survival_index, status=ScreenState.GUIDE.value.status))

        _choose_oe = StateOperationNode('选择饰品提取', op=ChooseGuideCategory(ctx, GuideCategoryEnum.ORNAMENT_EXTRACTION.value, skip_wait=True))
        edges.append(StateOperationEdge(_choose_survival_index, _choose_oe))

        _choose_diff = StateOperationNode('选择难度', self.choose_diff)
        edges.append(StateOperationEdge(_choose_oe, _choose_diff))

        _choose_mission = StateOperationNode('选择副本', op=)

        self.plan: TrailblazePowerPlanItem = plan

    def check_screen(self) -> OperationOneRoundResult:
        """
        识别当前画面
        :return:
        """
        screen = self.screenshot()
        if screen_state.is_normal_in_world(screen, self.ctx.im):
            return self.round_success(ScreenNormalWorld.CHARACTER_ICON.value.status)

        if screen_state.in_secondary_ui(screen, self.ctx.ocr, ScreenState.GUIDE.value):
            return self.round_success(ScreenState.GUIDE.value.status)

        return self.round_success()

    def choose_diff(self) -> OperationOneRoundResult:
        """
        选择难度
        :return:
        """
        if self.plan['diff'] == 0 or self.plan['diff'] not in ChallengeOrnamentExtraction.DIFF_MAP:
            return self.round_success()

        self.ctx.controller.click(ScreenGuide.OE_DIFF_DROPDOWN.value.center)
        time.sleep(0.25)

        diff_str = ChallengeOrnamentExtraction.DIFF_MAP[self.plan['diff']]
        area = ScreenGuide.OE_DIFF_DROPDOWN_OPTIONS.value
        screen = self.screenshot()

        click = self.ocr_and_click_one_line(diff_str, area.rect, screen, lcs_percent=1)
        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success()
        else:
            return self.round_retry('选择难度失败', wait_round_time=0.5)


