import time
import os

import cv2
from cv2.typing import MatLike

from basic import cal_utils
from basic.img import cv2_utils
from basic.img.os import get_test_image_dir
from basic.log_utils import log
from sr import constants, cal_pos, performance_recorder
from sr.constants.map import Region
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.image.sceenshot import LargeMapInfo, mini_map, large_map
from sr.image.sceenshot.large_map import get_large_map_rect_by_pos


class TestCase:

    def __init__(self, region: Region, pos: tuple, num: int, running: bool, possible_pos: tuple = None):
        self.region: Region = region
        self.pos: tuple = pos
        self.num: int = num
        self.running: bool = running
        self.possible_pos: tuple = pos if possible_pos is None else possible_pos


case_list = [
    TestCase(constants.map.P01_R03_L1, (321, 329), 1, False),
    TestCase(constants.map.P01_R03_L1, (306, 422), 2, False),
    TestCase(constants.map.P01_R03_L1, (256, 392), 3, True),
    TestCase(constants.map.P01_R03_L1, (436, 502), 4, True),
    TestCase(constants.map.P01_R03_L1, (538, 551), 5, True),

    TestCase(constants.map.P01_R03_B1, (254, 356), 1, False),
    TestCase(constants.map.P01_R03_B1, (328, 438), 2, True),
    TestCase(constants.map.P01_R03_B1, (282, 437), 3, True),
    TestCase(constants.map.P01_R03_B1, (256, 315), 4, True),
    TestCase(constants.map.P01_R03_B1, (217, 312), 5, True),
    TestCase(constants.map.P01_R03_B1, (221, 356), 6, True),

    TestCase(constants.map.P01_R04_L1, (483, 276), 1, True),

    TestCase(constants.map.P02_R05, (495, 429), 1, True),
    TestCase(constants.map.P02_R05, (242, 1283), 2, True),

    TestCase(constants.map.P02_R06, (488, 687), 1, True),
    TestCase(constants.map.P02_R06, (465, 595), 2, True),

    TestCase(constants.map.P02_R11_L1, (655, 461), 1, True),
    TestCase(constants.map.P02_R11_L1, (707, 406), 2, True),
    TestCase(constants.map.P02_R11_L1, (726, 486), 3, False),
    TestCase(constants.map.P02_R11_L1, (733, 423), 4, False),

    TestCase(constants.map.P03_R03_L1, (352, 496), 1, True),
    TestCase(constants.map.P03_R03_L1, (413, 524), 2, True),

    TestCase(constants.map.P03_R09, (972, 402), 1, True, (963, 360, 30)),
]


def get_test_cal_pos_image(r: Region, num: int, suffix: str = '.png') -> MatLike:
    dir_path = os.path.join(get_test_image_dir('cal_pos'), r.planet.np_id)
    dir_path = os.path.join(dir_path, r.rl_id)
    img_path = os.path.join(dir_path, '%d%s' % (num, suffix))
    return cv2_utils.read_image(img_path)


def test_one(c: TestCase, lm_info: LargeMapInfo, show: bool = False) -> bool:
    mm = get_test_cal_pos_image(c.region, c.num)
    possible_pos = (*c.pos, 0)
    lm_rect = get_large_map_rect_by_pos(lm_info.gray.shape, mm.shape[:2], possible_pos)
    sp_map = constants.map.get_sp_type_in_rect(lm_info.region, lm_rect)
    mm_info = mini_map.analyse_mini_map(mm, im, sp_types=set(sp_map.keys()), another_floor=c.region.another_floor)
    x, y = cal_pos.cal_character_pos(im, lm_info, mm_info, lm_rect=lm_rect, show=show, retry_without_rect=False, running=c.running)

    if show:
        cv2.waitKey(0)

    error = x is None or cal_utils.distance_between((x,y), c.pos[:2]) > 10
    if error:
        log.error('定位错误 %s', (x, y))
    else:
        log.info('定位正确 %s', (x, y))

    return error


if __name__ == '__main__':
    ih = ImageHolder()
    im = CvImageMatcher(ih)
    lm_info_map = {}
    fail_list = []
    for i in range(len(case_list)):
        c: TestCase = case_list[i]
        # if c.region != constants.map.P01_R03_L1 or c.num != 5:
        #     continue
        if c.region.prl_id not in lm_info_map:
            lm_info_map[c.region.prl_id] = large_map.analyse_large_map(c.region, ih)
        is_err = test_one(c, lm_info_map[c.region.prl_id], False)
        if is_err:
            fail_list.append(c)

    performance_recorder.log_all_performance()

    for c in fail_list:
        log.error('定位错误 %s %d', c.region.prl_id, c.num)
