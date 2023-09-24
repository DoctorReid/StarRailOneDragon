import keyboard

from sr.context import get_context

if __name__ == '__main__':
    ctx = get_context()
    keyboard.wait('esc')


