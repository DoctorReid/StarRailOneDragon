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

    def init_before_execute(self):
        self.start_time = time.time()

    def run(self) -> int:
        screen = self.screenshot()

        if battle.IN_WORLD == battle.get_battle_status(screen, self.ctx.im):  # 进入到主界面
            return Operation.SUCCESS

        if enter_game_ui.in_final_enter_phase(screen, self.ctx.ocr):  # 右上角有公告 或者 下方有 点击进入 的字样
            self.ctx.controller.click(enter_game_ui.FINAL_ENTER_GAME_RECT.center)
            time.sleep(1)  # 暂停一段时间再操作
            return Operation.WAIT

        if enter_game_ui.in_express_supply_phase(screen, self.ctx.ocr):  # 列车补给 - 小月卡
            self.ctx.controller.click(enter_game_ui.EMPTY_POS)
            time.sleep(1)  # 暂停一段时间再操作
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

