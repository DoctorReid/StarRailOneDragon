from typing import Union, ClassVar, Optional

from basic import Rect
from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult


class SimUniExit(Operation):

    STATUS_EXIT: ClassVar[str] = '结束并结算'
    EXIT_BTN: ClassVar[Rect] = Rect(1323, 930, 1786, 985)
    CONFIRM_BTN: ClassVar[Rect] = Rect(1022, 651, 1324, 697)

    def __init__(self, ctx: Context):
        """
        模拟宇宙 结束并结算
        :param ctx:
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' %
                                 (gt('模拟宇宙', 'ui'),
                                  gt('结束并结算', 'ui'))
                         )

        self.exit_clicked: bool = False  # 是否已经点击离开了

    def _init_before_execute(self):
        """
        执行前的初始化 注意初始化要全面 方便一个指令重复使用
        """
        super()._init_before_execute()
        self.exit_clicked = False

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        open_menu = self._try_open_menu(screen)
        if open_menu is not None:
            return open_menu

        if self.exit_clicked:
            click_confirm = self._click_confirm(screen)
            if click_confirm is not None:
                return click_confirm

            if screen_state.is_empty_to_close(screen, self.ctx.ocr):
                click = self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)
                if click:
                    return Operation.round_success(SimUniExit.STATUS_EXIT)
                else:
                    return Operation.round_retry('点击空白处失败', wait=1)
        else:
            click_exit = self._click_exit(screen)
            if click_exit is not None:
                return click_exit

        return Operation.round_retry('未知状态', wait=1)

    def _try_open_menu(self, screen) -> Optional[OperationOneRoundResult]:
        if self.exit_clicked:
            return None
        elif screen_state.is_normal_in_world(screen, self.ctx.im):
            self.ctx.controller.esc()  # 打开菜单
            return Operation.round_retry('未打开菜单', wait=1)

    def _click_exit(self, screen) -> Optional[OperationOneRoundResult]:
        click = self.ocr_and_click_one_line('结束并结算', SimUniExit.EXIT_BTN, screen)
        if click == Operation.OCR_CLICK_SUCCESS:
            self.exit_clicked = True
            return Operation.round_wait(wait=1)
        elif click == Operation.OCR_CLICK_FAIL:
            return Operation.round_retry('点击结束并结算失败', wait=1)
        else:
            return None

    def _click_confirm(self, screen) -> Optional[OperationOneRoundResult]:
        click = self.ocr_and_click_one_line('确认', SimUniExit.CONFIRM_BTN, screen)
        if click == Operation.OCR_CLICK_SUCCESS:
            self.exit_clicked = True
            return Operation.round_wait(wait=4)
        elif click == Operation.OCR_CLICK_FAIL:
            return Operation.round_retry('点击确认失败', wait=1)
        else:
            return None
