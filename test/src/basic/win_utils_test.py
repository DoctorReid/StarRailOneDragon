from basic import win_utils
import ctypes

if __name__ == '__main__':
    ctypes.windll.user32.mouse_event(0x0001, 100, 0)