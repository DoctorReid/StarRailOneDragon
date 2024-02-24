import keyboard
import pyautogui

from basic.img import cv2_utils
from basic.img.os import save_debug_image
from basic.log_utils import log
from sr.app.application_base import Application
from sr.context import Context, get_context
from sr.control import GameController
from sr.image.sceenshot import fill_uid_black


class ScreenRecorder(Application):
    """
    开发用的截图工具
    按F10就截图一次
    按F11就打印当前鼠标在游戏窗口中的位置
    """

    def __init__(self, ctx: Context):
        super().__init__(ctx)
        self.ctrl: GameController = ctx.controller
        ctx.register_key_press('f11', self.screenshot)
        ctx.register_key_press('f12', self.mouse_position)

    def _execute_one_round(self):
        pass

    def screenshot(self):
        log.info('截图完成')
        img = self.ctrl.screenshot()
        no_uid = fill_uid_black(img, self.ctrl.win)
        cv2_utils.show_image(no_uid, win_name='no_uid')
        save_debug_image(no_uid)

    def mouse_position(self):
        rect = self.ctrl.win.get_win_rect()
        pos = pyautogui.position()
        print(pos.x - rect.x, pos.y - rect.y)


if __name__ == '__main__':
    ctx = get_context()
    r = ScreenRecorder(ctx)
    keyboard.wait('esc')
