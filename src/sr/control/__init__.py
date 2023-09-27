from cv2.typing import MatLike

from basic.img import cv2_utils
from basic.log_utils import log
from sr.image import OcrMatcher


class GameController:

    def __init__(self):
        self.ocr: OcrMatcher = None
        pass

    def init(self):
        pass

    def esc(self) -> bool:
        return False

    def open_map(self) -> bool:
        pass

    def click_ocr(self, screen: MatLike, word: str, threshold: float = 0.5, rect: tuple = None, click_offset: tuple = None,
                  press_time: int = 0,
                  ) -> bool:
        """
        在屏幕中点击关键词所在位置 多个关键词时随机点击一个
        :param screen: 屏幕截图
        :param word: 关键词
        :param threshold: 阈值
        :param rect: 圈定区域 (x,y,w,h) 默认分辨率下的游戏窗口里的坐标
        :param click_offset: 在匹配结果后 偏移多少进行点击
        :param press_time: 持续按的时间
        :return:
        """
        if rect is not None:
            x1, y1, x2, y2 = rect
        km = self.ocr.match_words(screen if rect is None else screen[y1:y2, x1:x2], words=[word], threshold=threshold)
        if len(km) == 0:
            return False
        for v in km.values():
            x, y = v.max.cx, v.max.cy
            if rect is not None:
                x += rect[0]
                y += rect[1]
            if click_offset is not None:
                x += click_offset[0]
                y += click_offset[1]
            log.debug('OCR识别 %s 成功 准备点击 (%d, %d)', word, x, y)
            return self.click((x, y), press_time=press_time)

    def click(self, pos: tuple = None, press_time: int = 0) -> bool:
        """
        点击位置
        :param pos: 点击位置 (x,y) 默认分辨率下的游戏窗口里的坐标
        :param press_time: 大于0时长按若干秒
        :return: 不在窗口区域时不点击 返回False
        """
        pass

    def screenshot(self) -> MatLike:
        """
        截图 如果分辨率和默认不一样则进行缩放
        :return: 缩放到默认分辨率的截图
        """
        pass

    def scroll(self, down: int, pos: tuple = None):
        """
        向下滚动
        :param down: 负数时为相上滚动
        :param pos: 滚动位置 默认分辨率下的游戏窗口里的坐标
        :return:
        """
        pass

    def drag_to(self, end: tuple, start: tuple = None, duration: float = 0.5):
        """
        按住拖拽
        :param end: 拖拽目的点
        :param start: 拖拽开始点
        :param duration: 拖拽持续时间
        :return:
        """
        pass