import time

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import MatchResult
from basic.log_utils import log
from sr.app.application_base import Application
from sr.const import phone_menu_const
from sr.context import Context
from sr.image.sceenshot import phone_menu
from sr.image.sceenshot.screen_state import in_secondary_ui, ScreenState
from sr.operation import Operation
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu


class NamelessHonorApp(Application):

    """
    1. 从菜单打开无名勋礼 如果有红点的话
    2. 到Tab-2领取点数 如果有红点的话
    3. 到Tab-1领取奖励 如果有的话
    4. 返回菜单
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('收取无名勋礼', 'ui'),
                         run_record=ctx.nameless_honor_run_record)

        self.phase: int = 0

    def _execute_one_round(self) -> int:
        if self.phase == 0:  # 打开菜单
            op = OpenPhoneMenu(self.ctx)
            if op.execute().success:
                self.phase += 1
                return Operation.WAIT
            else:
                return Operation.FAIL
        elif self.phase == 1:  # 检测无名勋礼红点并点击
            screen: MatLike = self.screenshot()
            result: MatchResult = phone_menu.get_phone_menu_item_pos(screen, self.ctx.im, phone_menu_const.NAMELESS_HONOR, alert=True)
            if result is None:
                log.info('检测不到无名勋礼红点 跳过')
                return Operation.SUCCESS
            else:
                self.ctx.controller.click(result.center)
                self.phase += 1
                time.sleep(1)
                return Operation.WAIT
        elif self.phase == 2:  # 检测第2个tab红点并点击
            screen: MatLike = self.screenshot()
            result: MatchResult = phone_menu.get_nameless_honor_tab_pos(screen, self.ctx.im, 2, alert=True)
            if result is None:
                log.info('检测不到任务红点')
                self.phase = 5  # 跳转到在tab1领取奖励
                return Operation.WAIT
            else:
                self.ctx.controller.click(result.center)
                self.phase += 1
                time.sleep(1)
                return Operation.WAIT
        elif self.phase == 3:  # 领取任务奖励
            screen: MatLike = self.screenshot()
            result: MatchResult = phone_menu.get_nameless_honor_tab_2_claim_pos(screen, self.ctx.ocr)
            if result is None:
                log.info('检测不到【一键领取】')
                return Operation.SUCCESS
            else:
                self.ctx.controller.click(result.center)
                time.sleep(2)
                self.ctx.controller.click(result.center)  # 可能会出现一个升级的画面 多点击一次
                time.sleep(1)
                self.phase += 1
                return Operation.WAIT
        elif self.phase == 4:  # 返回tab1
            screen: MatLike = self.screenshot()
            result: MatchResult = phone_menu.get_nameless_honor_tab_pos(screen, self.ctx.im, 1, alert=True)
            if result is None:
                log.info('检测不到奖励图标')
                time.sleep(1)
                return Operation.SUCCESS
            else:
                self.ctx.controller.click(result.center)
                time.sleep(1)
                self.phase += 1
                return Operation.WAIT
        elif self.phase == 5:  # 领取奖励
            screen: MatLike = self.screenshot()
            result: MatchResult = phone_menu.get_nameless_honor_tab_1_claim_pos(screen, self.ctx.ocr)
            if result is None:
                log.info('检测不到【一键领取】 跳过')  # 是可能没有奖励的
                self.phase += 1
                return Operation.WAIT
            else:
                self.ctx.controller.click(result.center)  # 点击后如果出现要选择的 就先退出 以后再加入选择配置
                self.phase += 1
                time.sleep(1)
                return Operation.WAIT
        elif self.phase == 6:  # 可能出现选择奖励的框 通过判断左上角标题判断
            screen = self.screenshot()
            if in_secondary_ui(screen, self.ctx.ocr, ScreenState.NAMELESS_HONOR.value):
                self.phase += 1
                time.sleep(0.2)
                return Operation.WAIT
            else:
                time.sleep(2)
                screen = self.screenshot()
                result: MatchResult = phone_menu.get_nameless_honor_tab_1_cancel_btn(screen, self.ctx.ocr)
                if result is not None:
                    self.ctx.controller.click(result.center)  # 点击后如果出现要选择的 就先退出 以后再加入选择配置
                    self.phase += 1
                    time.sleep(1)
                    return Operation.WAIT
                else:
                    self.phase += 1
                    time.sleep(1)
                    return Operation.WAIT
        elif self.phase == 7:  # 领取完返回菜单
            op = OpenPhoneMenu(self.ctx)
            r = op.execute().success
            if not r:
                return Operation.FAIL
            else:
                return Operation.SUCCESS
