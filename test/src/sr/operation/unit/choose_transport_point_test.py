from basic.img import cv2_utils
from basic.img.os import get_test_image
from sr import constants
from sr.context import get_context
from sr.operation.unit.choose_transport_point import ChooseTransportPoint


def _test_get_tp_pos():
    screen = get_test_image('large_map_htbgs')
    map_image = cv2_utils.crop_image(screen, ChooseTransportPoint.map_rect)
    offset = op.get_map_offset(map_image)
    r = op.get_tp_pos(map_image, offset)
    cv2_utils.show_image(map_image, r, win_name='map_image', wait=0)


if __name__ == '__main__':
    ctx = get_context('唯秘')
    op = ChooseTransportPoint(ctx, constants.map.P01_R01_TP01_HTBGS)
    _test_get_tp_pos()