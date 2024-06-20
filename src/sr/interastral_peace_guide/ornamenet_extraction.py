from typing import List

from sr.const import phone_menu_const
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.interastral_peace_guide.survival_index_mission import SurvivalIndexCategoryEnum
from sr.operation import StateOperation, StateOperationEdge, OperationOneRoundResult, StateOperationNode
from sr.operation.unit.guide import GuideTabEnum
from sr.operation.unit.guide.choose_guide_tab import ChooseGuideTab
from sr.operation.unit.guide.survival_index import SurvivalIndexChooseCategory
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.screen_area.screen_normal_world import ScreenNormalWorld


class ChallengeOrnamentExtraction(StateOperation):

    def __init__(self, ctx: Context):
        edges: List[StateOperationEdge] = []

        _check_screen = StateOperationNode('识别画面', self.check_screen)

        _open_menu = StateOperationNode('打开菜单', op=OpenPhoneMenu(ctx))
        edges.append(StateOperationEdge(_check_screen, _open_menu, status=ScreenNormalWorld.CHARACTER_ICON.value.status))

        _open_guide = StateOperationNode('打开指南', op=ClickPhoneMenuItem(ctx, phone_menu_const.INTERASTRAL_GUIDE))
        edges.append(StateOperationEdge(_open_menu, _open_guide))

        _choose_survival_index = StateOperationNode('选择生存索引', op=ChooseGuideTab(ctx, GuideTabEnum.TAB_2.value))
        edges.append(StateOperationEdge(_open_guide, _choose_survival_index))
        edges.append(StateOperationEdge(_check_screen, _choose_survival_index, status=ScreenState.GUIDE.value.status))

        _choose_oe = StateOperationNode('选择饰品提取', op=SurvivalIndexChooseCategory(ctx, SurvivalIndexCategoryEnum.ORNAMENT_EXTRACTION.value, skip_wait=True))
        edges.append(StateOperationEdge(_choose_survival_index, _choose_oe))

        _choose_diff = StateOperationNode('选择难度', )

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