import time

import cv2

from basic import cal_utils
from basic.img.os import get_test_cal_pos_image
from basic.log_utils import log
from sr import constants, cal_pos, performance_recorder
from sr.constants.map import Region
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.image.sceenshot import LargeMapInfo, mini_map, large_map
from sr.image.sceenshot.large_map import get_large_map_rect_by_pos


class TestCase:

    def __init__(self, region: Region, pos: tuple, num: int, running: bool):
        self.region: Region = region
        self.pos: tuple = pos
        self.num: int = num
        self.running: bool = running


case_list = [
    TestCase(constants.map.P01_R03_SRCD_L1, (321, 329), 1, False),
    TestCase(constants.map.P01_R03_SRCD_L1, (299, 410), 2, False),
    TestCase(constants.map.P01_R03_SRCD_L1, (256, 392), 3, True),
    TestCase(constants.map.P01_R03_SRCD_L1, (436, 497, 1), 4, True),
    TestCase(constants.map.P01_R03_SRCD_L1, (538, 546, 1), 5, True),

    TestCase(constants.map.P01_R03_SRCD_B1, (254, 356), 1, False),
    TestCase(constants.map.P01_R03_SRCD_B1, (328, 438), 2, True),
    TestCase(constants.map.P01_R03_SRCD_B1, (282, 437), 3, True),
    TestCase(constants.map.P01_R03_SRCD_B1, (256, 315), 4, True),
    TestCase(constants.map.P01_R03_SRCD_B1, (217, 312), 5, True),
    TestCase(constants.map.P01_R03_SRCD_B1, (221, 356), 6, True),

    TestCase(constants.map.P01_R04_ZYCD_L1, (470, 244), 1, True),

    TestCase(constants.map.P02_R05, (495, 429), 1, True),
    TestCase(constants.map.P02_R05, (242, 1283), 2, True),

    TestCase(constants.map.P02_R06, (488, 687), 1, True),
    TestCase(constants.map.P02_R06, (465, 595), 2, True),

    TestCase(constants.map.P02_R11_L1, (655, 461), 1, True),
    TestCase(constants.map.P02_R11_L1, (707, 406, 5), 2, True),
    TestCase(constants.map.P02_R11_L1, (726, 486, 50), 3, False),
    TestCase(constants.map.P02_R11_L1, (733, 423, 50), 4, False),

    TestCase(constants.map.P03_R03_L1, (352, 496, 6), 1, True),
    TestCase(constants.map.P03_R03_L1, (413, 524, 6), 2, True),
]


def test_one(c: TestCase, lm_info: LargeMapInfo, show: bool = False) -> bool:
    log.info('开始计算 %s %d', c.region.get_prl_id(), c.num)
    mm = get_test_cal_pos_image(c.num, c.region.get_prl_id())
    t1 = time.time()
    possible_pos = (*c.pos, 0)
    lm_rect = get_large_map_rect_by_pos(lm_info.gray.shape, mm.shape[:2], possible_pos)
    sp_map = constants.map.get_sp_type_in_rect(lm_info.region, lm_rect)
    mm_info = mini_map.analyse_mini_map(mm, im, sp_types=set(sp_map.keys()), another_floor=c.region.another_floor())
    t2 = time.time()
    analyse_time = t2 - t1
    log.debug('analyse_mini_map 耗时 %.6f', analyse_time)
    x, y = cal_pos.cal_character_pos(im, lm_info, mm_info, lm_rect=lm_rect, show=show, retry_without_rect=False, running=c.running, possible_pos=c.pos)
    t3 = time.time()
    cal_time = t3 - t2
    log.debug('cal_character_pos 耗时 %.6f', cal_time)

    if show:
        cv2.waitKey(0)

    error = x is None or cal_utils.distance_between((x,y), c.pos[:2]) > 10
    if error:
        log.error('定位错误 %s', (x, y))

    return error, analyse_time, cal_time


if __name__ == '__main__':
    ih = ImageHolder()
    im = CvImageMatcher(ih)
    lm_info_map = {}
    fail_list = []
    case_num = 0
    total_analyse_time = 0
    total_cal_time = 0
    for i in range(len(case_list)):
        c: TestCase = case_list[i]
        # if c.region != constants.map.P01_R03_SRCD_B1 or c.num != 1:
        #     continue
        if c.region.get_prl_id() not in lm_info_map:
            lm_info_map[c.region.get_prl_id()] = large_map.analyse_large_map(c.region, ih)
        is_err, analyse_time, cal_time = test_one(c, lm_info_map[c.region.get_prl_id()], False)
        if is_err:
            fail_list.append(c)
        case_num += 1
        total_analyse_time += analyse_time
        total_cal_time += cal_time

    performance_recorder.log_all_performance()

    for c in fail_list:
        log.error('定位错误 %s %d', c.region.get_prl_id(), c.num)
