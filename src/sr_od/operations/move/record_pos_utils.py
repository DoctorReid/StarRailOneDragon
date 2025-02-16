import time

import os
from typing import Optional

from cv2.typing import MatLike
import random

from one_dragon.base.config.yaml_operator import YamlOperator
from one_dragon.base.matcher.match_result import MatchResult
from one_dragon.utils import os_utils, cv2_utils
from sr_od.sr_map.sr_map_data import SrMapData
from sr_od.sr_map.sr_map_def import Region


def save_sample(region: Region, mm: MatLike, pos: MatchResult) -> None:
    """
    记录一个坐标 用于后续训练
    """
    if pos is None:
        return
    now = int(time.time() * 1000)
    base_dir = os_utils.get_path_under_work_dir('.debug', 'gps', region.prl_id, str(now))

    cv2_utils.save_image(mm, os.path.join(base_dir, 'mm.png'))
    yml = YamlOperator(os.path.join(base_dir, 'pos.yml'))
    yml.data = {
        'x': pos.x,
        'y': pos.y,
        'w': pos.w,
        'h': pos.h,
        'template_scale': pos.template_scale
    }
    yml.save()


def random_check(base_dir: Optional[str]) -> None:
    """
    随机检查上面保存的数据是否正确
    """
    map_data: SrMapData = SrMapData()
    if base_dir is None:
        base_dir = os_utils.get_path_under_work_dir('.debug', 'gps')
    while True:
        prl_id_list = os.listdir(base_dir)
        prl_id = random.choice(prl_id_list)
        prl_dir = os.path.join(base_dir, prl_id)

        case_list = os.listdir(prl_dir)
        case_id = random.choice(case_list)
        case_dir = os.path.join(prl_dir, case_id)

        mm = cv2_utils.read_image(os.path.join(case_dir, 'mm.png'))
        yml = YamlOperator(os.path.join(case_dir, 'pos.yml'))

        region = [i for i in map_data.region_list if i.prl_id == prl_id][0]
        lm_info = map_data.get_large_map_info(region)

        pos = MatchResult(1, yml.get('x'), yml.get('y'), yml.get('w'), yml.get('h'), template_scale=yml.get('template_scale'))

        print(prl_id, case_id)
        cv2_utils.show_overlap(lm_info.raw, mm,
                               pos.x, pos.y,
                               template_scale=pos.template_scale,
                               win_name='overlap',
                               wait=0)


if __name__ == '__main__':
    random_check()