from cv2.typing import MatLike

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

    def click_ocr(self, screen: MatLike, word: str, rect: tuple = None, click_offset: tuple = None) -> bool:
        """
        在屏幕中点击关键词所在位置 多个关键词时随机点击一个
        :param screen: 屏幕截图
        :param word: 关键词
        :param rect: 圈定区域 (x,y,w,h) 默认分辨率下的游戏窗口里的坐标
        :param click_offset: 在匹配结果后 偏移多少进行点击
        :return:
        """
        if rect is not None:
            x1, y1, x2, y2 = rect
        km = self.ocr.match_words(screen if rect is None else screen[y1:y2, x1:x2], words=[word])
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
            return self.click((x, y))

    def click(self, pos: tuple) -> bool:
        """
        点击位置
        :param pos: 点击位置 (x,y) 默认分辨率下的游戏窗口里的坐标
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