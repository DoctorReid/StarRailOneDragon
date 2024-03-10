import time

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult
from sr.screen_area.screen_normal_world import ScreenNormalWorld
from sr.screen_area.screen_phone_menu import ScreenPhoneMenu
from sr.screen_area.screen_sim_uni import ScreenSimUni
from sr.screen_area.screen_treasures_lightward import ScreenTreasuresLightWard
from sr.sim_uni import sim_uni_screen_state
from sr.sim_uni.op.sim_uni_choose_bless import SimUniChooseBless, SimUniDropBless
from sr.sim_uni.op.sim_uni_choose_curio import SimUniChooseCurio, SimUniDropCurio
from sr.sim_uni.op.sim_uni_event import SimUniEvent
from sr.sim_uni.op.sim_uni_exit import SimUniExit


class BackToNormalWorldPlus(Operation):

    def __init__(self, ctx: Context):
        """
        返回普通大世界 增强版
        需要在任何情况下使用都能顺利地返回手机菜单 用于应用结束后 确保不会卡死下一个应用
        已考虑场景如下
        :param ctx:
        """
        super().__init__(ctx, try_times=20,
                         op_name=gt('返回普通大世界', 'ui'),
                         timeout_seconds=60,
                         )

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        # 先看看左上角是否退出按钮
        exit_icon = ScreenSimUni.EXIT_BTN.value
        if self.find_area(exit_icon, screen):
            # 判断是否在模拟宇宙内
            sim_uni_level_type = sim_uni_screen_state.get_level_type(screen, self.ctx.ocr)
            if sim_uni_level_type is not None:
                return self.sim_uni_exit()

            # 判断是否在逐光捡金内
            click = self.find_and_click_area(exit_icon, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                return Operation.round_wait(wait=1)

            # 都不在的话 暂时不支持返回大世界
            return Operation.round_fail('未支持的副本画面')

        # 在可以移动的画面 - 普通大世界
        character_icon = ScreenNormalWorld.CHARACTER_ICON.value
        if self.find_area(character_icon, screen):  # 右上角有角色图标
            return Operation.round_success()

        # 手机菜单
        phone_menu = ScreenPhoneMenu.TRAILBLAZE_LEVEL_PART.value
        if self.find_area(phone_menu, screen):
            self.ctx.controller.click(ScreenPhoneMenu.EXIT_BTN.value.center)
            return Operation.round_wait(wait=1)

        # 模拟宇宙内的画面
        sim_uni_state = screen_state.get_sim_uni_screen_state(
            screen, self.ctx.im, self.ctx.ocr,
            event=True,
            bless=True,
            drop_bless=True,
            curio=True,
            drop_curio=True
        )

        if sim_uni_state == screen_state.ScreenState.SIM_BLESS.value:
            return self.sim_uni_choose_bless()

        if sim_uni_state == screen_state.ScreenState.SIM_DROP_BLESS.value:
            return self.sim_uni_drop_bless()

        if sim_uni_state == screen_state.ScreenState.SIM_CURIOS.value:
            return self.sim_uni_choose_curio()

        if sim_uni_state == screen_state.ScreenState.SIM_DROP_CURIOS.value:
            return self.sim_uni_drop_curio()

        if sim_uni_state == screen_state.ScreenState.SIM_EVENT.value:
            return self.sim_uni_event()

        # 对话框 - 逐光捡金 退出确认
        dialog_confirm = ScreenTreasuresLightWard.EXIT_DIALOG_CONFIRM.value
        if self.find_and_click_area(dialog_confirm, screen) == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_wait(wait=5)

        # 列车补给 - 点击空白处继续
        express_supply = ScreenNormalWorld.EXPRESS_SUPPLY.value
        if self.find_area(express_supply, screen):
            express_supply_get = ScreenNormalWorld.EXPRESS_SUPPLY_GET.value
            self.ctx.controller.click(express_supply_get.center)
            time.sleep(3)  # 暂停一段时间再操作
            self.ctx.controller.click(express_supply_get.center)  # 领取需要分两个阶段 点击两次
            time.sleep(1)  # 暂停一段时间再操作
            return Operation.round_wait(wait=2)

        # 战斗中 点击右上角后出现的画面 需要需要退出
        battle_exit_area_list = [
            ScreenSimUni.BATTLE_EXIT.value,  # 模拟宇宙
        ]
        for area in battle_exit_area_list:
            if self.find_and_click_area(area, screen) == Operation.OCR_CLICK_SUCCESS:
                return Operation.round_wait(wait=1)

        # 其他情况 - 均点击右上角触发返回上一级
        self.ctx.controller.click(ScreenPhoneMenu.EXIT_BTN.value.center)
        return Operation.round_wait(wait=1)

    def sim_uni_exit(self) -> OperationOneRoundResult:
        op = SimUniExit(self.ctx)
        op_result = op.execute()
        if op_result.success:
            return Operation.round_wait(wait=1)
        else:
            return Operation.round_retry(wait=1)

    def sim_uni_event(self) -> OperationOneRoundResult:
        op = SimUniEvent(self.ctx)
        op_result = op.execute()
        if op_result.success:
            return Operation.round_wait(wait=1)
        else:
            return Operation.round_retry(wait=1)

    def sim_uni_choose_bless(self) -> OperationOneRoundResult:
        op = SimUniChooseBless(self.ctx)
        op_result = op.execute()
        if op_result.success:
            return Operation.round_wait(wait=1)
        else:
            return Operation.round_retry(wait=1)

    def sim_uni_drop_bless(self) -> OperationOneRoundResult:
        op = SimUniDropBless(self.ctx)
        op_result = op.execute()
        if op_result.success:
            return Operation.round_wait(wait=1)
        else:
            return Operation.round_retry(wait=1)

    def sim_uni_choose_curio(self) -> OperationOneRoundResult:
        op = SimUniChooseCurio(self.ctx)
        op_result = op.execute()
        if op_result.success:
            return Operation.round_wait(wait=1)
        else:
            return Operation.round_retry(wait=1)

    def sim_uni_drop_curio(self) -> OperationOneRoundResult:
        op = SimUniDropCurio(self.ctx)
        op_result = op.execute()
        if op_result.success:
            return Operation.round_wait(wait=1)
        else:
            return Operation.round_retry(wait=1)
