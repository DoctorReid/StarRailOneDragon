import cv2
import numpy as np
from cv2.typing import MatLike

from basic.img import cv2_utils
from sr import constants
from sr.image import ImageMatcher


def extract_arrow(mini_map: MatLike):
    """
    提取小箭头部分 范围越小越精准
    :param mini_map: 小地图
    :return: 小箭头
    """
    return cv2_utils.color_similarity_2d(mini_map, constants.COLOR_ARROW_BGR)


def get_arrow_mask(mini_map: MatLike):
    """
    获取小地图的小箭头掩码
    :param mini_map: 小地图
    :return: 中心区域的掩码 和 整张图的掩码
    """
    w, h = mini_map.shape[1], mini_map.shape[0]
    cx, cy = w // 2, h // 2
    r = constants.TEMPLATE_ARROW_R
    center = mini_map[cy-r:cy+r, cx-r:cx+r]
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
    kernel = np.ones((7, 7), np.uint8)
    cv2.dilate(src=whole_mask, dst=whole_mask, kernel=kernel, iterations=1)
    return mask, whole_mask


def get_arrow_template(mini_map: MatLike):
    """
    找一个传送点下来朝正右方的地方 截取小箭头的template 推荐位置 空间站黑塔-支援舱段-
    :param mini_map: 小地图
    :return: 模板
    """
    bw, _ = get_arrow_mask(mini_map)
    d0 = bw.shape[0]
    all_template = np.zeros((8 * d0, 9 * d0), dtype=np.uint8)
    for i in range(8):
        for j in range(9):
            offset_x = j * d0
            offset_y = i * d0
            angle = ((i * 9) + j) * 5
            all_template[offset_y:offset_y+d0, offset_x:offset_x+d0] = cv2_utils.image_rotate(bw, angle)

    # 稍微扩大一下模板 方便匹配
    d1 = constants.TEMPLATE_TRANSPORT_LEN
    sx = (d1 - d0) // 2
    one_template = np.zeros((d1, d1), dtype=np.uint8)
    one_template[sx:sx+d0, sx:sx+d0] = bw

    return one_template, all_template


def get_angle_from_arrow(arrow: MatLike, all_template: MatLike, one_template: MatLike,
                         im: ImageMatcher,
                         show: bool = False) -> int:
    """
    用小地图上的箭头 计算当前方向 正右方向为0度 逆时针旋转为正度数
    :param arrow: 已经提取好的白色的箭头
    :param all_template: 模板 每5度一张图的模板
    :param one_template: 模板 0度的模板
    :param im: 图片匹配器
    :param show: 显示结果
    :return: 角度
    """
    result = im.match_image(all_template, arrow, threshold=0.9)
    if len(result) == 0:
        return None

    if show:
        cv2_utils.show_image(all_template, result.max, win_name="match_template_all")

    d = constants.TEMPLATE_ARROW_LEN

    row = result.max.cy // d
    col = result.max.cx // d
    base_angle = (row * 9 + col) * 5
    best_angle = None
    best_result = None
    for i in range(11):  # -5 ~ +5 试一遍
        test_angle = base_angle + i - 5
        rotate_template = cv2_utils.image_rotate(one_template, test_angle)
        if show:
            cv2_utils.show_image(rotate_template, win_name="rotate_template")
            cv2_utils.show_image(arrow, win_name="arrow")
        result = im.match_image(rotate_template, arrow, threshold=0.9)
        if len(result) == 0:
            continue
        if best_result is None or result.max.confidence > best_result.confidence:
            best_angle = test_angle
            best_result = result.max

    if best_angle is not None and best_angle < 0:
        best_angle += 360
    return best_angle