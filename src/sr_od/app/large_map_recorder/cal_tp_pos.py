import os

import cv2

from one_dragon.utils import debug_utils, cv2_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from sr_od.context.sr_context import SrContext
from sr_od.operations.move import cal_pos_utils
from sr_od.sr_map import mini_map_utils, large_map_utils
from sr_od.sr_map.large_map_info import LargeMapInfo
from sr_od.sr_map.sr_map_def import SpecialPoint


def cal_one(tp: SpecialPoint, debug_image: str, show: bool = False):
    image = debug_utils.get_debug_image(debug_image)
    mm = mini_map_utils.cut_mini_map(image, ctx.game_config.mini_map_pos)

    possible_pos = (*(tp.lm_pos.tuple()), 200)
    lm_info: LargeMapInfo = ctx.map_data.get_large_map_info(tp.region)
    lm_rect = large_map_utils.get_large_map_rect_by_pos(lm_info.raw.shape, mm.shape[:2], possible_pos)
    mm_info = mini_map_utils.analyse_mini_map(mm)
    result = cal_pos_utils.cal_character_pos_by_sp_result(ctx, lm_info, mm_info, lm_rect=lm_rect)
    if result is None:
        result = cal_pos_utils.cal_character_pos_by_gray(ctx, lm_info, mm_info, lm_rect=lm_rect,
                                                         scale_list=cal_pos_utils.get_mini_map_scale_list(False, is_debug=True))

    log.info('%s 传送落地坐标 tp_pos: [%d, %d] 使用缩放 %.2f', tp.display_name, result.center.x, result.center.y, result.template_scale)
    if show:
        cv2_utils.show_overlap(lm_info.raw, mm, result.x, result.y, template_scale=result.template_scale, wait=0)


if __name__ == '__main__':
    ctx = SrContext()
    ctx.init_by_config()

    planet_name: str = '翁法罗斯'
    region_name: str = '「穹顶关塞」晨昏之眼'

    planet = ctx.map_data.best_match_planet_by_name(gt(planet_name))
    region = ctx.map_data.best_match_region_by_name(gt(region_name), planet=planet)

    sp_name_list = [
        '天象画壁',
        '霓虹尽处',
        '关塞垂井',
        '擎空骨械',
        '关塞悬廊',
        '关塞颅顶',
        '晨昏的回眸·历战余响',
    ]
    img_list = [
        '_1749308404675',
        '_1749308763036',
        '_1749308771385',
        '_1749308776419',
        '_1749308781019',
        '_1749308787419',
        '_1749308792302',
    ]
    for i in range(len(sp_name_list)):
        sp = ctx.map_data.best_match_sp_by_name(region, gt(sp_name_list[i]))
        if sp is None:
            log.error(f'找不到 {sp_name_list[i]}')
        cal_one(sp, debug_image=img_list[i], show=True)
        # cal_one(sp_list[i])
    cv2.destroyAllWindows()
