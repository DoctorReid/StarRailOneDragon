import cv2

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

    def click_ocr(self, screen: cv2.typing.MatLike, word: str, rect: tuple=None) -> bool:
        """
        在屏幕中点击关键词所在位置 多个关键词时随机点击一个
        :param screen: 屏幕截图
        :param word: 关键词
        :param rect: 圈定区域 (x,y,w,h)
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
        """点击位置"""
        pass

    def screenshot(self) -> cv2.typing.MatLike:
        pass