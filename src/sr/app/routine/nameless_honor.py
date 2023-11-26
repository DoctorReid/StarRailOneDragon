import time
from typing import Optional

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import MatchResult, cv2_utils
from basic.log_utils import log
from sr.app import Application, AppRunRecord, AppDescription, register_app
from sr.const import phone_menu_const
from sr.context import Context
from sr.image.sceenshot import phone_menu, secondary_ui
from sr.operation import Operation
from sr.operation.unit.open_phone_menu import OpenPhoneMenu

NAMELESS_HONOR = AppDescription(cn='无名勋礼', id='nameless_honor')
register_app(NAMELESS_HONOR)


class NamelessHonorRecord(AppRunRecord):

    def __init__(self):
        super().__init__(NAMELESS_HONOR.id)

    def check_and_update_status(self):
        super().check_and_update_status()
        self.update_status(AppRunRecord.STATUS_WAIT)


nameless_honor_record: Optional[NamelessHonorRecord] = None


def get_record() -> NamelessHonorRecord:
    global nameless_honor_record
    if nameless_honor_record is None:
        nameless_honor_record = NamelessHonorRecord()
    return nameless_honor_record


class ClaimNamelessHonor(Application):

    """
    1. 从菜单打开无名勋礼 如果有红点的话
    2. 到Tab-2领取点数 如果有红点的话
    3. 到Tab-1领取奖励 如果有的话
    4. 返回菜单
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('收取无名勋礼', 'ui'))

        self.phase: int = 0

    def _execute_one_round(self) -> int:
        if self.phase == 0:  # 打开菜单
            op = OpenPhoneMenu(self.ctx)
            if op.execute():
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
            if secondary_ui.in_secondary_ui(screen, self.ctx.ocr, phone_menu_const.NAMELESS_HONOR.cn):
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
                    return Operation.FAIL
        elif self.phase == 7:  # 领取完返回菜单
            op = OpenPhoneMenu(self.ctx)
            r = op.execute()
            if not r:
                return Operation.FAIL
            else:
                return Operation.SUCCESS

    def _after_stop(self, result: bool):
        get_record().update_status(AppRunRecord.STATUS_SUCCESS if result else AppRunRecord.STATUS_FAIL)
