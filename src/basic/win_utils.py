import os
import time
from typing import Union, List

import cv2
import numpy as np
import pyautogui
from PIL.Image import Image
from cv2.typing import MatLike
from pygetwindow import Win32Window


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


def close_win_with_f4(win: Win32Window):
    """
    先切换到窗口 再使用 ALT+F4 对窗口进行关闭 可能只会最小化到任务栏
    :param win: 窗口
    :return: None
    :raise PyAutoGUIException 找不到对应窗口
    """
    if win is not None:
        win.activate()
        pyautogui.hotkey('alt', 'f4')
    else:
        raise pyautogui.PyAutoGUIException


def close_win_with_f4_by_name(window_name: str):
    """
    根据窗口名称
    先切换到窗口 再使用 ALT+F4 对窗口进行关闭 可能只会最小化到任务栏
    :param window_name: 窗口名称
    :return: None
    :raise PyAutoGUIException 找不到对应窗口
    """
    win: Win32Window = get_win_by_name(window_name)
    close_win_with_f4(win)


def shutdown_sys(seconds: int):
    """
    ${minutes} 秒后自动关机
    使用 shutdown -s -t ${minutes} 来关闭系统
    :param seconds: 秒
    :return:
    """
    os.system("shutdown -s -t %d" % seconds)


def cancel_shutdown_sys():
    """
    取消计划的自动关机
    使用 shutdown -a 命令
    :return:
    """
    os.system("shutdown -a")


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


def scroll_with_mouse_press(pos: List, down_distance: int = 50, duration: float = 0.5):
    """
    按住鼠标左键进行画面拖动
    :param pos: 位置
    :param down_distance: 向下滑动的距离
    :param duration: 拖动鼠标到目标位置，持续秒数
    :return:
    """
    pyautogui.moveTo(pos[0], pos[1])  # 将鼠标移动到起始位置
    pyautogui.dragTo(pos[0], pos[1] - down_distance, duration=duration)


def key_down(k: str, t: int, asyn: bool = False):
    """

    :param k:
    :param t:
    :param asyn:
    :return:
    """
    pyautogui.keyDown(k)
    time.sleep(t)
    pyautogui.keyUp(k)