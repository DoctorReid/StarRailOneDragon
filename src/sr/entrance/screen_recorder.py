import cv2
import keyboard

from basic.img.os import save_debug_image
from sr.context import Context, get_context
from sr.control import GameController
from sr.image.sceenshot import fill_uid_black


class ScreenRecorder:
    """
    按一次F8就截图一次
    """

    def __init__(self, ctx: Context):
        self.ctrl: GameController = ctx.controller
        ctx.register_key_press('f8', self.screenshot)

    def screenshot(self):
        img = self.ctrl.screenshot()
        no_uid = fill_uid_black(img, self.ctrl.win)
        save_debug_image(no_uid)


if __name__ == '__main__':
    ctx = get_context()
    keyboard.wait('esc')
