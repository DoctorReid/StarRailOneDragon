import cv2
import numpy as np
import pyautogui

from basic import gui_utils, os_utils
from basic.img import cv2_utils
from dev import get_debug_image


def screenshot_game(no_uid: bool = True, save_result: bool = True, show_result: bool = False):
    """
    对游戏窗口进行截图
    :param no_uid: 是否屏幕uid部分
    :param save_result: 是否显示结果
    :return:
    """
    win = gui_utils.get_win_by_name('崩坏：星穹铁道', active=True)
    # 移开鼠标
    pyautogui.moveTo(1, 1)
    img = gui_utils.screenshot_win(win)
    if no_uid:
        img = cv2_utils.mark_area_as_transparent(img, [0, 1080, 200, 100])
    if show_result:
        cv2_utils.show_image(img)
    if save_result:
        path = get_debug_image('%s.png' % os_utils.now_timestamp_str())
        print(path)
        print(cv2.imwrite(path, img))
    return img


def screenshot_map_vertically(save_each: bool = False, save_merge: bool = True, show_merge: bool = False):
    """
    使用垂直滚动的方式对大地图进行截图，并进行垂直方向的拼接。
    结果图使用美图秀秀自动扣图和裁剪即可。
    :param save_each: 是否保存中间截图结果
    :param save_merge: 是否保存最终拼接结果
    :param show_merge: 是否显示最终拼接结果
    :return: 完整的大地图
    """
    win = gui_utils.get_win_by_name('崩坏：星穹铁道', active=True)
    # 先拉取到最上方
    gui_utils.scroll_with_mouse_press([win.topleft.x + 1300, win.topleft.y + 500], down_distance=-1000, duration=1)
    img = []
    # 每秒往下滚动一次截图
    for i in range(3):
        no_uid = screenshot_game(no_uid=False, save_result=False)
        map_part = no_uid[250: 900, 200: 1400]
        if len(img) == 0 or not np.array_equal(img[len(img) - 1], map_part):
            img.append(map_part)
            if save_each:
                path = get_debug_image('%s.png' % os_utils.now_timestamp_str())
                print(cv2.imwrite(path, map_part))
            gui_utils.scroll_with_mouse_press([win.topleft.x + 1300, win.topleft.y + 500], down_distance=300)

    merge = img[0]
    for i in range(len(img)):
        if i == 0:
            merge = img[i]
        else:
            merge = cv2_utils.concat_vertically(merge, img[i])

    if show_merge:
        cv2_utils.show_image(merge)

    if save_merge:
        path = get_debug_image('%s.png' % os_utils.now_timestamp_str())
        print(cv2.imwrite(path, merge))


if __name__ == '__main__':
    screenshot_game(save_result=True, show_result=False)