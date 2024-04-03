from basic import Point
from sr.control import GameController
from sr.image.ocr_matcher import OcrMatcher


class MockController(GameController):

    def __init__(self, ocr: OcrMatcher):
        """
        不做任何动作的控制器 用于测试
        """
        super().__init__(ocr)

    def click(self, pos: Point = None, press_time: float = 0, pc_alt: bool = False) -> bool:
        return True
