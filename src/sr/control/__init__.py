import cv2
from cv2.typing import MatLike

from basic.img import MatchResultList
from sr.app import get_context, Context


class GameController:

    def __init__(self):
        pass

    def init(self):
        pass

    def esc(self) -> bool:
        return False

    def open_map(self) -> bool:
        pass

    def click_ocr(self, screen: MatLike, word: str, rect: tuple=None) -> bool:
        """
        在屏幕中点击关键词所在位置 多个关键词时随机点击一个
        :param screen: 屏幕截图
        :param word: 关键词
        :param rect: 圈定区域 (x,y,w,h) 默认分辨率下的游戏窗口里的坐标
        :return:
        """
        ctx: Context = get_context()
        x, y, w, h = word
        km = ctx.ocr.match_words(screen if rect is None else screen[y:y+h, x:x+w])
        if len(km) == 0:
            return False
        for v in km.values():  # -> MatchResultList
            return self.click((v.max.cx, v.max.cy))

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
        :return: 截图
        """
        pass

    def scroll(self, down: int, pos: tuple = None):
        """
        向下滚动
        :param down: 负数时为相上滚动
        :param pos: 滚动位置
        :return:
        """
        pass