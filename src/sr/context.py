import keyboard
import pyautogui
from sentry_sdk.integrations import threading

from basic.i18_utils import gt
from basic.log_utils import log
from sr.control import GameController
from sr.control.pc_controller import PcController
from sr.image import ImageMatcher, OcrMatcher
from sr.image.cnocr_matcher import CnOcrMatcher
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.win import Window


class Context:

    def __init__(self):
        self.platform: str = 'PC'
        self.ih: ImageHolder = ImageHolder()
        self.im: ImageMatcher = None
        self.ocr: OcrMatcher = None
        self.controller: GameController = None
        self.running: int = 0  # 0-停止 1-运行 2-暂停
        self.press_event: dict = {}
        self.pause_callback: dict = {}
        self.resume_callback: dict = {}
        self.stop_callback: dict = {}

        keyboard.on_press(self.on_key_press)
        self.register_key_press('f9', self.switch)
        self.register_key_press('f10', self.stop_running)
        self.register_key_press('f11', self.screenshot)
        if self.platform == 'PC':
            self.register_key_press('f12', self.stop_running)

        self.init_status: int = 0

    def register_key_press(self, key, callback):
        if key not in self.press_event:
            self.press_event[key] = []
        self.press_event[key].append(callback)

    def on_key_press(self, event):
        k = event.name
        if k in self.press_event:
            log.debug('触发按键 %s', k)
            for callback in self.press_event[k]:
                callback()

    def start_running(self) -> bool:
        if self.running != 0:
            log.error('不处于停止状态 当前状态(%d) 启动失败', self.running)
            return False

        self.running = 1
        self.controller.init()
        return True

    def stop_running(self):
        log.info('停止运行')
        self.running = 0
        t = threading.Thread(target=self.after_stop)
        t.start()

    def after_stop(self):
        for obj_id, callback in self.stop_callback.items():
            callback()

    def switch(self):
        if self.running == 1:
            log.info('暂停运行')
            self.running = 2
            for obj_id, callback in self.pause_callback.items():
                callback()
        elif self.running == 2:
            log.info('恢复运行')
            self.running = 1
            for obj_id, callback in self.resume_callback.items():
                callback()
        else:
            log.error('不处于运行状态 当前状态(%d) 启动失败', self.running)

    def register_pause(self, obj,
                       pause_callback,
                       resume_callback):
        self.pause_callback[id(obj)] = pause_callback
        self.resume_callback[id(obj)] = resume_callback

    def register_stop(self, obj, stop_callback):
        self.stop_callback[id(obj)] = stop_callback

    def unregister(self, obj):
        if id(obj) in self.pause_callback:
            del self.pause_callback[id(obj)]
        if id(obj) in self.resume_callback:
            del self.resume_callback[id(obj)]

    def init_controller(self, renew: bool = False) -> bool:
        if renew:
            self.controller = None
        try:
            if self.controller is None:
                if self.platform == 'PC':
                    win = Window(gt('崩坏：星穹铁道'))
                    self.controller = PcController(win=win, ocr=self.ocr)
        except pyautogui.PyAutoGUIException:
            log.error('未开打游戏')
            return False
        log.info('加载游戏控制器完毕')
        return True

    def init_image_matcher(self, renew: bool = False) -> bool:
        if renew:
            self.im = None
        if self.im is None:
            self.im = CvImageMatcher(self.ih)
        log.info('加载图片匹配器完毕')
        return True

    def init_ocr_matcher(self, renew: bool = False) -> bool:
        if renew:
            self.ocr = None
        if self.ocr is None:
            self.ocr = CnOcrMatcher()
        log.info('加载OCR识别器完毕')
        return True

    def init_all(self, renew: bool = False) -> bool:
        result: bool = True
        result = result and self.init_image_matcher(renew)
        result = result and self.init_ocr_matcher(renew)
        result = result and self.init_controller(renew)
        return result

    def mouse_position(self):
        rect = self.controller.win.get_win_rect()
        pos = pyautogui.position()
        print(pos.x - rect.x, pos.y - rect.y)

    def screenshot(self):
        self.controller.screenshot()


global_context: Context = Context()


def get_context() -> Context:
    global global_context
    return global_context
