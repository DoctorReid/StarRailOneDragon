import os
import time

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import os_utils
from basic.img import cv2_utils
from basic.img.os import get_debug_image_dir, get_test_image, save_debug_image, get_debug_image
from basic.log_utils import log
from sr.config import game_config
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.image.sceenshot import mini_map, mini_map_angle_alas


def _test_extract_arrow():
    dir = get_debug_image_dir()
    for filename in os.listdir(dir):
        screen = cv2_utils.read_image(os.path.join(dir, filename))
    # for i in range(5):
    #     screen = get_test_image('game%d' % (i+1))
        mm = mini_map.cut_mini_map(screen)
        cv2_utils.show_image(mm, win_name='mm')
        arrow = mini_map.extract_arrow(mm)
        cv2_utils.show_image(arrow, win_name='arrow')
        _, bw = cv2.threshold(arrow, 180, 255, cv2.THRESH_BINARY)
        cv2_utils.show_image(bw, win_name='bw')
        raw_arrow = cv2.bitwise_and(mm, mm, mask=bw)
        cv2_utils.show_image(raw_arrow, win_name='raw_arrow')

        cv2.waitKey(0)
        cv2.destroyAllWindows()


def _test_get_arrow_mask():
    screen = get_debug_image('1697036916493')
    mm = mini_map.cut_mini_map(screen)
    m, wm = mini_map.get_arrow_mask(mm)
    cv2_utils.show_image(m, win_name='m')
    cv2_utils.show_image(wm, win_name='wm')
    cv2.waitKey(0)


def _test_analyse_arrow_and_angle():
    screen = get_debug_image('1697036916493')
    mm = mini_map.cut_mini_map(screen)
    _, _, angle = mini_map.analyse_arrow_and_angle(mm, im)
    print(angle)


def _test_all_get_angle_from_arrow():
    """
    用箭头匹配角度 测试所有角度
    结果发现误差较大 效率也低
    :return:
    """
    mm = get_test_image('mm_arrow', sub_dir='mini_map')
    max_delta = 0
    for i in range(360):
        to_test = cv2_utils.image_rotate(mm, -i)
        t1 = time.time()
        center_arrow_mask, arrow_mask = mini_map.get_arrow_mask(to_test)
        angle = mini_map.get_angle_from_arrow(center_arrow_mask, im, show=False)
        # print(time.time() - t1)
        # cv2.waitKey(0)
        expect = i
        delta = abs(angle - expect)
        if delta > 180:
            delta = 360 - delta
        if delta > max_delta:
            max_delta = delta
            print(max_delta)
        # if abs(angle - expect) > 2:
        #     print(i, expect, angle)
        #     break
    print(max_delta)


def test_get_angle_new():
    mm = get_test_image('mm_arrow', sub_dir='mini_map')
    max_delta = 0
    for i in range(100):
        to_test = cv2_utils.image_rotate(mm, -i)
        t1 = time.time()
        angle = mini_map_angle_alas.calculate(to_test)
        print(i, angle)
        print(time.time() - t1)
        if abs(i - angle) > max_delta:
            max_delta = abs(i - angle)
    print(max_delta)


def _test_get_sp_mask_by_feature_match():
    screen: MatLike = get_debug_image('1696773991417')
    mm = mini_map.cut_mini_map(screen)
    info = mini_map.analyse_mini_map(mm, im)

    mini_map.get_sp_mask_by_feature_match(info, im, show=True)
    cv2.waitKey(0)


def _test_radio_mask():
    screen = get_debug_image('1697036262088')
    mm = mini_map.cut_mini_map(screen)
    road = np.zeros_like(mm, dtype=np.uint8)
    road[:,:] = [65,65,65]
    ans = cv2.subtract(mm, road)
    cv2_utils.show_image(ans, win_name='ans')
    cv2.waitKey(0)


def _test_get_enemy_road_mask():
    pass


def _test_cut_mini_map():
    screen = get_debug_image('_1705934808671')
    mm = mini_map.cut_mini_map(screen)
    save_debug_image(mm)
    # dir = get_debug_image_dir()
    # for x in os.listdir(dir):
    #     if not x.endswith('.png'):
    #         continue
    #     screen = cv2_utils.read_image(os.path.join(dir, x))
    #     mm = mc.cut_mini_map(screen)
    #     save_debug_image(mm)


def _test_is_under_attack():
    mm_pos = game_config.get().mini_map_pos

    mm = get_test_image('under_1', sub_dir='battle')
    assert mini_map.is_under_attack(mm, mm_pos=mm_pos, show=False, strict=False)  # True

    mm = get_test_image('under_2', sub_dir='battle')
    assert mini_map.is_under_attack(mm, mm_pos=mm_pos, show=False, strict=True)  # True

    mm = get_test_image('under_3', sub_dir='battle')
    assert not mini_map.is_under_attack(mm, mm_pos=mm_pos, show=False)  # False

    mm = get_test_image('under_4', sub_dir='battle')
    assert not mini_map.is_under_attack(mm, mm_pos=mm_pos, show=False, strict=True)  # False

    mm = get_test_image('under_5', sub_dir='battle')
    assert not mini_map.is_under_attack(mm, mm_pos=mm_pos, show=False, strict=True)  # False
    log.info('通过测试')


def _test_radio_color():
    """
    保存一个扇形雷达区域需要叠加的颜色
    :return:
    """
    mm = get_test_image('cal_radio', sub_dir='mini_map')

    cv2_utils.show_image(mm, win_name='mm')

    radius = mm.shape[0] // 2 - 20
    d = radius * 2 + 1
    mask = np.zeros((d, d), dtype=np.uint8)
    center = (d // 2, d // 2)
    print(radius)
    start_angle = - 46  # 扇形起始角度（以度为单位）
    end_angle = 46  # 扇形结束角度（以度为单位）
    cv2.ellipse(mask, center, (radius, radius), 0, start_angle, end_angle, 255, -1)  # 画扇形
    cv2_utils.show_image(mask, win_name='mask')

    x1 = mm.shape[1] // 2 - radius
    x2 = x1 + d
    y1 = mm.shape[1] // 2 - radius
    y2 = y1 + d

    to_del = np.zeros((d, d, 3), dtype=np.int8)
    to_del[:,:] = mm[y1:y2, x1:x2]
    to_del -= 55
    to_del = cv2.bitwise_and(to_del, to_del, mask=mask)

    new_mm = mm.copy()
    new_mm[y1:y2, x1:x2] = new_mm[y1:y2, x1:x2] - to_del
    new_mm[np.where(new_mm < 0)] = 0

    cv2_utils.show_image(new_mm, win_name='new_mm', wait=0)

    save_template_image(to_del, 'mini_map_radio', 'origin')
    save_template_image(mask, 'mini_map_radio', 'mask')

    template = ih.get_template('mini_map_radio')
    to_del = template.origin

    new_mm_2 = mm.copy()
    new_mm_2[y1:y2, x1:x2] = new_mm_2[y1:y2, x1:x2] - to_del
    new_mm_2[np.where(new_mm < 0)] = 0

    cv2_utils.show_image(new_mm_2, win_name='new_mm_2', wait=0)


def save_template_image(img: MatLike, template_id: str, tt: str):
    """
    保存模板图片
    :param img: 模板图片
    :param template_id: 模板id
    :param tt: 模板类型
    :return:
    """
    path = os_utils.get_path_under_work_dir('images', 'template', template_id)
    print(path)
    print(cv2.imwrite(os.path.join(path, '%s.png' % tt), img))


if __name__ == '__main__':
    ih = ImageHolder()
    im = CvImageMatcher(ih)
    _test_cut_mini_map()