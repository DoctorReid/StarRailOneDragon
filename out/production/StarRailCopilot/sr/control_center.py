import time

from basic.img import OcrMatcher
from basic.img.cv2_matcher import CvImageMatcher
from basic.log_utils import log
from sr.config import ConfigHolder


class ControlCenter:

    def __init__(self):
        log.info('开始初始化加载')
        t = time.time()

        self.config_holder = ConfigHolder()
        log.info('加载配置')
        self.ocr_matcher = OcrMatcher()
        log.info('加载OCR')
        self.image_matcher = CvImageMatcher()
        log.info('加载图片识别')
