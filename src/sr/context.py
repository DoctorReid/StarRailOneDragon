import keyboard
import pyautogui

from basic.i18_utils import gt
from basic.log_utils import log
from sr.config import ConfigHolder
from sr.control import GameController
from sr.control.pc_controller import PcController
from sr.image import ImageMatcher, OcrMatcher
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.map_cal import MapCalculator
from sr.win import Window


class Context:

    def __init__(self):
        self.config: ConfigHolder = None
        self.map_cal: MapCalculator = None
        self.image: ImageHolder = None
        self.matcher: ImageMatcher = None
        self.ocr: OcrMatcher = None
        self.map_cal: MapCalculator = None
        self.controller: GameController = None
        self.running: bool = False
        self.press_event: dict = {}

        keyboard.on_press(self.on_key_press)
        self.register_key_press('f9', self.switch)

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

    def switch(self):
        if self.running:

            log.info('暂停运行')
            self.running = False
        else:
            log.info('恢复运行')
            self.running = True


global_context: Context = None


def get_context(win_title: str='崩坏：星穹铁道') -> Context:
    global global_context
    if global_context is not None:
        return global_context
    try:
        win = Window(gt(win_title))
        # win = Window(gt('Clash for Windows'))
    except pyautogui.PyAutoGUIException:
        log.error('未开打游戏')
        exit(1)
    global_context = Context()
    global_context.config = ConfigHolder()
    global_context.image = ImageHolder()
    global_context.matcher = CvImageMatcher(global_context.image)
    global_context.ocr = OcrMatcher()
    global_context.map_cal = MapCalculator(im=global_context.image, config=global_context.config)
    global_context.controller = PcController(win=win, ocr=global_context.ocr)
    return global_context