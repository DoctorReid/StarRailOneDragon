import time

import cv2

from basic import cal_utils
from basic.img import cv2_utils
from basic.img.os import get_test_image, get_test_cal_pos_image
from basic.log_utils import log
from sr import constants
from sr.constants.map import Region
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.image.sceenshot import LargeMapInfo, mini_map
from sr.map_cal import MapCalculator


class TestCase:

    def __init__(self, region: Region, pos: tuple, num: int, running: bool):
        self.region: Region = region
        self.pos: tuple = pos
        self.num: int = num
        self.running: bool = running


case_list = [
    TestCase(constants.map.P01_R03_SRCD_L1, (314, 319), 1, False),
    TestCase(constants.map.P01_R03_SRCD_L1, (292, 400), 2, False),
    TestCase(constants.map.P01_R03_SRCD_L1, (249, 382), 3, True),

    TestCase(constants.map.P01_R03_SRCD_B1, (243, 342), 1, False),
    TestCase(constants.map.P01_R03_SRCD_B1, (321, 428), 2, True),
    TestCase(constants.map.P01_R03_SRCD_B1, (275, 427), 3, True),
    TestCase(constants.map.P01_R03_SRCD_B1, (249, 305), 4, True),
    TestCase(constants.map.P01_R03_SRCD_B1, (210, 302), 5, True),
    TestCase(constants.map.P01_R03_SRCD_B1, (214, 346), 6, True),
]


def test_one(c: TestCase, lm_info: LargeMapInfo, show: bool = False) -> bool:
    log.info('开始计算 %s %d', c.region.get_prl_id(), c.num)
    mm = get_test_cal_pos_image(c.num, c.region.get_prl_id())
    t1 = time.time()
    possible_pos = (*c.pos, 0)
    lm_rect = mc.get_large_map_rect_by_pos(lm_info.gray.shape, mm.shape[:2], possible_pos)
    sp_map = constants.map.get_sp_type_in_rect(lm_info.region, lm_rect)
    mm_info = mini_map.analyse_mini_map(mm, im, sp_types=set(sp_map.keys()))
    log.debug('analyse_mini_map 耗时 %.6f', (time.time() - t1))
    x, y = mc.cal_character_pos(lm_info, mm_info, lm_rect=lm_rect, show=show, retry_without_rect=False, running=c.running)
    log.debug('cal_character_pos 耗时 %.6f', (time.time() - t1))

    if show:
        cv2.waitKey(0)

    return x is None or cal_utils.distance_between((x,y), c.pos) > 10


if __name__ == '__main__':
    ih = ImageHolder()
    im = CvImageMatcher(ih)
    mc = MapCalculator(im=im)
    lm_info_map = {}
    fail_list = []
    for i in range(len(case_list)):
        c: TestCase = case_list[i]
        # if c.region != constants.map.P01_R03_SRCD_B1 or c.num != 7:
        #     continue
        if c.region.get_prl_id() not in lm_info_map:
            lm_info_map[c.region.get_prl_id()] = mc.analyse_large_map(c.region)
        if test_one(c, lm_info_map[c.region.get_prl_id()], True):
            fail_list.append(c)

    for c in fail_list:
        log.error('定位错误 %s %d', c.region.get_prl_id(), c.num)