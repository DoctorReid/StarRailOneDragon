from typing import ClassVar, Optional

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import StateOperation, StateOperationNode, StateOperationEdge, OperationOneRoundResult, Operation, \
    OperationResult
from sr.screen_area.dialog import ScreenDialog


class SwitchMember(StateOperation):

    STATUS_CONFIRM: ClassVar[str] = '确认'

    def __init__(self, ctx: Context, num: int,
                 skip_first_screen_check: bool = False,
                 skip_resurrection_check: bool = False):
        """
        切换角色 需要在大世界页面
        :param ctx:
        :param num: 第几个队友 从1开始
        :param skip_first_screen_check: 是否跳过第一次画面状态检查
        :param skip_resurrection_check: 跳过复活检测 逐光捡金中可跳过
        """
        edges = []

        switch = StateOperationNode('切换', self._switch)
        confirm = StateOperationNode('确认', self._confirm)
        edges.append(StateOperationEdge(switch, confirm))

        wait = StateOperationNode('等待', self._wait_after_confirm)
        edges.append(StateOperationEdge(confirm, wait, status=SwitchMember.STATUS_CONFIRM))

        edges.append(StateOperationEdge(wait, switch))  # 复活后需要再按一次切换

        super().__init__(ctx, try_times=5,
                         op_name='%s %d' % (gt('切换角色', 'ui'), num),
                         edges=edges, specified_start_node=switch)

        self.num: int = num
        self.skip_first_screen_check: bool = skip_first_screen_check  # 是否跳过第一次的画面状态检查 用于提速
        self.first_screen_check: bool = True  # 是否第一次检查画面状态
        self.skip_resurrection_check: bool = skip_resurrection_check  # 跳过复活检测

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        self.first_screen_check = True

        return None

    def _switch(self) -> OperationOneRoundResult:
        first = self.first_screen_check
        self.first_screen_check = False
        if first and self.skip_first_screen_check:
            pass
        else:
            screen = self.screenshot()
            if not screen_state.is_normal_in_world(screen, self.ctx.im):
                return self.round_retry('未在大世界页面', wait=1)

        self.ctx.controller.switch_character(self.num)
        return self.round_success(wait=1)

    def _confirm(self) -> OperationOneRoundResult:
        """
        复活确认
        :return:
        """
        if self.skip_resurrection_check:
            return self.round_success()

        screen = self.screenshot()
        if screen_state.is_normal_in_world(screen, self.ctx.im):  # 无需复活
            return self.round_success()

        if self.find_area(ScreenDialog.FAST_RECOVER_NO_CONSUMABLE.value, screen):
            area = ScreenDialog.FAST_RECOVER_CANCEL.value
        else:
            area = ScreenDialog.FAST_RECOVER_CONFIRM.value

        click = self.find_and_click_area(area, screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(area.status, wait=1)
        else:
            return self.round_retry('点击%s失败' % area.status, wait=1)

    def _wait_after_confirm(self) -> OperationOneRoundResult:
        """
        等待回到大世界画面
        :return:
        """
        screen = self.screenshot()
        if screen_state.is_normal_in_world(screen, self.ctx.im):
            return self.round_success()
        else:
            return self.round_retry('未在大世界画面', wait=1)

    def _after_operation_done(self, result: OperationResult):
        super()._after_operation_done(result)

        if not result.success or \
                ScreenDialog.FAST_RECOVER_CANCEL.value == result.status:
            # 指令出错 或者 没药复活 导致切换失败
            # 将当前角色设置成一个非法的下标 这样就可以让所有依赖这个的判断失效
            self.ctx.team_info.current_active = -1
        else:
            self.ctx.team_info.current_active = self.num - 1
