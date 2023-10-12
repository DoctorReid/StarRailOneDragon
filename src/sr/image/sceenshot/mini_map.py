from typing import Set

import cv2
import numpy as np
from cv2.typing import MatLike

from basic.img import cv2_utils, MatchResultList, MatchResult
from sr import constants
from sr.config.game_config import MiniMapPos
from sr.image import ImageMatcher, TemplateImage
from sr.image.sceenshot import MiniMapInfo


def extract_arrow(mini_map: MatLike):
    """
    提取小箭头部分 范围越小越精准
    :param mini_map: 小地图
    :return: 小箭头
    """
    return cv2_utils.color_similarity_2d(mini_map, constants.COLOR_ARROW_BGR)


def get_arrow_mask(mm: MatLike):
    """
    获取小地图的小箭头掩码
    :param mm: 小地图
    :return: 中心区域的掩码 和 整张图的掩码
    """
    w, h = mm.shape[1], mm.shape[0]
    cx, cy = w // 2, h // 2
    d = constants.TEMPLATE_ARROW_LEN
    r = constants.TEMPLATE_ARROW_R
    center = mm[cy - r:cy + r, cx - r:cx + r]
    arrow = extract_arrow(center)
    _, mask = cv2.threshold(arrow, 180, 255, cv2.THRESH_BINARY)
    # 做一个连通性检测 小于50个连通的认为是噪点
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    large_components = []
    for label in range(1, num_labels):
        if stats[label, cv2.CC_STAT_AREA] < 50:
            large_components.append(label)
    for label in large_components:
        mask[labels == label] = 0

    whole_mask = np.zeros((h,w), dtype=np.uint8)
    whole_mask[cy-r:cy+r, cx-r:cx+r] = mask
    # 黑色边缘线条采集不到 稍微膨胀一下
    kernel = np.ones((5, 5), np.uint8)
    cv2.dilate(src=whole_mask, dst=whole_mask, kernel=kernel, iterations=1)
    arrow_mask, _ = cv2_utils.convert_to_standard(mask, mask, width=d, height=d)
    return arrow_mask, whole_mask


def get_angle_from_arrow(arrow: MatLike,
                         im: ImageMatcher,
                         show: bool = False) -> int:
    """
    用小地图上的箭头 计算当前方向 正右方向为0度 逆时针旋转为正度数
    :param arrow: 已经提取好的白色的箭头
    :param all_template: 模板 每5度一张图的模板
    :param one_template: 模板 0度的模板
    :param im: 图片匹配器
    :param show: 显示结果
    :return: 角度 正右方向为0度 顺时针旋转为正度数
    """
    rough_template = im.get_template('arrow_rough').mask
    result = im.match_image(rough_template, arrow, threshold=0.85)
    if len(result) == 0:
        return None

    if show:
        cv2_utils.show_image(rough_template, result.max, win_name="rough_template_match")

    d = constants.TEMPLATE_ARROW_LEN

    row = result.max.cy // d
    col = result.max.cx // d
    rough_angle = (row * 11 + col) * 3

    rough_arrow = cv2_utils.image_rotate(arrow, -rough_angle)
    precise_template = im.get_template('arrow_precise').mask
    result2 = im.match_image(precise_template, rough_arrow, threshold=0.85)

    if len(result2) == 0:
        precise_angle = rough_angle
    else:
        row = result2.max.cy // d
        col = result2.max.cx // d
        precise_delta_angle = (row * 11 + col - 6) / 10.0
        precise_angle = rough_angle + precise_delta_angle

    if precise_angle is not None and precise_angle < 0:
        precise_angle += 360
    return 360 - precise_angle


def analyse_arrow_and_angle(mini_map: MatLike, im: ImageMatcher):
    """
    在小地图上获取小箭头掩码和角度
    :param mini_map: 小地图图片
    :param im: 图片匹配器
    :return:
    """
    center_arrow_mask, arrow_mask = get_arrow_mask(mini_map)
    angle = get_angle_from_arrow(center_arrow_mask, im)  # 正右方向为0度 顺时针旋转为正度数
    return center_arrow_mask, arrow_mask, angle


def get_edge_mask_by_hsv(mm: MatLike, arrow_mask: MatLike):
    """
    废弃了 背景亮的時候效果很差
    将小地图转化成HSV格式，然后根据亮度扣出前景
    最后用Canny画出边缘
    :param mm: 小地图截图
    :param arrow_mask: 小箭头掩码 传入时忽略掉这部分
    :return:
    """
    hsv = cv2.cvtColor(mm, cv2.COLOR_BGR2HSV)
    hsv_mask = cv2.threshold(hsv[:, :, 2], 180, 255, cv2.THRESH_BINARY)[1]
    if arrow_mask is not None:
        hsv_mask = cv2.bitwise_and(hsv_mask, hsv_mask, mask=cv2.bitwise_not(arrow_mask))

    # 膨胀一下 粗点的边缘可以抹平一些取色上的误差 后续模板匹配更准确
    kernel = np.ones((3, 3), np.uint8)
    return cv2.dilate(hsv_mask, kernel, iterations=1)


def get_sp_mask_by_feature_match(mm_info: MiniMapInfo, im: ImageMatcher,
                                 sp_types: Set = None,
                                 show: bool = False):
    """
    在小地图上找到特殊点
    使用特征匹配 每个模板最多只能找到一个
    :param mm_info: 小地图信息
    :param im: 图片匹配器
    :param sp_types: 限定种类的特殊点
    :param show: 是否展示结果
    :return:
    """
    feature_detector = cv2.SIFT_create()
    source = mm_info.origin
    source_mask = mm_info.circle_mask
    source_kps, source_desc = feature_detector.detectAndCompute(source, mask=source_mask)

    sp_mask = np.zeros_like(mm_info.gray)
    sp_match_result = {}
    for prefix in ['mm_tp', 'mm_sp']:
        for i in range(100):
            if i == 0:
                continue

            template_id = '%s_%02d' % (prefix, i)
            t: TemplateImage = im.get_template(template_id)
            if t is None:
                break
            if sp_types is not None and template_id not in sp_types:
                continue

            match_result_list = MatchResultList()
            template = t.origin
            template_mask = t.mask

            # TODO 后续预处理
            template_kps, template_desc = feature_detector.detectAndCompute(template, mask=template_mask)

            good_matches, offset_x, offset_y, scale = cv2_utils.feature_match(
                source_kps, source_desc,
                template_kps, template_desc,
                source_mask=source_mask)

            if offset_x is not None:
                mr = MatchResult(1, offset_x, offset_y, template.shape[1], template.shape[0], template_scale=scale)  #
                match_result_list.append(mr)
                sp_match_result[template_id] = match_result_list

                # 缩放后的宽度和高度
                sw = int(template.shape[1] * scale)
                sh = int(template.shape[0] * scale)
                one_sp_maks = cv2.resize(template_mask, (sw, sh))
                sp_mask[mr.y:mr.y + sh, mr.x:mr.x + sw] = cv2.bitwise_or(sp_mask[mr.y:mr.y + sh, mr.x:mr.x + sw], one_sp_maks)

            if show:
                cv2_utils.show_image(source, win_name='source')
                cv2_utils.show_image(source_mask, win_name='source_mask')
                source_with_keypoints = cv2.drawKeypoints(source, source_kps, None)
                cv2_utils.show_image(source_with_keypoints, win_name='source_with_keypoints_%s' % template_id)
                template_with_keypoints = cv2.drawKeypoints(template, template_kps, None)
                cv2_utils.show_image(
                    cv2.bitwise_and(template_with_keypoints, template_with_keypoints, mask=template_mask),
                    win_name='template_with_keypoints_%s' % template_id)
                all_result = cv2.drawMatches(template, template_kps, source, source_kps, good_matches, None, flags=2)
                cv2_utils.show_image(all_result, win_name='all_match_%s' % template_id)

                if offset_x is not None:
                    cv2_utils.show_overlap(source, template, offset_x, offset_y, template_scale=scale, win_name='overlap_%s' % template_id)
                cv2.waitKey(0)
                cv2.destroyAllWindows()

    return sp_mask, sp_match_result


def get_enemy_road_mask(mm: MatLike) -> MatLike:
    """
    在小地图上找红点敌人的道路掩码
    :param mm: 小地图截图
    :return: 敌人在小地图上的坐标
    """
    lower_color = np.array([45, 45, 100], dtype=np.uint8)
    upper_color = np.array([65, 65, 255], dtype=np.uint8)
    return cv2.inRange(mm, lower_color, upper_color)


def get_track_road_mask(mm: MatLike) -> MatLike:
    """
    小地图上移动轨迹的掩码
    :param mm: 小地图截图
    :return: 掩码
    """
    lower_color = np.array([45, 45, 110], dtype=np.uint8)
    upper_color = np.array([65, 65, 130], dtype=np.uint8)
    return cv2.inRange(mm, lower_color, upper_color)


def is_under_attack(mini_map: MatLike, mm_pos: MiniMapPos, show: bool = True) -> bool:
    """
    根据小地图边缘 判断是否被锁定
    红色色道应该有一个圆
    :param mini_map: 小地图截图
    :param mm_pos: 小地图坐标信息
    :return: 是否被锁定
    """
    w, h = mini_map.shape[1], mini_map.shape[0]
    cx, cy = w // 2, h // 2
    r = mm_pos.r

    circle_mask = np.zeros(mini_map.shape[:2], dtype=np.uint8)
    cv2.circle(circle_mask, (cx, cy), r, 255, 3)

    circle_part = cv2.bitwise_and(mini_map, mini_map, mask=circle_mask)
    _, red = cv2.threshold(circle_part[:, :, 2], 200, 255, cv2.THRESH_BINARY)

    circles = cv2.HoughCircles(red, cv2.HOUGH_GRADIENT, 0.3, 100, param1=10, param2=10,
                               minRadius=mm_pos.r - 10, maxRadius=mm_pos.r + 10)
    find: bool = circles is not None

    if show:
        cv2_utils.show_image(circle_part, win_name='circle_part')
        cv2_utils.show_image(red, win_name='red')
        find_circle = np.zeros(mini_map.shape[:2], dtype=np.uint8)
        if circles is not None:
            # 将检测到的圆形绘制在原始图像上
            circles = np.round(circles[0, :]).astype("int")
            for (x, y, r) in circles:
                cv2.circle(find_circle, (x, y), r, 255, 1)
        cv2_utils.show_image(find_circle, win_name='find_circle')

    return find


def get_mini_map_scale_list(running: bool):
    return [1.25, 1.20, 1.15, 1.10] if running else [1, 1.05]