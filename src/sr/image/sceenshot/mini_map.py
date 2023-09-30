from typing import List

import cv2
import numpy as np
from cv2.typing import MatLike

from basic.img import cv2_utils, MatchResultList, MatchResult
from sr import constants
from sr.image import ImageMatcher, TemplateImage
from sr.image.image_holder import ImageHolder
from sr.image.sceenshot import MiniMapInfo


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
    :return: 角度 正右方向为0度 顺时针旋转为正度数
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
    return 360 - best_angle


def analyse_arrow_and_angle(mini_map: MatLike, im: ImageMatcher):
    """
    在小地图上获取小箭头掩码和角度
    :param mini_map: 小地图图片
    :param im: 图片匹配器
    :return:
    """
    center_arrow_mask, arrow_mask = get_arrow_mask(mini_map)
    all_template = im.get_template('arrow_all').mask
    one_template = im.get_template('arrow_one').mask
    angle = get_angle_from_arrow(center_arrow_mask, all_template, one_template, im)  # 正右方向为0度 顺时针旋转为正度数
    return center_arrow_mask, arrow_mask, angle


def get_edge_mask_by_hsv(mm: MatLike, arrow_mask: MatLike):
    """
    背景亮的時候效果很差
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

def find_map_special_point_mask(gray_map_image: MatLike,
                                is_little_map: bool = False):
    """
    在地图中 圈出传送点、商铺点等可点击交互的的特殊点
    :param gray_map_image: 灰度地图
    :param is_little_map: 是否小地图
    :return: 特殊点组成的掩码图 特殊点是白色255、特殊点的匹配结果
    """
    sp_match_result = {}
    mask = np.zeros(gray_map_image.shape[:2], dtype=np.uint8)
    source_image = gray_map_image
    # 找出特殊点位置
    for prefix in ['mm_tp', 'mm_sp']:
        for i in range(100):
            if i == 0:
                continue
            start_time = time.time()
            template_id = '%s_%02d' % (prefix, i)
            template: TemplateImage = self.im.get_template(template_id)
            if template is None:
                break
            alpha = template.mask

            match_result = self.im.match_template(
                source_image, template_id, template_type='gray',
                threshold=constants.THRESHOLD_SP_TEMPLATE_IN_LITTLE_MAP_CENTER if is_little_map else constants.THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP,
                ignore_inf=True)

            if is_little_map:
                cx, cy = source_image.shape[1] // 2, source_image.shape[0] // 2
                cr = constants.TEMPLATE_ARROW_LEN // 2
                cx1, cy1 = cx - cr, cy - cr
                cx2, cy2 = cx + cr, cy + cr
                real_match_result = MatchResultList()
                for r in match_result:
                    rx1, ry1 = r.x, r.y
                    rx2, ry2 = r.x + r.w, r.y + r.h
                    overlap = cv2_utils.calculate_overlap_area((cx1, cy1, cx2, cy2), (rx1, ry1, rx2, ry2))
                    total = r.w * r.h
                    threshold = (constants.THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP - constants.THRESHOLD_SP_TEMPLATE_IN_LITTLE_MAP_CENTER) * (1.0 - overlap / total) + constants.THRESHOLD_SP_TEMPLATE_IN_LITTLE_MAP_CENTER
                    if r.confidence > threshold:
                        real_match_result.append(r)

                match_result = real_match_result

            if len(match_result) > 0:
                sp_match_result[template_id] = match_result
            for r in match_result:
                mask[r.y:r.y+r.h, r.x:r.x+r.w] = cv2.bitwise_or(mask[r.y:r.y+r.h, r.x:r.x+r.w], alpha)
            log.debug('特殊点匹配一次 %.4f s', time.time() - start_time)
    return mask, sp_match_result


def get_sp_mask_by_feature_match(mm_info: MiniMapInfo, ih: ImageHolder,
                                 template_type: str = 'origin',
                                 template_list: List = None,
                                 show: bool = False):
    """
    在小地图上找到特殊点
    使用特征匹配 每个模板最多只能找到一个
    :param mm_info: 小地图信息
    :param ih: 图片加载器
    :param template_type: 模板类型
    :param template_list: 限定种类的特殊点
    :param show: 是否展示结果
    :return:
    """
    feature_detector = cv2.SIFT_create()
    source = mm_info.origin if template_type == 'origin' else mm_info.gray
    source_mask = mm_info.center_mask
    source_kps, source_desc = feature_detector.detectAndCompute(source, mask=source_mask)

    sp_mask = np.zeros_like(mm_info.gray)
    sp_match_result = {}
    for prefix in ['mm_tp', 'mm_sp']:
        for i in range(100):
            if i == 0:
                continue

            template_id = '%s_%02d' % (prefix, i)
            if template_list is not None and template_id not in template_list:
                continue

            match_result_list = MatchResultList()
            t: TemplateImage = ih.get_template(template_id)
            if t is None:
                break
            template = t.get(template_type)
            template_mask = t.mask

            # TODO 后续预处理
            template_kps, template_desc = feature_detector.detectAndCompute(template, mask=template_mask)

            good_matches, offset_x, offset_y, scale = cv2_utils.feature_match(
                source_kps, source_desc,
                template_kps, template_desc,
                source_mask=source_mask)

            if offset_x is not None:
                mr = MatchResult(1, offset_x, offset_y, template.shape[1], template.shape[0], scale=scale)
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


def get_enemy_location(mini_map: MatLike) -> List:
    """
    在小地图上找红点敌人的位置
    :param mini_map: 小地图截图
    :return: 敌人在小地图上的坐标
    """
    return []


def is_under_attack(mini_map: MatLike) -> bool:
    """
    根据小地图边缘 判断是否被锁定
    :param mini_map:
    :return:
    """
    return False