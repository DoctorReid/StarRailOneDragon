import os

import cv2
import numpy as np

from basic import os_utils
from basic.img import cv2_utils
from sr.image.sceenshot import icon


def _test_init_icon_with_background(template_id):
    icon.init_icon_with_background(template_id)

def _test_init_sp_with_background(template_id):
    icon.init_sp_with_background(template_id)


if __name__ == '__main__':
    # _test_init_icon_with_background('mm_tp_01')
    _test_init_sp_with_background('mm_sp_04')