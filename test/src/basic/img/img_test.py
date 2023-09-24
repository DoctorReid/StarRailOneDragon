import dev

import basic.img.get
import sr
from basic import gui_utils
from basic.img import MatchResultList, cv2_utils
from sr.image.cnocr_matcher import CnocrMatcher
from sr.image.cv2_matcher import CvImageMatcher
from sr import constants
from sr.config import ConfigHolder
from sr.map_cal import MapCalculator


im = CvImageMatcher()
ch = ConfigHolder()
mc = MapCalculator(im=im, config=ch)


def _test_match_template():
    source = sr.read_map_image(constants.PLANET_1_KZJ, constants.REGION_2_JZCD, 'usage')
    template = sr.raed_template_image('transport_1')
    cv2_utils.show_image(source, win_name='source')
    cv2_utils.show_image(template, win_name='template')
    result = cv2_utils.match_template(source, template, constants.THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP, top_n=2)
    print(result)
    cv2_utils.show_image(source, result, wait=0)


def _test_ocr():
    win = gui_utils.get_win_by_name('微信')
    gui_utils.active_win(win)
    img = gui_utils.screenshot_win(win)
    ocr = CnocrMatcher()
    out = ocr.match_words(img, ['叶叶子', '庆国'])
    merge_match_result = MatchResultList()
    for k in out.keys():
        for r in out[k]:
            print(r)
            merge_match_result.append(r)
    cv2_utils.show_image(img, merge_match_result)


def _test_rotate():
    i = cv2_utils.read_image(basic.img.get.get_test_image('t3.png'))
    cv2_utils.image_rotate(i, -90, show_result=True)


def _test_match_template_with_rotation():
    screen = basic.img.get.get_debug_image('1695022366133')
    little_map = mc.cut_mini_map(screen)
    im = CvImageMatcher()
    print(im.match_template_with_rotation(little_map, constants.TEMPLATE_ARROW))


def _test_mark_area_as_transparent():
    i = cv2_utils.read_image(basic.img.get.get_test_image('game1.png'))
    o = cv2_utils.mark_area_as_transparent(i, [0, 1080, 200, 100])
    cv2_utils.show_image(o)


def _test_find_circle():
    screen = cv2_utils.read_image(basic.img.get.get_test_image('game2.png'))

    # 左上角部分
    x, y = 0, 0
    x2, y2 = 340, 380
    image = screen[y:y2, x:x2]
    cv2_utils.show_image(image)
    cv2_utils.find_circle(image, show_result=True)


if __name__ == '__main__':
    _test_match_template()
