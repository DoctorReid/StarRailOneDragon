import time

from one_dragon.base.config.one_dragon_config import InstanceRun
from one_dragon.base.controller.pc_clipboard import PcClipboard
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.i18_utils import gt
from sr_od.config.game_config import TypeInputWay
from sr_od.context.sr_context import SrContext
from sr_od.operations.back_to_normal_world_plus import BackToNormalWorldPlus
from sr_od.operations.sr_operation import SrOperation


class EnterGame(SrOperation):

    def __init__(self, ctx: SrContext, switch: bool = False):
        """
        进入游戏后 进行登陆
        :param ctx:
        """
        SrOperation.__init__(self, ctx, op_name=gt('进入游戏', 'ui'))

        self.force_login: bool = (self.ctx.one_dragon_config.instance_run == InstanceRun.ALL.value.value
            and len(self.ctx.one_dragon_config.instance_list_in_od) > 1)

        # 切换账号的情况下 一定需要登录
        if switch:
            self.force_login = True

        self.already_login: bool = False  # 是否已经登录了
        self.use_clipboard: bool = self.ctx.game_config.type_input_way == TypeInputWay.CLIPBOARD.value.value  # 使用剪切板输入

    @node_from(from_name='国服-输入账号密码')
    @node_from(from_name='登陆其他账号')
    @operation_node(name='画面识别', node_max_retry_times=60, is_start_node=True)
    def check_screen(self) -> OperationRoundResult:
        screen = self.screenshot()

        if self.force_login and not self.already_login:
            result = self.round_by_find_area(screen, '进入游戏', '文本-点击进入')
            if result.is_success:
                result2 = self.round_by_find_and_click_area(screen, '进入游戏', '按钮-登出确定')
                if result2.is_success:
                    return self.round_wait(result2.status, wait=2)

                result2 = self.round_by_find_area(screen, '进入游戏-退出登陆', '标题-退出登录')
                if result2.is_success:
                    return self.round_success(result2.status)

                result2 = self.round_by_find_and_click_area(screen, '进入游戏', '按钮-登出')
                if result2.is_success:
                    return self.round_wait(result2.status, wait=1)

                return self.round_retry(result2.status, wait=1)
            else:
                result2 = self.round_by_find_and_click_area(screen, '进入游戏-选择账号', '按钮-登陆其他账号')
                if result2.is_success:
                    return self.round_wait(result2.status, wait=1)
        else:
            result = self.round_by_find_and_click_area(screen, '进入游戏', '文本-点击进入')
            if result.is_success:
                return self.round_success(result.status, wait=5)

        result = self.round_by_find_and_click_area(screen, '进入游戏', '国服-账号密码')
        if result.is_success:
            return self.round_success(result.status, wait=1)

        result = self.round_by_find_and_click_area(screen, '进入游戏', '文本-开始游戏')
        if result.is_success:
            return self.round_wait(result.status, wait=1)

        return self.round_retry(wait=1)

    @node_from(from_name='画面识别', status='国服-账号密码')
    @operation_node(name='国服-输入账号密码')
    def input_account_password(self) -> OperationRoundResult:
        if self.ctx.game_account_config.account == '' or self.ctx.game_account_config.password == '':
            return self.round_fail('未配置账号密码')

        screen = self.screenshot()
        self.round_by_click_area('进入游戏', '国服-账号输入区域')
        time.sleep(0.5)
        if self.use_clipboard:
            PcClipboard.copy_and_paste(self.ctx.game_account_config.account)
        else:
            self.ctx.controller.keyboard_controller.keyboard.type(self.ctx.game_account_config.account)
        time.sleep(1.5)

        self.round_by_click_area('进入游戏', '国服-密码输入区域')
        time.sleep(0.5)
        if self.use_clipboard:
            PcClipboard.copy_and_paste(self.ctx.game_account_config.password)
        else:
            self.ctx.controller.keyboard_controller.keyboard.type(self.ctx.game_account_config.password)
        time.sleep(1.5)

        result = self.round_by_find_area(screen, '进入游戏', '文本-同意-旧')
        if result.is_success:
            self.round_by_click_area('进入游戏', '国服-同意按钮-旧')

        result = self.round_by_find_area(screen, '进入游戏', '文本-同意-新')
        if result.is_success:
            self.round_by_click_area('进入游戏', '国服-同意按钮')
        time.sleep(0.5)

        screen = self.screenshot()
        self.already_login = True
        return self.round_by_find_and_click_area(screen, '进入游戏', '国服-账号密码进入游戏',
                                                 success_wait=5, retry_wait=1)

    @node_from(from_name='画面识别', status='文本-点击进入')
    @operation_node(name='等待画面加载')
    def wait_game(self) -> OperationRoundResult:
        op = BackToNormalWorldPlus(self.ctx)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='画面识别', status='标题-退出登录')
    @operation_node(name='退出并保留登陆记录')
    def logout_with_account_kept(self) -> OperationRoundResult:
        screen = self.screenshot()
        self.round_by_click_area('进入游戏-退出登陆', '按钮-退出并保留登陆记录', success_wait=1)
        return self.round_by_find_and_click_area(screen, '进入游戏-退出登陆', '按钮-退出',
                                                 success_wait=1, retry_wait=1)

    @node_from(from_name='退出并保留登陆记录')
    @operation_node(name='登陆其他账号')
    def choose_other_account(self) -> OperationRoundResult:
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '进入游戏-选择账号', '按钮-登陆其他账号',
                                                 success_wait=1, retry_wait=1)


def __debug():
    ctx = SrContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    ctx.start_running()
    app = EnterGame(ctx, switch=True)
    app.execute()


if __name__ == '__main__':
    __debug()