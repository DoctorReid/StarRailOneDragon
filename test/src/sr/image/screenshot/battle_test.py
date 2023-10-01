from basic.img.os import get_test_image
from sr.image.cnocr_matcher import CnOcrMatcher
from sr.image.sceenshot import battle


def _test_get_battle_status():
    screen = get_test_image('mm_arrow')
    print(battle.get_battle_status(screen, ocr))


if __name__ == '__main__':
    ocr = CnOcrMatcher()
    _test_get_battle_status()