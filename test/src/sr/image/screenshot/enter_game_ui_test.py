from basic.img.os import get_debug_image
from sr.image.cn_ocr_matcher import CnOcrMatcher
from sr.image.sceenshot import enter_game_ui


def _test_in_password_phase():
    screen = get_debug_image('_1699191894611')
    assert enter_game_ui.in_password_phase(screen, ocr)


def _test_in_server_phase():
    screen = get_debug_image('_1699283893453')
    assert enter_game_ui.in_server_phase(screen, ocr)


def _test_in_final_enter_phase():
    screen = get_debug_image('_1699192180111')
    assert enter_game_ui.in_final_enter_phase(screen, ocr)


def _test_in_get_supply_phase():
    screen = get_debug_image('_1699249813322')
    assert enter_game_ui.in_get_supply_phase(screen, ocr)


if __name__ == '__main__':
    ocr = CnOcrMatcher()
    _test_in_server_phase()
