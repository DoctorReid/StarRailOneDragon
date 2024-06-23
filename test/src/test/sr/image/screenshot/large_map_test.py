import cv2

from basic.img import cv2_utils
from basic.img.os import get_test_image
from sr.const import map_const
from sr.const.map_const import Region
from sr.context.context import get_context
from sr.image import ImageMatcher
from sr.image.cn_ocr_matcher import CnOcrMatcher
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.image_holder import ImageHolder
from sr.image.sceenshot import large_map, LargeMapInfo


def _test_get_planet_name():
    screen = get_test_image('large_map_1')
    cv2_utils.show_image(screen[30:100, 90:250], win_name='cut', wait=0)
    ocr = CnOcrMatcher()
    print(large_map.get_planet(screen, ocr))


def _test_get_sp_mask_by_template_match():
    ih = ImageHolder()
    screen = get_test_image('large_map_htbgs')
    lm_info = LargeMapInfo()
    lm_info.origin = screen
    sp_mask, _ = large_map.get_sp_mask_by_template_match(lm_info, ih, show=True)
    cv2_utils.show_image(sp_mask, win_name='sp_mask', wait=0)


def _test_get_active_region_name():
    ocr = CnOcrMatcher()
    screen = get_test_image('large_map_2')
    print(large_map.get_active_region_name(screen, ocr))


def _test_get_active_level():
    ocr = CnOcrMatcher()
    screen = get_test_image('level', sub_dir='large_map')
    part, _ = cv2_utils.crop_image(screen, large_map.FLOOR_LIST_PART)
    cv2_utils.show_image(part, win_name='part')
    level_str = large_map.get_active_level(screen, ocr)
    print(level_str)
    cv2.waitKey(0)


def _test_init_large_map(region: Region):
    ctx = get_context()
    ih: ImageHolder = ImageHolder()
    im: ImageMatcher = CvImageMatcher(ih)
    large_map.init_large_map(region, ih.get_large_map(region).raw, im, ctx.game_config.mini_map_pos, save=True)


if __name__ == '__main__':
    for r in [map_const.P03_R10]:
        _test_init_large_map(r)