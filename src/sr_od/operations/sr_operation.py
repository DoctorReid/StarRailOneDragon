from typing import Optional, Callable

from one_dragon.base.operation.operation import Operation
from one_dragon.base.operation.operation_base import OperationResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.base.geometry.rectangle import Rect
from one_dragon.base.geometry.point import Point
from sr_od.context.sr_context import SrContext
from sr_od.operations.enter_game.open_and_enter_game import OpenAndEnterGame
from sr_od.operations.reconnect_exception import ReconnectException


class SrOperation(Operation):

    def __init__(self, ctx: SrContext,
                 node_max_retry_times: int = 3,
                 op_name: str = '',
                 timeout_seconds: float = -1,
                 op_callback: Optional[Callable[[OperationResult], None]] = None,
                 need_check_game_win: bool = True
                 ):
        self.ctx: SrContext = ctx
        op_to_enter_game = OpenAndEnterGame(ctx)
        Operation.__init__(self,
                           ctx=ctx,
                           node_max_retry_times=node_max_retry_times,
                           op_name=op_name,
                           timeout_seconds=timeout_seconds,
                           op_callback=op_callback,
                           need_check_game_win=need_check_game_win,
                           op_to_enter_game=op_to_enter_game)

    def screenshot(self):
        screen = super().screenshot()
        self._check_reconnect_dialog(screen)
        return screen

    def _check_reconnect_dialog(self, screen):
        rect = Rect(780, 480, 1150, 550)
        part = cv2_utils.crop_image_only(screen, rect)
        ocr_result_map = self.ctx.ocr.run_ocr(part)
        for text in ocr_result_map.keys():
            if str_utils.find_by_lcs('与服务器断开连接，请重新登录', text, percent=0.6):
                self.ctx.controller.click(Point(985, 645))
                raise ReconnectException()
