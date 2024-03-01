from typing import ClassVar, List

from basic.i18_utils import gt
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult, StateOperation, StateOperationEdge, StateOperationNode
from sr.screen_area.screen_sim_uni import ScreenSimUni


class SimUniExit(StateOperation):

    STATUS_EXIT_CLICKED: ClassVar[str] = '点击结算'
    STATUS_BACK_MENU: ClassVar[str] = '返回菜单'

    def __init__(self, ctx: Context, exit_clicked: bool = False):
        """
        模拟宇宙 结束并结算
        :param ctx:
        :param exit_clicked: 是否已经点击过退出了
        """
        edges: List[StateOperationEdge] = []

        open_menu = StateOperationNode('打开菜单', self._open_menu)
        click_exit = StateOperationNode('点击结算', self._click_exit)
        edges.append(StateOperationEdge(open_menu, click_exit))
        edges.append(StateOperationEdge(click_exit, open_menu, status=SimUniExit.STATUS_BACK_MENU))

        click_confirm = StateOperationNode('点击确认', self._click_confirm)
        edges.append(StateOperationEdge(click_exit, click_confirm, status=SimUniExit.STATUS_EXIT_CLICKED))

        click_empty = StateOperationNode('点击空白处继续', self._click_empty)
        edges.append(StateOperationEdge(click_confirm, click_empty))

        super().__init__(ctx, try_times=10,
                         op_name='%s %s' %
                                 (gt('模拟宇宙', 'ui'),
                                  gt('结束并结算', 'ui')),
                         edges=edges,
                         specified_start_node=open_menu
                         )

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()

    def _open_menu(self) -> OperationOneRoundResult:
        """
        打开菜单 或者 战斗中的打开退出
        :return:
        """
        self.ctx.controller.esc()
        return Operation.round_success(wait=1)

    def _click_exit(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        area_list = [ScreenSimUni.MENU_EXIT.value, ScreenSimUni.BATTLE_EXIT.value]
        for area in area_list:
            click = self.find_and_click_area(area, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                return Operation.round_success(SimUniExit.STATUS_EXIT_CLICKED, wait=1)

        return Operation.round_success(SimUniExit.STATUS_BACK_MENU, wait=1)

    def _click_confirm(self) -> OperationOneRoundResult:
        """
        确认退出模拟宇宙
        :return:
        """
        screen = self.screenshot()
        area = ScreenSimUni.EXIT_DIALOG_CONFIRM.value

        click = self.find_and_click_area(area, screen)
        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(wait=6)
        else:
            return Operation.round_retry('点击%s失败' % area.status, wait=1)

    def _click_empty(self) -> OperationOneRoundResult:
        """
        结算画面点击空白
        :return:
        """
        screen = self.screenshot()
        area = ScreenSimUni.EXIT_EMPTY_TO_CONTINUE.value

        click = self.find_and_click_area(area, screen)
        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(wait=2)
        else:
            return Operation.round_retry('点击%s失败' % area.status, wait=1)
