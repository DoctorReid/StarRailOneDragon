import os

import cv2
from cv2.typing import MatLike

from basic import cal_utils, Point
from basic.img import cv2_utils
from basic.img.os import get_test_image_dir
from basic.log_utils import log
from sr import cal_pos, performance_recorder
from sr.const import map_const
from sr.const.map_const import Region
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.image.sceenshot import LargeMapInfo, mini_map, mini_map_angle_alas
from sr.image.sceenshot.large_map import get_large_map_rect_by_pos


class TestCase:

    def __init__(self, region: Region, pos: Point, num: int, running: bool, possible_pos: tuple = None):
        self.region: Region = region
        self.pos: Point = pos
        self.num: int = num
        self.running: bool = running
        self.possible_pos: tuple = (*pos.tuple(), 0) if possible_pos is None else possible_pos


case_list = [
    TestCase(map_const.P01_R03_L1, Point(321, 329), 1, False),
    TestCase(map_const.P01_R03_L1, Point(306, 422), 2, False),
    TestCase(map_const.P01_R03_L1, Point(256, 392), 3, True),
    TestCase(map_const.P01_R03_L1, Point(436, 502), 4, True),
    TestCase(map_const.P01_R03_L1, Point(538, 551), 5, True),

    TestCase(map_const.P01_R03_B1, Point(254, 356), 1, False),
    TestCase(map_const.P01_R03_B1, Point(328, 438), 2, True),
    TestCase(map_const.P01_R03_B1, Point(282, 437), 3, True),
    TestCase(map_const.P01_R03_B1, Point(256, 315), 4, True),
    TestCase(map_const.P01_R03_B1, Point(217, 312), 5, True),
    TestCase(map_const.P01_R03_B1, Point(221, 356), 6, True),

    TestCase(map_const.P01_R04_L1, Point(483, 276), 1, True),

    TestCase(map_const.P01_R05_L2, Point(381, 669), 1, True, possible_pos=(386, 678, 25)),
    TestCase(map_const.P01_R05_L2, Point(332, 525), 2, True, possible_pos=(302, 554, 25)),
    TestCase(map_const.P01_R05_L2, Point(332, 525), 3, True, possible_pos=(298, 530, 60)),

    TestCase(map_const.P02_R05, Point(497, 440), 1, True),
    TestCase(map_const.P02_R05, Point(242, 1283), 2, True),
    TestCase(map_const.P02_R05, Point(488, 1147), 3, False, possible_pos=(488, 1155, 0)),
    TestCase(map_const.P02_R05, Point(365, 1176), 4, True, possible_pos=(390, 1176, 52)),

    TestCase(map_const.P02_R06, Point(488, 687), 1, True),
    TestCase(map_const.P02_R06, Point(465, 595), 2, True),

    TestCase(map_const.P02_R11_L1, Point(655, 461), 1, True),
    TestCase(map_const.P02_R11_L1, Point(707, 406), 2, True),
    TestCase(map_const.P02_R11_L1, Point(726, 486), 3, False),
    TestCase(map_const.P02_R11_L1, Point(734, 433), 4, False),
    TestCase(map_const.P02_R11_L1, Point(740, 556), 5, True, possible_pos=(740, 556, 20)),

    TestCase(map_const.P03_R03_L1, Point(352, 496), 1, True),
    TestCase(map_const.P03_R03_L1, Point(413, 524), 2, True),

    TestCase(map_const.P03_R09, Point(972, 402), 1, True, (963, 360, 30)),

    TestCase(map_const.P03_R10, Point(378, 806), 1, True, (400, 784, 29)),
]


def get_test_cal_pos_image(r: Region, num: int, suffix: str = '.png') -> MatLike:
    dir_path = os.path.join(get_test_image_dir('cal_pos'), r.planet.np_id)
    dir_path = os.path.join(dir_path, r.rl_id)
    img_path = os.path.join(dir_path, '%d%s' % (num, suffix))
    return cv2_utils.read_image(img_path)


def test_one(c: TestCase, lm_info: LargeMapInfo, show: bool = False) -> bool:
    mm = get_test_cal_pos_image(c.region, c.num)
    possible_pos = c.possible_pos
    lm_rect = get_large_map_rect_by_pos(lm_info.gray.shape, mm.shape[:2], possible_pos)
    sp_map = map_const.get_sp_type_in_rect(lm_info.region, lm_rect)
    mm_info = mini_map.analyse_mini_map(mm, im, sp_types=set(sp_map.keys()))
    result = cal_pos.cal_character_pos(im, lm_info, mm_info, lm_rect=lm_rect, show=show, retry_without_rect=False, running=c.running)

    if show:
        cv2.waitKey(0)

    error = result is None or cal_utils.distance_between(result, c.pos) > 10
    if error:
        log.error('定位错误 %s', result)
    else:
        log.info('定位正确 %s', result)

    return error


if __name__ == '__main__':
    ih = ImageHolder()
    ih.preheat_for_world_patrol()  # 预热 方便后续统计耗时
    for i in range(93, 100):  # 预热 方便后续统计耗时 不同时期截图大小可能不一致
        mini_map_angle_alas.RotationRemapData(i * 2)
    im = CvImageMatcher(ih)
    lm_info_map = {}
    fail_list = []
    for i in range(len(case_list)):
        c: TestCase = case_list[i]
        # if c.region != map_const.P03_R10 or c.num != 1:
        #     continue
        if c.region.prl_id not in lm_info_map:
            lm_info_map[c.region.prl_id] = ih.get_large_map(c.region)
        is_err = test_one(c, lm_info_map[c.region.prl_id], False)
        if is_err:
            fail_list.append(c)

    performance_recorder.log_all_performance()

    for c in fail_list:
        log.error('定位错误 %s %d', c.region.prl_id, c.num)
