from basic import win_utils
import ctypes


def _test_active_win():
    win_utils.get_win_by_name('微信', active=True)


def _test_scroll():
    print(win_utils.get_mouse_sensitivity())
    win_utils.scroll(1)




























if __name__ == '__main__':
    _test_is_window_maximized()