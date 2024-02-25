import time
from typing import List

import sr.const
from basic.i18_utils import gt
from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot import battle, enter_game_ui, screen_state
from sr.operation import Operation, OperationOneRoundResult, StateOperation, StateOperationEdge, StateOperationNode
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.screen_area.dialog import ScreenDialog
from sr.screen_area.screen_login import ScreenLogin
from sr.screen_area.screen_phone_menu import ScreenPhoneMenu


class EnterGame(StateOperation):

    def __init__(self, ctx: Context):
        """
        打开游戏后 进行登陆
        :param ctx:
        """
        edges: List[StateOperationEdge] = []

        wait = StateOperationNode('等待登陆画面', self._wait)

        login = StateOperationNode('登陆', self._login)
        edges.append(StateOperationEdge(wait, login))

        enter = StateOperationNode('等待游戏加载', op=WaitEnterGame(ctx))
        edges.append(StateOperationEdge(login, enter))

        super().__init__(ctx, try_times=3,
                         op_name=gt('进入游戏', 'ui'),
                         edges=edges,
                         timeout_seconds=180)
        self.need_password: bool = False

    def _init_before_execute(self):
        super()._init_before_execute()
        self.need_password = False

    def _wait(self) -> OperationOneRoundResult:
        """
        等待画面加载
        :return:
        """
        screen = self.screenshot()

        area1 = ScreenLogin.LOGIN_BTN.value
        area2 = ScreenLogin.SWITCH_PASSWORD.value
        if self.find_area(area1, screen) and self.find_area(area2, screen):
            self.need_password = True
            return Operation.round_success()

        area = ScreenLogin.CONFIRM_START_GAME.value
        if self.find_area(area, screen):
            self.need_password = False
            return Operation.round_success()

        return Operation.round_wait(wait=1)

    def _login(self) -> OperationOneRoundResult:
        """
        登陆
        :return:
        """
        op = LoginWithPassword(self.ctx, self.need_password)
        return Operation.round_by_op(op.execute())


class LoginWithAnotherAccount(StateOperation):

    def __init__(self, ctx: Context):
        """
        退出登陆后重新登陆
        :param ctx:
        """
        edges: List[StateOperationEdge] = []

        logout = StateOperationNode('退出登陆', op=Logout(ctx))
        login = StateOperationNode('登陆', op=LoginWithPassword(ctx))
        edges.append(StateOperationEdge(logout, login))

        enter = StateOperationNode('等待游戏加载', op=WaitEnterGame(ctx))
        edges.append(StateOperationEdge(login, enter))

        super().__init__(ctx, try_times=50,
                         op_name=gt('切换登陆账号', 'ui'),
                         edges=edges,
                         # specified_start_node=login,
                         )


class Logout(StateOperation):

    def __init__(self, ctx: Context):
        """
        登出当前账号
        """
        edges: List[StateOperationEdge] = []

        back_menu = StateOperationNode('打开菜单', op=OpenPhoneMenu(ctx))
        back_to_login = StateOperationNode('返回登陆', self._back_to_login)
        edges.append(StateOperationEdge(back_menu, back_to_login))

        logout = StateOperationNode('登出', self._logout)
        edges.append(StateOperationEdge(back_to_login, logout))

        super().__init__(ctx, try_times=50,
                         op_name=gt('登出账号', 'ui'),
                         edges=edges)

    def _back_to_login(self) -> OperationOneRoundResult:
        """
        返回登陆页面
        :return:
        """
        # 偷工减料 暂时直接点击不做匹配
        click = self.ctx.controller.click(ScreenPhoneMenu.POWER_BTN.value.rect.center)

        if not click:
            return Operation.round_retry('点击返回登陆按钮失败', wait=1)

        time.sleep(2)

        screen = self.screenshot()

        area = ScreenDialog.BACK_TO_LOGIN_CONFIRM.value
        click = self.find_and_click_area(area, screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(wait=15)
        else:
            return Operation.round_retry('点击%s失败', area.text, wait=1)

    def _logout(self) -> OperationOneRoundResult:
        """
        登出
        :return:
        """
        area = ScreenLogin.LOGOUT.value
        click = self.find_and_click_area(area)

        if not click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_retry('点击%s失败' % area.text, wait=1)

        time.sleep(1)

        area = ScreenLogin.LOGOUT_CONFIRM.value
        click = self.find_and_click_area(area)
        if not click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(wait=1)
        else:
            return Operation.round_retry('点击%s失败' % area.text, wait=1)


class LoginWithPassword(StateOperation):

    def __init__(self, ctx: Context, need_password: bool = True):
        """
        输入密码登陆
        :param ctx:
        """
        edges: List[StateOperationEdge] = []

        wait = StateOperationNode('等待加载', self._wait)
        switch = StateOperationNode('切换账号密码', self._switch_to_password)
        edges.append(StateOperationEdge(wait, switch))

        login = StateOperationNode('进入游戏', self._enter_password)
        edges.append(StateOperationEdge(switch, login))

        server = StateOperationNode('开始游戏', self._server_enter_game)
        edges.append(StateOperationEdge(login, server))

        confirm = StateOperationNode('点击进入', self._confirm_enter_game)
        edges.append(StateOperationEdge(server, confirm))

        super().__init__(ctx, try_times=20,
                         op_name=gt('登陆账号', 'ui'),
                         edges=edges,
                         specified_start_node=wait if need_password else confirm
                         )

    def _wait(self) -> OperationOneRoundResult:
        """
        等待画面加载
        :return:
        """
        screen = self.screenshot()
        area = ScreenLogin.LOGIN_BTN.value

        if self.find_area(area, screen):
            return Operation.round_success()
        else:
            return Operation.round_retry('未在%s画面' % area.status, wait=1)

    def _switch_to_password(self) -> OperationOneRoundResult:
        """
        切换到输入账号密码的地方
        :return:
        """
        screen = self.screenshot()
        area = ScreenLogin.PASSWORD_INPUT.value

        if self.find_area(area, screen):
            return Operation.round_success()

        area = ScreenLogin.SWITCH_PASSWORD.value
        click = self.find_and_click_area(area, screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_wait(wait=1)
        else:
            return Operation.round_retry('点击%s失败' % area.text, wait=1)

    def _enter_password(self) -> OperationOneRoundResult:
        """
        输入账号密码登陆
        :return:
        """
        gc = self.ctx.game_config
        if len(gc.game_account) == 0 or len(gc.game_account_password) == 0:
            return Operation.round_fail('未配置账号密码')

        # 输入账号
        self.ctx.controller.click(ScreenLogin.ACCOUNT_INPUT.value.rect.center)
        time.sleep(0.5)
        self.ctx.controller.delete_all_input()
        self.ctx.controller.input_str(gc.game_account)
        time.sleep(0.5)

        # 输入密码
        self.ctx.controller.click(ScreenLogin.PASSWORD_INPUT.value.rect.center)
        time.sleep(0.5)
        self.ctx.controller.delete_all_input()
        self.ctx.controller.input_str(gc.game_account_password)
        time.sleep(0.5)

        # 同意协议
        self.ctx.controller.click(ScreenLogin.APPROVE.value.rect.center)
        time.sleep(0.5)

        # 进入游戏
        area = ScreenLogin.LOGIN_BTN.value
        click = self.find_and_click_area(area)
        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(wait=3)
        else:
            return Operation.round_retry('点击%s失败' % area.text, wait=1)

    def _server_enter_game(self) -> OperationOneRoundResult:
        """
        登陆后 在选择服务器页面点击 开始游戏
        :return:
        """
        screen = self.screenshot()
        area1 = ScreenLogin.SERVER_START_GAME.value
        click = self.find_and_click_area(area1, screen)
        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(wait=5)

        area2 = ScreenLogin.CONFIRM_START_GAME.value
        if self.find_area(area2, screen):  # 有可能不需要选择服务器
            return Operation.round_success()
        else:
            return Operation.round_retry('未在 %s 或 %s 画面' % (area1.status, area2.status), wait=1)

    def _confirm_enter_game(self) -> OperationOneRoundResult:
        """
        确认进入游戏
        :return:
        """
        screen = self.screenshot()
        area = ScreenLogin.CONFIRM_START_GAME.value
        click = self.find_and_click_area(area, screen)
        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(wait=5)
        else:
            return Operation.round_retry('未在%s画面' % area.status, wait=2)


class WaitEnterGame(Operation):

    def __init__(self, ctx: Context):
        """
        登陆游戏加载
        :param ctx:
        """
        super().__init__(ctx, try_times=3,
                         op_name=gt('等待游戏加载', 'ui'),
                         timeout_seconds=180)

        self.first_in_world_time: float = 0  # 第一次在大世界的时间
        self.claim_express_supply: bool = False  # 是否已经获取过列车补给

    def _init_before_execute(self):
        super()._init_before_execute()
        self.first_in_world_time = 0
        self.claim_express_supply = False

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        if screen_state.is_normal_in_world(screen, self.ctx.im):  # 进入到主界面
            now = time.time()
            if self.first_in_world_time == 0:
                self.first_in_world_time = now

            if self.claim_express_supply:  # 已经领取过列车补给
                self.ctx.first_transport = True
                return Operation.round_success()
            else:  # 没领列车补给的话 等2秒看看有没有
                if now - self.first_in_world_time > 2:
                    self.ctx.first_transport = True
                    return Operation.round_success()
                else:
                    return Operation.round_wait(wait=1)

        if enter_game_ui.in_express_supply_phase(screen, self.ctx.ocr):  # 列车补给(小月卡) - 会先出现主界面
            self.ctx.controller.click(sr.const.CLICK_TO_CONTINUE_POS)
            time.sleep(3)  # 暂停一段时间再操作
            self.ctx.controller.click(sr.const.CLICK_TO_CONTINUE_POS)  # 领取需要分两个阶段 点击两次
            time.sleep(1)  # 暂停一段时间再操作
            self.claim_express_supply = True
            return Operation.round_wait()

        return Operation.round_wait(wait=1)
