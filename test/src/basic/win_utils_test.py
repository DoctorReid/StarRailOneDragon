from basic import win_utils
import ctypes


def _test_active_win():
    win_utils.get_win_by_name('唯秘', active=True)


if __name__ == '__main__':
    _test_active_win()