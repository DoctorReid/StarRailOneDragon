import ctypes
import os
import time
from functools import lru_cache
from typing import Union

import cv2
import numpy as np
import pyautogui
from PIL.Image import Image
from cv2.typing import MatLike
from pygetwindow import Win32Window

from basic import Point

SPI_GETMOUSESPEED = 0x0070


def get_win_by_name(window_name: str, active: bool = False) -> Win32Window:
    """
    根据名称找到具体的窗口 需完全相等
    :param window_name: 窗口名称
    :param active: 是否自动激活置顶窗口
    :return: Application
    :raise PyAutoGUIException
    """
    windows = pyautogui.getWindowsWithTitle(window_name)
    if len(windows) > 0:
        for win in windows:
            if win.title == window_name:
                if active:
                    active_win(win)
                return win
    raise pyautogui.PyAutoGUIException


def active_win(win: Win32Window):
    """
    切换到具体的窗口上
    :param win: 窗口
    :return: None
    """
    if win is not None and not win.isActive:
        try:
            win.restore()
            win.activate()
        except Exception:  # 比较神奇的一个bug 直接activate有可能失败 https://github.com/asweigart/PyGetWindow/issues/16#issuecomment-1110207862
            win.minimize()
            win.restore()
            win.activate()


def is_active_win(win: Win32Window) -> bool:
    """
    判断窗口是否最前激活
    :param win: 窗口
    :return: 是否最前激活 空窗口返回False
    """
    return win.isActive if win is not None else False


def is_active_win_by_name(window_name: str):
    """
    根据窗口名称判断窗口是否最前激活
    :param window_name: 窗口名称
    :return: 如果窗口不存在 返回False 否则返回是否激活
    """
    try:
        win = get_win_by_name(window_name)
        return is_active_win(win)
    except pyautogui.PyAutoGUIException:
        return False


def shutdown_sys(seconds: int):
    """
    使用 shutdown -s -t ${seconds} 来关闭系统
    :param seconds: 秒
    :return:
    """
    os.system("shutdown /s /t %d" % seconds)


def cancel_shutdown_sys():
    """
    取消计划的自动关机
    使用 shutdown /a 命令
    :return:
    """
    os.system("shutdown /a")


def screenshot_win(win: Union[str, Win32Window]) -> MatLike:
    """
    激活窗口然后对屏幕截图 截取窗口所在区域
    :param win: 窗口名称 或 具体窗口
    :param save_path: 保存路径
    :return:
    """
    if type(win) == str:
        target = get_win_by_name(win)
    elif type(win) == Win32Window:
        target = win
    else:
        return None

    active_win(target)
    left = target.left
    top = target.top
    width = target.width
    height = target.height
    return screenshot(left, top, width, height)


def screenshot(left, top, width, height) -> MatLike:
    """
    对屏幕区域截图
    :param left:
    :param top:
    :param width:
    :param height:
    :return:
    """
    img: Image = pyautogui.screenshot(region=(left, top, width, height))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def click(pos: Point = None, press_time: float = 0, primary: bool = True):
    """
    点击鼠标
    :param pos: 屏幕坐标
    :param press_time: 按住时间
    :param primary: 是否点击鼠标主要按键（通常是左键）
    :return:
    """
    btn = pyautogui.PRIMARY if primary else pyautogui.SECONDARY
    if pos is None:
        pos = get_current_mouse_pos()
    if press_time > 0:
        pyautogui.moveTo(pos.x, pos.y)
        pyautogui.mouseDown(button=btn)
        time.sleep(press_time)
        pyautogui.mouseUp(button=btn)
    else:
        pyautogui.click(pos.x, pos.y, button=btn)


def drag_mouse(start: Point, end: Point, duration: float = 0.5):
    """
    按住鼠标左键进行画面拖动
    :param start: 原位置
    :param end: 拖动位置
    :param duration: 拖动鼠标到目标位置，持续秒数
    :return:
    """
    pyautogui.moveTo(start.x, start.y)  # 将鼠标移动到起始位置
    pyautogui.dragTo(end.x, end.y, duration=duration)


def move_mouse_in_place(dx: int, dy: int, duration: float = 0.5):
    """
    原地移动鼠标
    :param dx: 偏移量
    :param dy: 偏移量
    :param duration: 时间
    :return:
    """
    p = pyautogui.position()
    pyautogui.moveTo(p.x + dx, p.y + dy, duration=duration)


def key_down(k: str, t: int, asyn: bool = False):
    """
    键盘按键
    :param k: 按键
    :param t: 持续时间
    :param asyn: 是否异步 未实现
    :return:
    """
    pyautogui.keyDown(k)
    time.sleep(t)
    pyautogui.keyUp(k)


def scroll(clicks: int, pos: Point = None):
    """
    向下滚动
    :param clicks: 负数时为相上滚动
    :param pos: 滚动位置 不传入时为鼠标当前位置
    :return:
    """
    if pos is not None:
        pyautogui.moveTo(pos.x, pos.y)
    d = 2000 if get_mouse_sensitivity() <= 10 else 1000
    pyautogui.scroll(-d * clicks, pos.x, pos.y)


@lru_cache
def get_mouse_sensitivity():
    """
    获取鼠标灵敏度
    :return:
    """
    user32 = ctypes.windll.user32
    speed = ctypes.c_int()
    user32.SystemParametersInfoA(SPI_GETMOUSESPEED, 0, ctypes.byref(speed), 0)
    print(speed.value)
    return speed.value


def get_current_mouse_pos() -> Point:
    """
    获取鼠标当前坐标
    :return:
    """
    pos = pyautogui.position()
    return Point(pos.x, pos.y)
