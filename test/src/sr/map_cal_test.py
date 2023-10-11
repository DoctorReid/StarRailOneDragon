import time

import cv2

from basic.img import cv2_utils, MatchResult
from basic.img.os import get_test_image, get_debug_image
from sr import constants
from sr.constants.map import TransportPoint, Region
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.map_cal import MapCalculator


def _print_tp_pos(tp: TransportPoint):
    lm = ih.get_large_map(tp.region, map_type='origin')
    lm_info = mc.analyse_large_map(lm)

    screen = get_test_image('%s-%s' % (tp.region.get_rl_id(), tp.id), sub_dir='tp')
    mm = mc.cut_mini_map(screen)
    mm_info = mc.analyse_mini_map(mm)

    print(mc.cal_character_pos(lm_info, mm_info, show=True))
    cv2.waitKey(0)


def _test_cal_character_pos():
    region: Region = constants.map.P01_R03_SRCD_L1

    lm_info = mc.analyse_large_map(region)

    for x in ['1696773964057', '1696773991417', '1696774015238']:
        screen = get_debug_image(x)
        mm = mc.cut_mini_map(screen)
        t1 = time.time()
        possible_pos = (311, 316, 100)
        lm_rect = mc.get_large_map_rect_by_pos(lm_info.gray.shape, mm.shape[:2], possible_pos)
        if lm_rect is not None:
            cv2_utils.show_image(cv2_utils.crop_image(lm_info.origin, lm_rect), win_name='large_map_rect')
        sp_map = constants.map.get_sp_type_in_rect(region, lm_rect)
        mm_info = mc.analyse_mini_map(mm, sp_map.keys())
        mc.cal_character_pos(lm_info, mm_info, lm_rect=lm_rect, show=True, retry_without_rect=False)
        print('cal_character_pos 耗时 %.6f' % (time.time() - t1))
        cv2.waitKey(0)


def _test_analyse_mini_map():
    screen = get_debug_image('1696773991417')
    mm = mc.cut_mini_map(screen)
    mm_info = mc.analyse_mini_map(mm)
    cv2_utils.show_image(mm_info.road_mask, win_name='road_mask')

    edge = mc.find_mini_map_edge_mask(mm)
    cv2_utils.show_image(edge, win_name='edge')

    edge_2 = cv2.bitwise_and(mm_info.edge, edge)
    cv2_utils.show_image(edge_2, win_name='edge_2')

    cv2.waitKey(0)


def _test_find_mini_map_edge_mask():
    screen = get_debug_image('1696773991417')
    mm = mc.cut_mini_map(screen)
    edge = mc.find_mini_map_edge_mask(mm)
    cv2_utils.show_image(edge, win_name='edge')

    cv2.waitKey(0)


if __name__ == '__main__':
    ih = ImageHolder()
    im = CvImageMatcher()
    mc = MapCalculator(im=im)
    # _print_tp_pos(constants.map.P01_R03_TP01_KZZXW)
    _test_cal_character_pos()