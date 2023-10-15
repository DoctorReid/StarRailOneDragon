import os

import cv2
import numpy as np

from basic import os_utils
from basic.img import cv2_utils
from basic.img.os import get_test_image
from sr.image import TemplateImage
from sr.image.sceenshot import icon


def _test_init_tp_with_background(template_id):
    icon.init_tp_with_background(template_id)

def _test_init_sp_with_background(template_id):
    icon.init_sp_with_background(template_id)


def _test_init_ui_icon(template_id):
    icon.init_ui_icon(template_id, noise_threshold=20)


def _test_init_arrow_template():
    mm = get_test_image('mm_arrow', sub_dir='mini_map')
    icon.init_arrow_template(mm)


def _test_init_template_feature():
    for prefix in ['mm_tp', 'mm_sp']:
        for i in range(100):
            if i == 0:
                continue

            template_id = '%s_%02d' % (prefix, i)
            success = icon.init_template_feature(template_id)
            if not success:
                break


if __name__ == '__main__':
    # icon.init_tp_with_background('mm_tp_11', noise_threshold=0)
    # icon.init_sp_with_background('mm_sp_07')
    # _test_init_ui_icon('ui_icon_09')
    # icon.init_battle_ctrl_icon('battle_ctrl_02')
    # _test_init_arrow_template()
    icon.init_battle_lock()