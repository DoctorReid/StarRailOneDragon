import cv2
from cv2.typing import MatLike

from sr.win import Window


def fill_uid_black(screen: MatLike, win: Window = None):
    """
    将截图的UID部分变成黑色
    :param screen: 屏幕截图
    :param win: 窗口
    :return: 没有UID的新图
    """
    img = screen.copy()
    lt = (30, 1030)
    rb = (200, 1080)
    if win is None:
        cv2.rectangle(img, lt, rb, (0, 0, 0), -1)
    else:
        cv2.rectangle(img, win.game_pos(lt), win.game_pos(rb), (0, 0, 0), -1)
    return img