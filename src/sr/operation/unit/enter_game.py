import time

import sr.const
from basic.i18_utils import gt
from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot import battle, enter_game_ui
from sr.operation import Operation, OperationOneRoundResult


class EnterGame(Operation):
    """
    操作进入游戏
    主要为点击 点击进入 最终进入到游戏主界面 右上角看到角色的图标
    需保证游戏不需要登录
    以后再考虑加入选择账号登录功能
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx, try_times=3, op_name=gt('进入游戏', 'ui'), timeout_seconds=180)
        self.first_in_world_time: float = 0
        self.claim_express_supply: bool = False
        self.try_login: bool = False  # 是否已经尝试过登录了

    def _init_before_execute(self):
        super()._init_before_execute()
        self.first_in_world_time = 0
        self.claim_express_supply = False
        self.try_login = False

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        if battle.IN_WORLD == battle.get_battle_status(screen, self.ctx.im):  # 进入到主界面
            now = time.time()
            if self.first_in_world_time == 0:
                self.first_in_world_time = now

            if self.claim_express_supply:  # 已经领取过列车补给
                return Operation.round_success()
            else:  # 没领列车补给的话 等2秒看看有没有
                if now - self.first_in_world_time > 2:
                    return Operation.round_success()
                else:
                    return Operation.round_wait()

        if enter_game_ui.in_final_enter_phase(screen, self.ctx.ocr):  # 下方有 点击进入 的字样
            self.ctx.controller.click(enter_game_ui.FINAL_ENTER_GAME_RECT.center)
            time.sleep(1)  # 暂停一段时间再操作
            return Operation.round_wait()

        if enter_game_ui.in_express_supply_phase(screen, self.ctx.ocr):  # 列车补给(小月卡) - 会先出现主界面
            self.ctx.controller.click(sr.const.CLICK_TO_CONTINUE_POS)
            time.sleep(3)  # 暂停一段时间再操作
            self.ctx.controller.click(sr.const.CLICK_TO_CONTINUE_POS)  # 领取需要分两个阶段 点击两次
            time.sleep(1)  # 暂停一段时间再操作
            self.claim_express_supply = True
            return Operation.round_wait()

        if enter_game_ui.in_login_phase(screen, self.ctx.ocr):
            gc = self.ctx.game_config
            if len(gc.game_account) == 0 or len(gc.game_account_password) == 0:
                log.error('未配置账号密码 请自行输入密码登录后再启动脚本')
                return Operation.round_wait()
            else:
                if self.try_login:  # 已经尝试过登录了 但没成功 就不再尝试 避免账号异常
                    return Operation.round_fail('登录失败')

                # 尝试点击切换到账号密码
                click1 = self.ocr_and_click_one_line('账号密码', enter_game_ui.LOGIN_SWITCH_PASSWORD_RECT_1,
                                                     screen=screen, lcs_percent=0.1, wait_after_success=1)
                click2 = self.ocr_and_click_one_line('账号密码', enter_game_ui.LOGIN_SWITCH_PASSWORD_RECT_2,
                                                     screen=screen, lcs_percent=0.1, wait_after_success=1)
                if click1 != Operation.OCR_CLICK_NOT_FOUND or click2 != Operation.OCR_CLICK_NOT_FOUND:
                    return Operation.round_wait(wait=1)

                # 输入账号
                self.ctx.controller.click(enter_game_ui.LOGIN_ACCOUNT_RECT.center)
                time.sleep(0.5)
                self.ctx.controller.input_str(gc.game_account)
                time.sleep(0.5)

                # 输入密码
                self.ctx.controller.click(enter_game_ui.LOGIN_PASSWORD_RECT.center)
                time.sleep(0.5)
                self.ctx.controller.input_str(gc.game_account_password)
                time.sleep(0.5)

                # 同意协议
                self.ctx.controller.click(enter_game_ui.LOGIN_ACCEPT_POINT)
                time.sleep(0.5)

                # 进入游戏
                self.ctx.controller.click(enter_game_ui.LOGIN_ENTER_GAME_RECT.center)

                self.try_login = True
                return Operation.round_wait(wait=3)

        if enter_game_ui.in_server_phase(screen, self.ctx.ocr):
            self.ctx.controller.click(enter_game_ui.SERVER_ENTER_GAME_RECT.center)
            time.sleep(1)  # 暂停一段时间再操作
            return Operation.round_wait()

        time.sleep(1)  # 暂停一段时间再操作
        return Operation.round_wait()
