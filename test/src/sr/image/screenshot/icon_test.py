import os

import cv2
import numpy as np

from basic import os_utils
from basic.img import cv2_utils
from sr.image.sceenshot import icon


def _test_init_tp_with_background(template_id):
    icon.init_tp_with_background(template_id)

def _test_init_sp_with_background(template_id):
    icon.init_sp_with_background(template_id)

def _test_init_ui_icon(template_id):
    icon.init_ui_icon(template_id, noise_threshold=20)


if __name__ == '__main__':
    # icon.init_tp_with_background('mm_tp_11', noise_threshold=0)
    icon.init_sp_with_background('mm_sp_07')
    # _test_init_ui_icon('ui_icon_09')
    # icon.init_battle_ctrl_icon('battle_ctrl_02')
