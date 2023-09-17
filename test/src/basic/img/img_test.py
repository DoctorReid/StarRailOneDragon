import dev
from basic import gui_utils
from basic.img import MatchResultList, cv2_utils
from basic.img.cnocr_matcher import CnocrMatcher


def _test_match_template():
    source = cv2_utils.read_image_with_alpha(dev.get_test_image('m5.png'))
    template = cv2_utils.read_image_with_alpha(dev.get_test_image('t3.png'))
    result = cv2_utils.match_template(source, template, 0.5)
    cv2_utils.show_image(source, result)


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
    i = cv2_utils.read_image_with_alpha(dev.get_test_image('t3.png'))
    cv2_utils.image_rotate(i, -90, show_result=True)


def _test_convert_png_and_save():
    i = dev.get_test_image('g.jiff')
    o = dev.get_test_image('game2.png')
    cv2_utils.convert_png_and_save(i, o)


def _test_mark_area_as_transparent():
    i = cv2_utils.read_image_with_alpha(dev.get_test_image('game_can_find_little_map.png'))
    o = cv2_utils.mark_area_as_transparent(i, [0, 1080, 200, 100])
    cv2_utils.show_image(o)


def _test_find_circle():
    screen = cv2_utils.read_image_with_alpha(dev.get_test_image('game2.png'))

    # 左上角部分
    x, y = 0, 0
    x2, y2 = 340, 380
    image = screen[y:y2, x:x2]
    cv2_utils.show_image(image)
    cv2_utils.find_circle(image, show_result=True)


if __name__ == '__main__':
    _test_match_template()
