from basic.img import cv2_utils
from basic.img.os import get_test_image
from sr import constants
from sr.constants.map import Region, TransportPoint
from sr.context import get_context
from sr.operation.unit.choose_transport_point import ChooseTransportPoint


def _test_get_tp_pos():
    screen = get_test_image('large_map_htbgs')
    map_image, _ = cv2_utils.crop_image(screen, ChooseTransportPoint.map_rect)
    offset = op.get_map_offset(map_image)
    r = op.get_tp_pos(map_image, offset)
    cv2_utils.show_image(map_image, r, win_name='map_image', wait=0)


def _test_whole_operation():
    ctx.running = True
    ctx.controller.init()
    op.execute()


if __name__ == '__main__':
    ctx = get_context()
    tp: TransportPoint = constants.map.P01_R02_SP01_JKS
    op = ChooseTransportPoint(ctx, tp)
    _test_whole_operation()