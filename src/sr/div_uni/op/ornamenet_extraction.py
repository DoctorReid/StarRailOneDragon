import time
from typing import Optional, Callable

from basic.i18_utils import gt
from sr.const import phone_menu_const
from sr.context.context import Context
from sr.div_uni.op.choose_oe_file import ChooseOeFile
from sr.div_uni.op.choose_oe_support import ChooseOeSupport
from sr.div_uni.screen_div_uni import ScreenDivUni
from sr.image.sceenshot import screen_state
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.interastral_peace_guide.choose_guide_category import ChooseGuideCategory
from sr.interastral_peace_guide.choose_guide_mission import ChooseGuideMission
from sr.interastral_peace_guide.choose_guide_tab import ChooseGuideTab
from sr.interastral_peace_guide.guide_const import GuideTabEnum, GuideCategoryEnum, GuideMissionEnum
from sr.operation import StateOperation, OperationOneRoundResult, StateOperationNode, Operation
from sr.operation.battle.start_fight import StartFightForElite
from sr.operation.battle.wait_battle_result import WaitBattleResult
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.screen_area.interastral_peace_guide import ScreenGuide
from sr.screen_area.screen_battle import ScreenBattle
from sr.screen_area.screen_normal_world import ScreenNormalWorld
from sr.sim_uni.op.v2.sim_uni_move_v2 import SimUniMoveToEnemyByMiniMap
from sr.sim_uni.sim_uni_const import OrnamentExtraction


class ChallengeOrnamentExtraction(StateOperation):

    def __init__(self, ctx: Context, mission: OrnamentExtraction, run_times: int,
                 diff: int, file_num: int, support_character: str,
                 get_reward_callback: Optional[Callable[[int], None]] = None):
        super().__init__(ctx, op_name=gt('饰品提取', 'ui'))

        self.mission: OrnamentExtraction = mission
        """需要挑战的副本"""

        self.run_times: int = run_times
        """需要挑战的次数"""

        self.file_num: int = file_num
        """需要使用的存档 0为不选择"""

        self.diff: int = diff
        """需要挑战的难度 0为不选择"""

        self.support_character: str = support_character
        """需要使用的支援角色 None为不是用"""

        self.get_reward_callback: Callable[[int], None] = get_reward_callback
        """挑战成功后 获取奖励的回调"""

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        check_screen = StateOperationNode('识别画面', self.check_screen)

        open_menu = StateOperationNode('打开菜单', op=OpenPhoneMenu(self.ctx))
        self.add_edge(check_screen, open_menu, status=ScreenNormalWorld.CHARACTER_ICON.value.status)

        open_guide = StateOperationNode('打开指南', op=ClickPhoneMenuItem(self.ctx, phone_menu_const.INTERASTRAL_GUIDE))
        self.add_edge(open_menu, open_guide)

        choose_survival_index = StateOperationNode('选择生存索引', op=ChooseGuideTab(self.ctx, GuideTabEnum.TAB_2.value))
        self.add_edge(open_guide, choose_survival_index)
        self.add_edge(check_screen, choose_survival_index, status=ScreenState.GUIDE.value)

        choose_oe = StateOperationNode('选择饰品提取', op=ChooseGuideCategory(self.ctx, GuideCategoryEnum.ORNAMENT_EXTRACTION.value, skip_wait=True))
        self.add_edge(choose_survival_index, choose_oe)

        choose_diff = StateOperationNode('选择难度', self.choose_diff)
        self.add_edge(choose_oe, choose_diff)

        choose_mission = StateOperationNode('选择副本', op=ChooseGuideMission(self.ctx, GuideMissionEnum.get_by_unique_id(self.mission.unique_id)), wait_after_op=3)
        self.add_edge(choose_diff, choose_mission)

        choose_file = StateOperationNode('选择存档', op=ChooseOeFile(self.ctx, self.file_num))
        self.add_edge(choose_mission, choose_file)

        choose_support = StateOperationNode('选择支援', op=ChooseOeSupport(self.ctx, self.support_character))
        self.add_edge(choose_file, choose_support)

        click_challenge = StateOperationNode('点击挑战', self.click_challenge)
        self.add_edge(choose_support, click_challenge)
        self.add_edge(choose_support, click_challenge, success=False)  # 选择支援失败也能继续

        wait_mission_loaded = StateOperationNode('等待副本加载', self.wait_mission_loaded)
        self.add_edge(click_challenge, wait_mission_loaded)

        move_by_mm = StateOperationNode('向红点移动', op=SimUniMoveToEnemyByMiniMap(self.ctx, no_attack=True, stop_after_arrival=True))
        self.add_edge(wait_mission_loaded, move_by_mm)

        start_fight = StateOperationNode('进入战斗', op=StartFightForElite(self.ctx, skip_point_check=True, skip_resurrection_check=True))
        self.add_edge(move_by_mm, start_fight)

        wait_battle_result = StateOperationNode('等待战斗结果', self.wait_battle_result)
        self.add_edge(start_fight, wait_battle_result)

        after_battle_result = StateOperationNode('处理战斗结果', self.after_battle_result)
        self.add_edge(wait_battle_result, after_battle_result)
        self.add_edge(after_battle_result, wait_battle_result, status=ScreenBattle.AFTER_BATTLE_CHALLENGE_AGAIN_BTN.value.status)  # 再次挑战

        wait_back = StateOperationNode('等待退出', self.wait_back)
        self.add_edge(after_battle_result, wait_back, status=ScreenBattle.AFTER_BATTLE_EXIT_BTN.value.status)

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """

        self.battle_fail_times: int = 0
        """战斗失败次数"""

        self.battle_success_times: int = 0
        """战斗胜利的次数"""

        return None

    def check_screen(self) -> OperationOneRoundResult:
        """
        识别当前画面
        :return:
        """
        screen = self.screenshot()
        if screen_state.is_normal_in_world(screen, self.ctx.im):
            return self.round_success(ScreenNormalWorld.CHARACTER_ICON.value.status)

        if screen_state.in_secondary_ui(screen, self.ctx.ocr, ScreenState.GUIDE.value):
            return self.round_success(ScreenState.GUIDE.value)

        return self.round_success()

    def choose_diff(self) -> OperationOneRoundResult:
        """
        选择难度
        :return:
        """
        if self.diff == 0:
            return self.round_success('默认难度')
        if self.diff < 0 or self.diff > 5:
            return self.round_fail('难道只支持1~5')

        diff_opts = [
            ScreenGuide.OE_DIFF_OPT_1.value,
            ScreenGuide.OE_DIFF_OPT_2.value,
            ScreenGuide.OE_DIFF_OPT_3.value,
            ScreenGuide.OE_DIFF_OPT_4.value,
            ScreenGuide.OE_DIFF_OPT_5.value
        ]

        self.ctx.controller.click(ScreenGuide.OE_DIFF_DROPDOWN.value.center)
        time.sleep(0.5)

        area = diff_opts[self.diff - 1]
        self.ctx.controller.click(area.center)
        time.sleep(0.5)

        return self.round_success()

    def click_challenge(self) -> OperationOneRoundResult:
        """
        点击挑战
        :return:
        """
        screen = self.screenshot()
        area = ScreenDivUni.OE_CHALLENGE_BTN.value
        click = self.find_and_click_area(area, screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(wait=2)
        else:
            return self.round_retry(f'点击{area.status}失败', wait_round_time=0.5)

    def wait_mission_loaded(self) -> OperationOneRoundResult:
        """
        等待副本加载
        :return:
        """
        screen = self.screenshot()
        area = ScreenNormalWorld.CHARACTER_ICON.value
        return self.round_by_find_area(screen, area, retry_wait_round=0.5)

    def wait_battle_result(self) -> OperationOneRoundResult:
        """
        等待战斗结果
        :return:
        """
        op = WaitBattleResult(self.ctx, try_attack=True)
        op_result = op.execute()
        if not op_result.success:
            return self.round_fail_by_op(op_result)

        if op_result.status == WaitBattleResult.STATUS_FAIL:
            self.battle_fail_times += 1
            return self.round_by_op(op_result)
        elif op_result.status == WaitBattleResult.STATUS_SUCCESS:
            self.battle_success_times += 1
            if self.get_reward_callback is not None:
                self.get_reward_callback(1)
            return self.round_by_op(op_result)
        else:
            return self.round_fail('未知状态')

    def after_battle_result(self) -> OperationOneRoundResult:
        """
        战斗结果出来后 点击再来一次或退出
        :return:
        """
        screen = self.screenshot()
        if self.battle_fail_times >= 5 or self.battle_success_times >= self.run_times:  # 失败过多或者完成指定次数了 退出
            area = ScreenBattle.AFTER_BATTLE_EXIT_BTN.value
        else:  # 还需要继续挑战
            area = ScreenBattle.AFTER_BATTLE_CHALLENGE_AGAIN_BTN.value

        return self.round_by_find_and_click_area(screen, area, success_wait=2, retry_wait_round=0.5)

    def wait_back(self) -> OperationOneRoundResult:
        """
        等待退出到大世界
        :return:
        """
        screen = self.screenshot()
        area = ScreenNormalWorld.CHARACTER_ICON.value
        return self.round_by_find_area(screen, area, retry_wait_round=1)
