from typing import ClassVar, List

from cv2.typing import MatLike

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.operation import Operation, OperationOneRoundResult, StateOperation, StateOperationEdge, StateOperationNode
from sr.screen_area.screen_sim_uni import ScreenSimUni
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight


class SimUniExit(StateOperation):

    STATUS_EXIT_CLICKED: ClassVar[str] = '点击结算'
    STATUS_BACK_MENU: ClassVar[str] = '返回菜单'

    def __init__(self, ctx: Context):
        """
        模拟宇宙 结束并结算
        :param ctx:
        """
        edges: List[StateOperationEdge] = []

        check_screen = StateOperationNode('检测画面', self._check_screen)

        open_menu = StateOperationNode('打开菜单', self._open_menu)
        edges.append(StateOperationEdge(check_screen, open_menu))

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
                         specified_start_node=check_screen
                         )

    def _check_screen(self) -> OperationOneRoundResult:
        """
        检查屏幕
        这个指令作为兜底的退出模拟宇宙的指令 应该兼容当前处于模拟宇宙的任何一种场景
        :return:
        """
        screen = self.screenshot()
        state = screen_state.get_sim_uni_screen_state(
            screen, self.ctx.im, self.ctx.ocr,
            in_world=True,
            battle=True,
            battle_fail=True
        )
        if state == ScreenState.NORMAL_IN_WORLD.value:  # 只有在大世界画面才继续
            return self.round_success()
        elif state == ScreenState.BATTLE_FAIL.value:  # 战斗失败
            return self._fail_click_empty(screen)
        else:  # 其他情况 统一交给 battle 处理
            op = SimUniEnterFight(self.ctx)
            op_result = op.execute()
            if op_result.success:
                return self.round_wait()  # 重新判断
            else:
                return self.round_retry()

    def _open_menu(self) -> OperationOneRoundResult:
        """
        打开菜单 或者 战斗中的打开退出
        :return:
        """
        self.ctx.controller.esc()
        return self.round_success(wait=1)

    def _click_exit(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        area_list = [ScreenSimUni.MENU_EXIT.value, ScreenSimUni.BATTLE_EXIT.value]
        for area in area_list:
            click = self.find_and_click_area(area, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                return self.round_success(SimUniExit.STATUS_EXIT_CLICKED, wait=1)

        return self.round_success(SimUniExit.STATUS_BACK_MENU, wait=1)

    def _click_confirm(self) -> OperationOneRoundResult:
        """
        确认退出模拟宇宙
        :return:
        """
        screen = self.screenshot()
        area = ScreenSimUni.EXIT_DIALOG_CONFIRM.value

        click = self.find_and_click_area(area, screen)
        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(wait=6)
        else:
            return self.round_retry('点击%s失败' % area.status, wait=1)

    def _click_empty(self) -> OperationOneRoundResult:
        """
        结算画面点击空白
        :return:
        """
        screen = self.screenshot()
        area = ScreenSimUni.EXIT_EMPTY_TO_CONTINUE.value

        click = self.find_and_click_area(area, screen)
        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(wait=2)
        else:
            return self.round_retry('点击%s失败' % area.status, wait=1)

    def _fail_click_empty(self, screen: MatLike) -> OperationOneRoundResult:
        """
        战斗失败后 结算画面的点击空白
        :return:
        """
        area = ScreenSimUni.EXIT_EMPTY_TO_CONTINUE.value

        click = self.find_and_click_area(area, screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(wait=2)
        else:
            return self.round_retry('未在结算画面', wait=1)
