import cv2
import os
from typing import Optional

from basic import os_utils
from basic.img import MatchResult, cv2_utils
from basic.img.os import get_debug_image
from sr import cal_pos
from sr.const import map_const
from sr.context import get_context
from sr.image.sceenshot import mini_map, LargeMapInfo

if __name__ == '__main__':
    uni_num = 7
    level = 1
    screen = get_debug_image('_1704458491959')
    ctx = get_context()
    ctx.init_image_matcher()

    mm = mini_map.cut_mini_map(screen)
    mm_info = mini_map.analyse_mini_map(mm, ctx.im)

    best_pos: Optional[MatchResult] = None
    best_lm_info: Optional[LargeMapInfo] = None

    for _, region_list in map_const.PLANET_2_REGION.items():
        for region in region_list:
            if region != map_const.P03_R03_F1:
                continue
            lm_info = ctx.ih.get_large_map(region)
            pos = cal_pos.cal_character_pos_by_original(ctx.im, lm_info, mm_info, scale_list=[1], show=True)

            if pos is None:
                continue

            if best_pos is None or best_pos.confidence < pos.confidence:
                best_pos = pos
                best_lm_info = lm_info

    print(best_pos)
    print(best_lm_info.region.cn)
    if best_pos is not None:
        cv2_utils.show_overlap(best_lm_info.origin, mm_info.origin, best_pos.x, best_pos.y, win_name='overlap', wait=0)

    idx = 1
    base_dir = os_utils.get_path_under_work_dir('images', 'template', 'sim_uni')
    dir_path = None
    while True:
        dir_path = os.path.join(base_dir, 'map_%02d_%02d' % (uni_num, idx))
        if os.path.exists(dir_path):
            idx += 1
        else:
            os.mkdir(dir_path)
            break

    cv2.imwrite(os.path.join(dir_path, 'mm.png'), mm)
    