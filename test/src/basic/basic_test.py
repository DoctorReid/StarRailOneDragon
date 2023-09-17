from PIL.Image import Image

from basic import os_utils, gui_utils, config_utils
from basic.i18_utils import gt
from basic.log_utils import log


def _test_find_win():
    print(gui_utils.get_win_by_name('微信'))


def _test_switch_window():
    gui_utils.active_win(gui_utils.get_win_by_name('微信'))


def _test_close_win():
    gui_utils.close_win_with_f4_by_name('微信')


def _test_is_active_win():
    _test_switch_window()
    print(gui_utils.is_active_win_by_name('微信'))


def _test_log():
    for i in range(20):
        log.info("test %d" % i)


def _test_i18():
    print(gt('test'))
    print(gt('测试'))


def _test_work_dir():
    print(os_utils.get_work_dir())


def _test_screenshot():
    img: Image = gui_utils.screenshot_win_by_name('微信')
    img.show('测试')


def _test_save_img():
    img: Image = gui_utils.screenshot_win_by_name('微信')
    os_utils.save_image_under_work_dir(img, 'test.png', '.debug', 'images')


def _test_async_config():
    a = {'game': {'pos': 1}}
    b = {'game2': {'pos2': 1}}
    config_utils.deep_copy_missing_prop(a, b)
    print(b)
    config_utils.deep_del_extra_prop(a, b)
    print(b)
    config_utils.async_sample('game')


def _test_save_config():
    config_utils.save_config('game', {'little_map': {'x': 149, 'y': 196, 'r': 93}})


if __name__ == '__main__':
    _test_save_config()
