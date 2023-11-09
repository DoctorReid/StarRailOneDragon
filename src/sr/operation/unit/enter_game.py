import time

from basic.i18_utils import gt
from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot import battle, enter_game_ui
from sr.operation import Operation


class EnterGame(Operation):
    """
    操作进入游戏
    主要为点击 点击进入 最终进入到游戏主界面 右上角看到角色的图标
    需保证游戏不需要登录
    以后再考虑加入选择账号登录功能
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx, try_times=2, op_name=gt('进入游戏', 'ui'))
        self.start_time = time.time()
        self.first_in_world_time: float = 0
        self.claim_express_supply: bool = False

    def init_before_execute(self):
        self.start_time = time.time()

    def _execute_one_round(self) -> int:
        screen = self.screenshot()

        if battle.IN_WORLD == battle.get_battle_status(screen, self.ctx.im):  # 进入到主界面
            now = time.time()
            if self.first_in_world_time == 0:
                self.first_in_world_time = now

            if self.claim_express_supply:  # 已经领取过列车补给
                return Operation.SUCCESS
            else:  # 没领列车补给的话 等2秒看看有没有
                if now - self.first_in_world_time > 2:
                    return Operation.SUCCESS
                else:
                    return Operation.WAIT

        if enter_game_ui.in_final_enter_phase(screen, self.ctx.ocr):  # 下方有 点击进入 的字样
            self.ctx.controller.click(enter_game_ui.FINAL_ENTER_GAME_RECT.center)
            time.sleep(1)  # 暂停一段时间再操作
            return Operation.WAIT

        if enter_game_ui.in_express_supply_phase(screen, self.ctx.ocr):  # 列车补给(小月卡) - 会先出现主界面
            self.ctx.controller.click(enter_game_ui.EMPTY_POS)
            time.sleep(3)  # 暂停一段时间再操作
            self.ctx.controller.click(enter_game_ui.EMPTY_POS)  # 领取需要分两个阶段 点击两次
            time.sleep(1)  # 暂停一段时间再操作
            self.claim_express_supply = True
            return Operation.WAIT

        if enter_game_ui.in_password_phase(screen, self.ctx.ocr):
            log.error('请自行输入密码登录后再启动脚本')
            return Operation.FAIL

        if enter_game_ui.in_server_phase(screen, self.ctx.ocr):
            self.ctx.controller.click(enter_game_ui.SERVER_ENTER_GAME_RECT.center)
            time.sleep(1)  # 暂停一段时间再操作
            return Operation.WAIT

        if time.time() - self.start_time > 180:  # 不应该这么久都没加载完游戏
            log.error('进入游戏超时')
            return Operation.FAIL

        time.sleep(1)  # 暂停一段时间再操作
        return Operation.WAIT

