from cv2.typing import MatLike

from basic.img import cv2_utils
from basic.img.os import get_debug_image
from sr.image.sceenshot import fill_uid_black

def _test_no_uid(img: MatLike, save: bool = False):
    no_uid = fill_uid_black(img)
    cv2_utils.show_image(no_uid, wait=0)


if __name__ == '__main__':

    _test_no_uid(get_debug_image('1695043542433'))