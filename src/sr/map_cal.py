import math

import cv2
import numpy as np
from cv2.typing import MatLike

from basic.img import MatchResult, cv2_utils
from basic.log_utils import log
from sr import constants
from sr.config.game_config import MiniMapPos, get_game_config
from sr.image import ImageMatcher
from sr.image.sceenshot import mini_map, MiniMapInfo, LargeMapInfo, large_map


class MapCalculator:

    def __init__(self,
                 im: ImageMatcher):
        self.im = im
        self.feature_detector = cv2.SIFT_create()
        self.mm_pos: MiniMapPos = get_game_config().mini_map_pos

    def cut_mini_map(self, screen: MatLike):
        """
        从整个游戏窗口截图中 裁剪出小地图部分
        :param screen: 屏幕截图
        :return:
        """
        if self.mm_pos is not None:
            # 截取圆圈的正方形
            lm = screen[self.mm_pos.ly:self.mm_pos.ry, self.mm_pos.lx:self.mm_pos.rx]
        else:
            x, y = 60, 110  # 默认的小地图坐标
            x2, y2 = 240, 280
            lm = screen[y:y2, x:x2]

        return lm

    def cal_little_map_pos(self, screen: MatLike):
        """
        计算小地图的坐标
        通过截取屏幕左上方部分 找出最大的圆圈 就是小地图。
        部分场景无法准确识别 所以使用一次校准后续读取配置使用。
        最容易匹配地点在【空间站黑塔】【基座舱段】【接待中心】传送点
        :param screen: 屏幕截图
        """
        # 左上角部分
        x, y = 0, 0
        x2, y2 = 340, 380
        image = screen[y:y2, x:x2]

        # 对图像进行预处理
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1.2, 100, minRadius=80, maxRadius=100)  # 小地图大概的圆半径

        # 如果找到了圆
        if circles is not None:
            circles = np.uint16(np.around(circles))
            tx, ty, tr = 0, 0, 0

            # 保留半径最大的圆
            for circle in circles[0, :]:
                if circle[2] > tr:
                    tx, ty, tr = circle[0], circle[1], circle[2]

            self.mm_pos = MiniMapPos(tx, ty, tr)
            log.debug('计算小地图所在坐标为 %s', self.mm_pos)
        else:
            log.error('无法找到小地图的圆')

    def analyse_mini_map(self, mm: MatLike):
        """
        预处理 从小地图中提取出所有需要的信息
        :param mm: 小地图 左上角的一个正方形区域
        :return:
        """
        info = MiniMapInfo()
        info.origin = mm
        info.center_arrow_mask, info.arrow_mask, info.angle = mini_map.analyse_arrow_and_angle(mm, self.im)
        info.gray = cv2.cvtColor(mm, cv2.COLOR_BGR2GRAY)

        # 小地图要只判断中间正方形 圆形边缘会扭曲原来特征
        h, w = mm.shape[1], mm.shape[0]
        cx, cy = w // 2, h // 2
        r = math.floor(h / math.sqrt(2) / 2) - 8
        info.center_mask = np.zeros_like(info.gray)
        info.center_mask[cy - r:cy + r, cx - r:cx + r] = 255

        info.feature_mask = np.zeros_like(info.gray)
        cv2.circle(info.feature_mask, (cx, cy), h // 2 - 5, 255, -1)
        ar = constants.TEMPLATE_ARROW_R # 小箭头
        cv2.rectangle(info.feature_mask, (cx - ar, cy - ar), (cx + ar, cy + ar), 0, -1)  # 特征提取忽略小箭头部分

        info.sp_mask, info.sp_result = mini_map.get_sp_mask_by_feature_match(info, self.im.ih)
        info.road_mask = self.find_map_road_mask(mm, sp_mask=info.sp_mask, arrow_mask=info.arrow_mask, is_little_map=True, angle=info.angle)
        info.gray, info.feature_mask = self.merge_all_map_mask(info.gray, info.road_mask, info.sp_mask)

        info.edge = self.find_edge_mask(info.feature_mask)

        info.kps, info.desc = self.feature_detector.detectAndCompute(info.gray, mask=info.feature_mask)

        return info

    def analyse_large_map(self, lm: MatLike):
        """
        预处理 从大地图中提取出所有需要的信息
        :param lm:
        :return:
        """
        info = LargeMapInfo()
        info.origin = lm
        gray = cv2.cvtColor(lm, cv2.COLOR_BGRA2GRAY)

        sp_mask, _ = large_map.get_sp_mask_by_template_match(info, self.im.ih)
        road_mask = self.find_map_road_mask(lm, sp_mask)
        info.gray, info.mask = self.merge_all_map_mask(gray, road_mask, sp_mask)
        info.edge = self.find_edge_mask(info.mask)

        info.kps, info.desc = self.feature_detector.detectAndCompute(info.gray, mask=info.mask)
        return info

    def merge_all_map_mask(self, gray_image: MatLike,
                           road_mask, sp_mask):
        """
        :param gray_image:
        :param road_mask:
        :param sp_mask:
        :return:
        """
        usage = gray_image.copy()

        # 稍微膨胀一下
        kernel = np.ones((3, 3), np.uint8)
        expand_sp_mask = cv2.dilate(sp_mask, kernel, iterations=1)

        all_mask = cv2.bitwise_or(road_mask, expand_sp_mask)
        usage[np.where(all_mask == 0)] = constants.COLOR_WHITE_GRAY
        usage[np.where(road_mask == 255)] = constants.COLOR_MAP_ROAD_GRAY
        return usage, all_mask

    def find_map_road_mask(self, map_image: MatLike,
                           sp_mask: MatLike = None,
                           arrow_mask: MatLike = None,
                           is_little_map: bool = False,
                           angle: int = -1) -> MatLike:
        """
        在地图中 按接近道路的颜色圈出地图的主体部分 过滤掉无关紧要的背景
        :param map_image: 地图图片
        :param sp_mask: 特殊点的掩码 道路掩码应该排除这部分
        :param arrow_mask: 小箭头的掩码 只有小地图有
        :param is_little_map: 是否小地图 小地图部分会额外补偿中心点散发出来的扇形朝向部分
        :param angle: 只有小地图上需要传入 表示当前朝向
        :return: 道路掩码图 能走的部分是白色255
        """
        # 按道路颜色圈出
        lower_color = np.array([45, 45, 45], dtype=np.uint8)
        # 大地图颜色比较简单
        upper_color = np.array([70, 70, 70] if is_little_map else [90, 90, 90], dtype=np.uint8)
        road_mask = cv2.inRange(map_image, lower_color, upper_color)

        # 对于小地图 要特殊扫描中心点附近的区块
        if is_little_map:
            radio_mask = self.find_little_map_radio_mask(map_image, angle)
            # cv2_utils.show_image(radio_mask, win_name='radio_mask')
            center_mask = cv2.bitwise_or(arrow_mask, radio_mask)
            road_mask = cv2.bitwise_or(road_mask, center_mask)

        # 合并特殊点进行连通性检测
        to_check_connection = cv2.bitwise_or(road_mask, sp_mask) if sp_mask is not None else road_mask
        # cv2_utils.show_image(to_check_connection, win_name='to_check_connection')

        # 非道路连通块 < 50的，认为是噪点 加入道路
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(cv2.bitwise_not(to_check_connection), connectivity=4)
        large_components = []
        for label in range(1, num_labels):
            if stats[label, cv2.CC_STAT_AREA] < 50:
                large_components.append(label)
        for label in large_components:
            to_check_connection[labels == label] = 255

        # 找到多于500个像素点的连通道路 这些才是真的路
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(to_check_connection, connectivity=4)
        large_components = []
        for label in range(1, num_labels):
            if stats[label, cv2.CC_STAT_AREA] > 500:
                large_components.append(label)
        real_road_mask = np.zeros(map_image.shape[:2], dtype=np.uint8)
        for label in large_components:
            real_road_mask[labels == label] = 255

        # 排除掉特殊点
        if sp_mask is not None:
            real_road_mask = cv2.bitwise_and(real_road_mask, cv2.bitwise_not(sp_mask))

        return real_road_mask

    def find_little_map_radio_mask(self, map_image: MatLike, angle: int = -1):
        """
        小地图中心雷达区的掩码
        :param map_image:
        :param angle:
        :return:
        """
        radio_mask = np.zeros(map_image.shape[:2], dtype=np.uint8)  # 圈出雷达区的掩码
        center = (map_image.shape[1] // 2, map_image.shape[0] // 2)  # 中心点坐标
        radius = 55  # 扇形半径 这个半径内
        color = 255  # 扇形颜色（BGR格式）
        thickness = -1  # 扇形边框线宽度（负值表示填充扇形）
        if angle != -1:  # 知道当前角度的话 画扇形
            start_angle = angle - 45  # 扇形起始角度（以度为单位）
            end_angle = angle + 45  # 扇形结束角度（以度为单位）
            cv2.ellipse(radio_mask, center, (radius, radius), 0, start_angle, end_angle, color, thickness)  # 画扇形
        else:  # 圆形兜底
            cv2.circle(radio_mask, center, radius, color, thickness)  # 画扇形
        radio_map = cv2.bitwise_and(map_image, map_image, mask=radio_mask)
        # cv2_utils.show_image(radio_map, win_name='radio_map')
        lower_color = np.array([70, 70, 60, 255] if map_image.shape[2] == 4 else [70, 70, 60], dtype=np.uint8)
        upper_color = np.array([130, 130, 100, 255] if map_image.shape[2] == 4 else [130, 130, 100], dtype=np.uint8)
        road_radio_mask = cv2.inRange(radio_map, lower_color, upper_color)
        return road_radio_mask

    def find_little_map_arrow_mask(self, map_image: MatLike):
        x, y = map_image.shape[1] // 2, map_image.shape[0] // 2
        r = constants.LITTLE_MAP_CENTER_ARROW_LEN
        # 匹配箭头效果不太好 暂时整块中心区域都标记了
        # r = constants.TEMPLATE_ARROW_LEN
        # arrow_part = map_image[y-r:y+r, x-r:x+r]
        # lower_color = np.array([210, 190, 0, 255])
        # upper_color = np.array([255, 240, 60, 255])
        # mask = cv2.inRange(arrow_part, lower_color, upper_color)

        arrow_mask = np.zeros(map_image.shape[:2], dtype=np.uint8)
        arrow_mask[y-r:y+r, x-r:x+r] = constants.COLOR_WHITE_GRAY
        return arrow_mask

    def find_mini_map_edge_mask(self, mm: MatLike):
        """
        小地图道路边缘掩码 暂时不需要
        :param mm: 小地图图片
        :return:
        """
        lower, upper = 180, 230
        lower_color = np.array([lower, lower, lower])
        upper_color = np.array([upper, upper, upper])
        edge_mask = cv2.inRange(mm, lower_color, upper_color)
        # 稍微膨胀一下
        kernel = np.ones((3, 3), np.uint8)
        expand_edge_mask = cv2.dilate(edge_mask, kernel, iterations=1)
        return expand_edge_mask

    def find_edge_mask(self, road_mask: MatLike):
        """
        大地图道路边缘掩码 暂时不需要
        :param road_mask:
        :return:
        """
        # return cv2.Canny(road_mask, threshold1=200, threshold2=230)

        # 查找轮廓
        contours, hierarchy = cv2.findContours(road_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # 创建空白图像作为绘制轮廓的画布
        edge_mask = np.zeros_like(road_mask)
        # 绘制轮廓
        cv2.drawContours(edge_mask, contours, -1, 255, 2)
        return edge_mask



    def cal_character_pos_with_scale(self, lm: LargeMapInfo, mm: MiniMapInfo,
                                     possible_pos: tuple = None, show: bool = False,
                                     retry_without_pos: bool = True):
        """
        根据小地图 匹配大地图 判断当前的坐标 - 先用特征匹配 最后用图片匹配兜底
        :param lm
        :param mm
        :param possible_pos: 可能在大地图的位置 (x,y,d)。 (x,y) 是上次在的位置 d是移动的距离。传入后会优先在这附近匹配 效率更高；失败后再整个大地图匹配
        :param retry_without_pos: 失败时是否去除可能点进行全图搜索
        :param show: 是否显示结果
        :return:
        """
        log.debug("准备计算当前位置 前一个位置为 %s", possible_pos)
        lm_offset_x = 0
        lm_offset_y = 0
        lm_offset_x2 = lm.gray.shape[1]
        lm_offset_y2 = lm.gray.shape[0]
        if possible_pos is not None:  # 传入了潜在位置 那就截取部分大地图再进行匹配
            lr = mm.gray.shape[0] // 2  # 小地图半径
            x, y, r = int(possible_pos[0]), int(possible_pos[1]), int(possible_pos[2])
            ur = r + lr + lr // 2  # 潜在位置半径 = 移动距离 + 1.5倍的小地图半径
            lm_offset_x = x - ur
            lm_offset_y = y - ur
            lm_offset_x2 = x + ur
            lm_offset_y2 = y + ur
            if lm_offset_x < 0:  # 防止越界
                lm_offset_x = 0
            if lm_offset_y < 0:
                lm_offset_y = 0
            if lm_offset_x2 > lm.gray.shape[1]:
                lm_offset_x2 = lm.gray.shape[1]
            if lm_offset_y2 > lm.gray.shape[0]:
                lm_offset_y2 = lm.gray.shape[0]

        source = lm.gray[lm_offset_y:lm_offset_y2, lm_offset_x:lm_offset_x2]
        source_mask = lm.mask[lm_offset_y:lm_offset_y2, lm_offset_x:lm_offset_x2]

        template_h, template_w = mm.gray.shape[1], mm.gray.shape[0]
        offset_x, offset_y = None, None

        if mm.sp_result is not None and len(mm.sp_result) > 0:  # 有特殊点的时候 直接在原灰度图上匹配即可
            cv2_utils.show_image(source, win_name='source')
            cv2_utils.show_image(source_mask, win_name='source_mask')
            template = mm.gray
            offset_x, offset_y, template_scale = self.feature_match(source, source_mask, template, mm.feature_mask, show=show)

            if offset_x is not None:
                # 小地图缩放后的宽度和高度
                scaled_width = int(template_w * template_scale)
                scaled_height = int(template_h * template_scale)

                # 大地图可能剪裁过 加上剪裁的offset
                offset_x = lm_offset_x + offset_x
                offset_y = lm_offset_y + offset_y

                # 小地图缩放后中心点在大地图的位置 即人物坐标
                center_x = offset_x + scaled_width // 2
                center_y = offset_y + scaled_height // 2
        else:  # 无特殊点的时候 绘制边缘来匹配
            source_edge = lm.edge[lm_offset_y:lm_offset_y2, lm_offset_x:lm_offset_x2]
            target: MatchResult = None
            template_scale = None
            for scale in [1, 1.05, 1.10, 1.15, 1.20, 1.25]:
                if scale > 1:
                    dest_size = (int(template_w * scale), int(template_h * scale))
                    template_edge = cv2.resize(mm.edge, dest_size)
                    template_edge_mask = cv2.resize(mm.center_mask, dest_size)
                else:
                    template_edge = mm.edge
                    template_edge_mask = mm.center_mask
                result: MatchResult = self.template_match(source_edge, template_edge, template_mask=template_edge_mask, show=show)
                if result is not None and (target is None or result.confidence > target.confidence):
                    target = result
                    template_scale = scale
            if target is not None:
                offset_x, offset_y = target.x + lm_offset_x, target.y + lm_offset_y
                center_x = offset_x + target.w // 2
                center_y = offset_y + target.h // 2

        if offset_x is None:
            if possible_pos is not None and retry_without_pos:  # 整张大地图试试
                return self.cal_character_pos_with_scale(lm, mm, show=show)
            else:
                return None, None

        if show:
            cv2_utils.show_overlap(lm.gray, mm.gray, offset_x, offset_y, template_scale=template_scale, win_name='overlap')

        log.debug('计算当前坐标为 (%s, %s) 使用缩放 %.2f', center_x, center_y, template_scale)

        return center_x, center_y

    def feature_match(self, source, source_mask, template, template_mask,
                      show: bool = False):
        template_kps, template_desc = self.feature_detector.detectAndCompute(template, mask=template_mask)
        source_kps, source_desc = self.feature_detector.detectAndCompute(source, mask=source_mask)

        if len(template_kps) == 0 or len(source_kps) == 0:
            return None, None, None

        good_matches, offset_x, offset_y, scale = cv2_utils.feature_match(
            source_kps, source_desc,
            template_kps, template_desc,
            source_mask)

        if show:
            source_with_keypoints = cv2.drawKeypoints(source, source_kps, None)
            cv2_utils.show_image(source_with_keypoints, win_name='source_with_keypoints')
            template_with_keypoints = cv2.drawKeypoints(template, template_kps, None)
            cv2_utils.show_image(cv2.bitwise_and(template_with_keypoints, template_with_keypoints, mask=template_mask), win_name='template_with_keypoints')
            all_result = cv2.drawMatches(template, template_kps, source, source_kps, good_matches, None, flags=2)
            cv2_utils.show_image(all_result, win_name='all_match')

        return offset_x, offset_y, scale

    def template_match(self, source, template, template_mask, show: bool = False) -> MatchResult:
        result = self.im.match_image(source, template, mask=template_mask, threshold=0.4, ignore_inf=True)

        if show:
            cv2_utils.show_image(source, win_name='template_match_source')
            cv2_utils.show_image(template, win_name='template_match_template')
            cv2_utils.show_image(template_mask, win_name='template_match_template_mask')
            # cv2_utils.show_image(cv2.bitwise_and(template, template_mask), win_name='template_match_template')

        if len(result) == 0:
            return None

        target = result.max

        if show:
            cv2_utils.show_image(source, result, win_name='template_match_all')

        return target