import os

import cv2

from basic.img import cv2_utils
from basic.img.os import get_debug_image_dir, get_test_image, save_debug_image
from sr.context import get_context, Context
from sr.image.sceenshot import mini_map


def _test_extract_arrow(ctx: Context):
    dir = get_debug_image_dir()
    for filename in os.listdir(dir):
        screen = cv2_utils.read_image(os.path.join(dir, filename))
    # for i in range(5):
    #     screen = get_test_image('game%d' % (i+1))
        mm = ctx.map_cal.cut_mini_map(screen)
        cv2_utils.show_image(mm, win_name='mm')
        arrow = mini_map.extract_arrow(mm)
        cv2_utils.show_image(arrow, win_name='arrow')
        _, bw = cv2.threshold(arrow, 180, 255, cv2.THRESH_BINARY)
        cv2_utils.show_image(bw, win_name='bw')
        raw_arrow = cv2.bitwise_and(mm, mm, mask=bw)
        cv2_utils.show_image(raw_arrow, win_name='raw_arrow')

        cv2.waitKey(0)
        cv2.destroyAllWindows()


def _test_get_arrow_template(ctx: Context):
    screen = get_test_image('mm_arrow')
    mm = ctx.map_cal.cut_mini_map(screen)
    one_template, all_template = mini_map.get_arrow_template(mm)
    cv2_utils.show_image(one_template, win_name='one')
    cv2_utils.show_image(all_template, win_name='all')
    save_debug_image(one_template)
    save_debug_image(all_template) # 最后复制到 images/template/arrow_one,arrow_all中 只保存mask即可
    cv2.waitKey(0)


def _test_get_angle_from_arrow(ctx: Context):
    screen = get_test_image('mm_arrow')
    mm = ctx.map_cal.cut_mini_map(screen)
    one_template, all_template = mini_map.get_arrow_template(mm)
    dir = get_debug_image_dir()
    for filename in os.listdir(dir):
        # if not filename.startswith('1695658291971'):
        #     continue
        screen = cv2_utils.read_image(os.path.join(dir, filename))
        mm = ctx.map_cal.cut_mini_map(screen)
        cv2_utils.show_image(mm, win_name='mm')
        arrow, _ = mini_map.get_arrow_mask(mm)
        cv2_utils.show_image(arrow, win_name='arrow')
        answer = mini_map.get_angle_from_arrow(arrow, all_template, one_template, ctx.im, show=True)
        print(answer)
        cv2.waitKey(0)


if __name__ == '__main__':
    ctx = get_context('唯秘')
    _test_get_arrow_template(ctx)