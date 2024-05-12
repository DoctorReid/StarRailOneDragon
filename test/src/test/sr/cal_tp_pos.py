import os

import cv2

from basic import os_utils
from basic.img import cv2_utils
from basic.img.os import get_debug_image
from basic.log_utils import log
from sr import cal_pos
from sr.const import map_const
from sr.const.map_const import TransportPoint
from sr.context import get_context
from sr.image.sceenshot import mini_map, large_map, LargeMapInfo


def get_tp_image_path(tp: TransportPoint):
    dir_path = os_utils.get_path_under_work_dir('test', 'resources', 'images', 'cal_pos', 'tp_pos')
    return os.path.join(dir_path, '%s.png' % tp.unique_id)


def cal_one(tp: TransportPoint, debug_image: str = None, show: bool = False):
    image_path = get_tp_image_path(tp)
    if debug_image is not None:
        image = get_debug_image(debug_image)
        mm = mini_map.cut_mini_map(image, ctx.game_config.mini_map_pos)
        # cv2.imwrite(image_path, mm)
    else:
        mm = cv2_utils.read_image(image_path)

    possible_pos = (*(tp.lm_pos.tuple()), 50)
    lm_info: LargeMapInfo = ctx.ih.get_large_map(tp.region)
    lm_rect = large_map.get_large_map_rect_by_pos(lm_info.gray.shape, mm.shape[:2], possible_pos)
    mm_info = mini_map.analyse_mini_map(mm)
    result = cal_pos.cal_character_pos_by_sp_result(ctx.im, lm_info, mm_info, lm_rect=lm_rect)
    if result is None:
        result = cal_pos.cal_character_pos_by_gray(ctx.im, lm_info, mm_info, lm_rect=lm_rect,
                                                   scale_list=cal_pos.get_mini_map_scale_list(False))

    log.info('%s 传送落地坐标 %s 使用缩放 %.2f', tp.display_name, result.center, result.template_scale)
    if show:
        cv2_utils.show_overlap(lm_info.origin, mm, result.x, result.y, template_scale=result.template_scale, wait=0)


if __name__ == '__main__':
    ctx = get_context()
    ctx.init_image_matcher()

    sp_list = [
        map_const.P04_R10_SP01,
        map_const.P04_R10_SP02,
        map_const.P04_R10_SP03,
        map_const.P04_R10_SP04,
        map_const.P04_R10_SP08,
    ]
    img_list = [
        '_1715508142338',
        '_1715508147203',
        '_1715508152886',
        '_1715508158286',
        '_1715508165487'
    ]
    for i in range(len(sp_list)):
        cal_one(sp_list[i], debug_image=img_list[i], show=True)
        # cal_one(sp_list[i])
    cv2.destroyAllWindows()
