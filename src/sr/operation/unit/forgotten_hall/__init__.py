from typing import Optional, List

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import Rect, Point, str_utils, cal_utils
from basic.img import MatchResult, cv2_utils, MatchResultList
from sr.context import Context

CHOOSE_MISSION_RECT = Rect(10, 495, 1900, 850)


def get_mission_num_pos(ctx: Context, mission_num: int, screen: MatLike) -> Optional[MatchResult]:
    """
    获取关卡数字所在的位置
    :param ctx: 上下文
    :param mission_num: 关卡数字
    :param screen: 屏幕截图
    :return: 数字位置
    """
    part, _ = cv2_utils.crop_image(screen, CHOOSE_MISSION_RECT)

    lower_color = np.array([240, 240, 240], dtype=np.uint8)
    upper_color = np.array([255, 255, 255], dtype=np.uint8)
    white_part = cv2.inRange(part, lower_color, upper_color)

    # 整张图片进行OCR容易出现匹配不到的情况 因为先切割再匹配
    contours, _ = cv2.findContours(white_part, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)  # 对于每个轮廓，计算外接矩形
        lt = Point(x, y) + CHOOSE_MISSION_RECT.left_top
        rb = Point(x + w, y + h) + CHOOSE_MISSION_RECT.left_top
        rect = Rect(lt.x - 5, lt.y - 5, rb.x + 5, rb.y + 5)
        if w > 25 or w < 10 or h < 30:  # 过滤过大或过小的矩阵
            continue

        # 在矩阵中匹配数字
        number_part, rect = cv2_utils.crop_image(screen, rect)

        lower_color = np.array([240, 240, 240], dtype=np.uint8)
        upper_color = np.array([255, 255, 255], dtype=np.uint8)
        white_number_part = cv2.inRange(number_part, lower_color, upper_color)

        ocr_result = ctx.ocr.ocr_for_single_line(white_number_part)
        # cv2_utils.show_image(white_number_part, win_name='part', wait=0)
        if str_utils.find_by_lcs(str(mission_num), ocr_result, percent=0.1):
           return MatchResult(1, rect.x1, rect.y1, rect.x2 - rect.x1, rect.y2 - rect.y1)

    return None


def get_mission_star(ctx: Context, mission_num: int, screen: MatLike) -> Optional[int]:
    """
    获取关卡数字所在的位置
    :param ctx: 上下文
    :param mission_num: 关卡数字
    :param screen: 屏幕截图
    :return: 星数 找不到关卡时为 None
    """
    num_pos: Optional[MatchResult] = get_mission_num_pos(ctx, mission_num, screen)

    if num_pos is None:
        return None
    else:
        return get_mission_star_by_num_pos(ctx, screen, num_pos)


def get_mission_star_by_num_pos(ctx: Context, screen: MatLike, num_pos: MatchResult) -> int:
    """
    获取数字下面星星的数量
    :param ctx: 上下文
    :param screen: 屏幕截图
    :param num_pos: 数字位置
    :return: 星数
    """
    num_center = num_pos.center

    star_rect = Rect(num_center.x - 70, num_center.y + 20, num_center.x + 90, num_center.y + 80)
    part, _ = cv2_utils.crop_image(screen, star_rect)

    lower_color = np.array([240, 240, 240], dtype=np.uint8)
    upper_color = np.array([255, 255, 255], dtype=np.uint8)
    # lower_color = np.array([140, 100, 115], dtype=np.uint8)  # 没激活的星星颜色
    # upper_color = np.array([150, 115, 130], dtype=np.uint8)
    white_part = cv2.inRange(part, lower_color, upper_color)

    template = ctx.ih.get_template('mission_star_active')
    template_result_list: MatchResultList = ctx.im.match_image(white_part, template.mask,
                                                               threshold=0.3,
                                                               only_best=False)
    # cv2_utils.show_image(part, template_result_list, wait=0)

    mini_distance = 15  # 星星间最短的距离
    star_pos_arr: List[MatchResult] = []
    for r in template_result_list:
        existed: bool = False  # 是否距离已有星星过近
        for star in star_pos_arr:
            if cal_utils.distance_between(r.center, star.center) < mini_distance:
                existed = True
                break

        if not existed:
            star_pos_arr.append(r)

    return len(star_pos_arr)