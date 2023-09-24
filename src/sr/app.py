import pyautogui

from basic import gui_utils
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
        self.map_cal: MapCalculator = None
        self.image: ImageHolder = None
        self.matcher: ImageMatcher = None
        self.ocr: OcrMatcher = None
        self.map_cal: MapCalculator = None
        self.controller: GameController = None
        self.running: bool = False


global_context: Context = None


def get_context() -> Context:
    global global_context
    if global_context is not None:
        return global_context
    try:
        win = Window(gt('崩坏：星穹铁道'))
    except pyautogui.PyAutoGUIException:
        log.error('未开打游戏')
        exit(1)
    global_context = Context()
    global_context.config = ConfigHolder()
    global_context.image = ImageHolder()
    global_context.matcher = CvImageMatcher(global_context.image)
    global_context.ocr = OcrMatcher()
    global_context.map_cal = MapCalculator(im=global_context.image, config=global_context.config)
    global_context.controller = PcController(win)
    return global_context


if __name__ == '__main__':


    ctx = get_context()


