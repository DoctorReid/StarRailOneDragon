import pyautogui
from pygetwindow import Win32Window


def get_win_by_name(window_name: str) -> Win32Window:
    """
    根据名称找到具体的窗口 需完全相等
    :param window_name: 窗口名称
    :return: Application
    :raise PyAutoGUIException
    """
    windows = pyautogui.getWindowsWithTitle(window_name)
    if len(windows) > 0:
        for win in windows:
            if win.title == window_name:
                return win
    raise pyautogui.PyAutoGUIException


def active_win(win: Win32Window):
    """
    切换到具体的窗口上
    :param win: 窗口
    :return: None
    :raise PyAutoGUIException 找不到对应窗口
    """
    if win is not None:
        win.activate()
    else:
        raise pyautogui.PyAutoGUIException
