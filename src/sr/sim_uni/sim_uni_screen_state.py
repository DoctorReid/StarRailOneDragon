from typing import Optional, List

from cv2.typing import MatLike

from basic import str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.image.ocr_matcher import OcrMatcher
from sr.screen_area.screen_sim_uni import ScreenSimUni
from sr.sim_uni.sim_uni_const import SimUniLevelType, SimUniLevelTypeEnum


def get_level_type(screen: MatLike, ocr: OcrMatcher) -> Optional[SimUniLevelType]:
    """
    获取当前画面的楼层类型
    :param screen:
    :param ocr:
    :return:
    """
    area = ScreenSimUni.LEVEL_TYPE.value
    part = cv2_utils.crop_image_only(screen, area.rect)
    region_name = ocr.ocr_for_single_line(part)
    level_type_list: List[SimUniLevelType] = [enum.value for enum in SimUniLevelTypeEnum]
    target_list = [gt(level_type.type_name, 'ocr') for level_type in level_type_list]
    target_idx = str_utils.find_best_match_by_lcs(region_name, target_list, lcs_percent_threshold=0.61)

    if target_idx is None:
        return None
    else:
        return level_type_list[target_idx]
