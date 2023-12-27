from typing import List
import os

import cv2

from basic import os_utils
from basic.img import cv2_utils
from basic.img.os import get_debug_image, get_test_image, get_test_image_path
from basic.log_utils import log
from sr import cal_pos
from sr.const import map_const
from sr.const.map_const import TransportPoint
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.image.sceenshot import mini_map, large_map, LargeMapInfo


def get_tp_image_path(tp: TransportPoint):
    dir_path = os_utils.get_path_under_work_dir('test', 'resources', 'images', 'cal_pos', 'tp_pos')
    return os.path.join(dir_path, '%s.png' % tp.unique_id)


def cal_one(tp: TransportPoint, debug_image: str = None, show: bool = False):
    image_path = get_tp_image_path(tp)
    if debug_image is not None:
        image = get_debug_image(debug_image)
        mm = mini_map.cut_mini_map(image)
        cv2.imwrite(image_path, mm)
    else:
        mm = cv2_utils.read_image(image_path)

    possible_pos = (*(tp.lm_pos.tuple()), 50)
    lm_info: LargeMapInfo = ih.get_large_map(tp.region)
    lm_rect = large_map.get_large_map_rect_by_pos(lm_info.gray.shape, mm.shape[:2], possible_pos)
    sp_map = map_const.get_sp_type_in_rect(lm_info.region, lm_rect)
    mm_info = mini_map.analyse_mini_map(mm, im, sp_types=set(sp_map.keys()))
    result = cal_pos.cal_character_pos(im, lm_info, mm_info, lm_rect=lm_rect, show=show, retry_without_rect=False, running=False)

    log.info('%s 传送落地坐标 %s', tp.display_name, result)
    cv2.waitKey(0)


if __name__ == '__main__':
    ih = ImageHolder()
    im = CvImageMatcher(ih)

    sp_list = [
        map_const.P01_R05_SP01,
        map_const.P01_R05_SP02,
        map_const.P01_R05_SP03,
        map_const.P01_R05_SP04,
        map_const.P01_R05_SP05,
    ]
    img_list = [
        '_1703687341194',
        '_1703687347992',
        '_1703687354009',
        '_1703687360542',
        '_1703687368042',
    ]
    for i in range(len(sp_list)):
        cal_one(sp_list[i], debug_image=img_list[i], show=True)