import cv2
import numpy as np
from cv2.typing import MatLike

import basic.cal_utils
from basic import cal_utils
from basic.img import MatchResult, cv2_utils
from basic.log_utils import log
from sr import constants
from sr.config.game_config import MiniMapPos, get_game_config
from sr.constants.map import Region
from sr.image import ImageMatcher
from sr.image.image_holder import ImageHolder
from sr.image.sceenshot import mini_map, MiniMapInfo, LargeMapInfo


class MapCalculator:

    def __init__(self,
                 im: ImageMatcher):
        self.im: ImageMatcher = im
        self.ih: ImageHolder = im.ih
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

    def analyse_large_map(self, region: Region):
        """
        预处理 从大地图中提取出所有需要的信息
        :param region: 区域
        :param re_cal: 是否重新计算
        :return:
        """
        info = self.ih.get_large_map(region)
        info.edge = self.find_edge_mask(info.mask)
        return info

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

    def cal_character_pos(self, lm: LargeMapInfo, mm: MiniMapInfo,
                          lm_rect: tuple = None, show: bool = False,
                          retry_without_rect: bool = True,
                          running: bool = False):
        """
        根据小地图 匹配大地图 判断当前的坐标 - 先用特征匹配 最后用图片匹配兜底
        :param lm
        :param mm
        :param lm_rect: 大地图特定区域
        :param retry_without_rect: 失败时是否去除特定区域进行全图搜索
        :param show: 是否显示结果
        :param running: 角色是否在移动 移动时候小地图会缩小
        :return:
        """
        log.debug("准备计算当前位置 大地图区域 %s", lm_rect)

        result: MatchResult = None

        # 匹配结果 是缩放后的 offset 和宽高
        if mm.sp_result is not None and len(mm.sp_result) > 0:  # 有特殊点的时候 使用特殊点倒推位置
            result = self.cal_character_pos_by_sp_result(lm, mm, lm_rect=lm_rect, show=show)
            if result is None:  # 倒推位置失败 使用特征匹配
                result = self.cal_character_pos_by_feature_match(lm, mm, lm_rect=lm_rect, show=show)

        if result is None:  # 使用模板匹配 用道路掩码的
            result: MatchResult = self.cal_character_pos_by_road_mask(lm, mm, lm_rect=lm_rect, running=running, show=show)

        # if result is None:  # 特征匹配失败 或者无特殊点的时候 使用模板匹配 用原图的
        #     result: MatchResult = self.cal_character_pos_by_template_match(lm, mm, lm_rect=lm_rect, running=running, show=show)

        if result is None:
            if lm_rect is not None and retry_without_rect:  # 整张大地图试试
                return self.cal_character_pos(lm, mm, running=running, show=show)
            else:
                return None, None

        offset_x = result.x
        offset_y = result.y
        scale = result.template_scale
        # 小地图缩放后中心点在大地图的位置 即人物坐标
        center_x = offset_x + result.w // 2
        center_y = offset_y + result.h // 2

        if show:
            cv2_utils.show_overlap(lm.origin, mm.origin, offset_x, offset_y, template_scale=scale, win_name='overlap')

        log.debug('计算当前坐标为 (%s, %s) 使用缩放 %.2f 置信度 %.2f', center_x, center_y, scale, result.confidence)

        return center_x, center_y

    def get_large_map_rect_by_pos(self, lm_shape, mm_shape, possible_pos: tuple = None):
        """
        :param lm_shape: 大地图尺寸
        :param mm_shape: 小地图尺寸
        :param possible_pos: 可能在大地图的位置 (x,y,d)。 (x,y) 是上次在的位置 d是移动的距离
        :return:
        """
        if possible_pos is not None:  # 传入了潜在位置 那就截取部分大地图再进行匹配
            lr = mm_shape[0] // 2  # 小地图半径
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
            if lm_offset_x2 > lm_shape[1]:
                lm_offset_x2 = lm_shape[1]
            if lm_offset_y2 > lm_shape[0]:
                lm_offset_y2 = lm_shape[0]
            return lm_offset_x, lm_offset_y, lm_offset_x2, lm_offset_y2
        else:
            return None

    def cal_character_pos_by_feature_match(self,
                                           lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                                           lm_rect: tuple = None,
                                           show: bool = False) -> MatchResult:
        """
        使用特征匹配 在大地图上匹配小地图的位置
        :param lm_info: 大地图信息
        :param mm_info: 小地图信息
        :param lm_rect: 圈定的大地图区域 传入后更准确
        :param show: 是否显示调试结果
        :return:
        """
        template_kps, template_desc = mm_info.kps, mm_info.desc
        source_kps, source_desc = lm_info.kps, lm_info.desc

        # 筛选范围内的特征点
        if lm_rect is not None:
            kps = []
            desc = []
            for i in range(len(source_kps)):
                p: cv2.KeyPoint = source_kps[i]
                d = source_desc[i]
                if basic.cal_utils.in_rect(p.pt, lm_rect):
                    kps.append(p)
                    desc.append(d)
            source_kps = kps
            source_desc = np.array(desc)

        if len(template_kps) == 0 or len(source_kps) == 0:
            return None

        source_mask = lm_info.mask

        good_matches, offset_x, offset_y, template_scale = cv2_utils.feature_match(
            source_kps, source_desc,
            template_kps, template_desc,
            source_mask)

        if show:
            source = lm_info.origin
            template = mm_info.origin
            template_mask = mm_info.feature_mask
            source_with_keypoints = cv2.drawKeypoints(source, source_kps, None)
            cv2_utils.show_image(source_with_keypoints, win_name='source_with_keypoints')
            template_with_keypoints = cv2.drawKeypoints(cv2.bitwise_and(template, template, mask=template_mask), template_kps, None)
            cv2_utils.show_image(template_with_keypoints, win_name='template_with_keypoints')
            all_result = cv2.drawMatches(template, template_kps, source, source_kps, good_matches, None, flags=2)
            cv2_utils.show_image(all_result, win_name='all_match')

        if offset_x is not None:
            template_w = mm_info.gray.shape[1]
            template_h = mm_info.gray.shape[0]
            # 小地图缩放后的宽度和高度
            scaled_width = int(template_w * template_scale)
            scaled_height = int(template_h * template_scale)

            return MatchResult(1, offset_x, offset_y, scaled_width, scaled_height,
                               template_scale=template_scale)
        else:
            return None

    def cal_character_pos_by_template_match(self,
                                            lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                                            lm_rect: tuple = None,
                                            running: bool = False,
                                            show: bool = False) -> MatchResult:
        """
        使用模板匹配 在大地图上匹配小地图的位置 会对小地图进行缩放尝试
        :param lm_info: 大地图信息
        :param mm_info: 小地图信息
        :param lm_rect: 圈定的大地图区域 传入后更准确
        :param running: 任务是否在跑动
        :param show: 是否显示调试结果
        :return:
        """
        template_w = mm_info.gray.shape[1]
        template_h = mm_info.gray.shape[0]
        source = lm_info.origin if lm_rect is None else cv2_utils.crop_image(lm_info.origin, lm_rect)
        target: MatchResult = None
        target_scale = None
        # 使用道路掩码
        origin_template_mask = cv2_utils.dilate(mm_info.road_mask, 10)
        origin_template_mask = cv2.bitwise_and(origin_template_mask, mm_info.circle_mask)
        for scale in mini_map.get_mini_map_scale_list(running):
            if scale > 1:
                dest_size = (int(template_w * scale), int(template_h * scale))
                template = cv2.resize(mm_info.origin, dest_size)
                template_mask = cv2.resize(origin_template_mask, dest_size)
            else:
                template = mm_info.origin
                template_mask = origin_template_mask

            result = self.im.match_image(source, template, mask=template_mask, threshold=0.4, ignore_inf=True)

            if show:
                cv2_utils.show_image(source, win_name='template_match_source')
                cv2_utils.show_image(template, win_name='template_match_template')
                cv2_utils.show_image(template_mask, win_name='template_match_template_mask')
                # cv2_utils.show_image(cv2.bitwise_and(template, template_mask), win_name='template_match_template')
                # cv2.waitKey(0)

            if result.max is not None:
                target = result.max
                target_scale = scale
                break  # 节省点时间 其中一个缩放匹配到就可以了 也不用太精准
        if target is not None:
            offset_x = target.x + (lm_rect[0] if lm_rect is not None else 0)
            offset_y = target.y + (lm_rect[1] if lm_rect is not None else 0)
            return MatchResult(target.confidence, offset_x, offset_y, target.w, target.h, target_scale)
        else:
            return None

    def cal_character_pos_by_sp_result(self,
                                       lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                                       lm_rect: tuple = None,
                                       show: bool = False) -> MatchResult:
        """
        根据特殊点 计算小地图在大地图上的位置
        :param lm_info: 大地图信息
        :param mm_info: 小地图信息
        :param lm_rect: 圈定的大地图区域 传入后更准确
        :param show: 是否显示调试结果
        :return:
        """
        mm_height, mm_width = mm_info.gray.shape[:2]

        lm_sp_map = constants.map.get_sp_type_in_rect(lm_info.region, lm_rect)

        cal_pos_list = []

        for template_id, v in mm_info.sp_result.items():
            lm_sp = lm_sp_map.get(template_id) if template_id in lm_sp_map else []
            if len(lm_sp) == 0:
                continue
            for r in v:
                # 特殊点是按照大地图缩放比例获取的 因为可以反向将小地图缩放回人物静止时的大小
                mm_scale = 1 / r.template_scale
                x = r.x / r.template_scale
                y = r.y / r.template_scale
                # 特殊点中心在小地图上的位置
                cx = int(x + r.w // 2)
                cy = int(y + r.h // 2)
                scaled_width = int(mm_width / r.template_scale)
                scaled_height = int(mm_height / r.template_scale)

                # 通过大地图上相同的特殊点 反推小地图在大地图上的偏移量
                for sp in lm_sp:
                    cal_x = sp.lm_pos[0] - cx
                    cal_y = sp.lm_pos[1] - cy
                    cal_pos_list.append(MatchResult(1, cal_x, cal_y, scaled_width, scaled_height, template_scale=mm_scale))

        if len(cal_pos_list) == 0:
            return None

        # 如果小地图上有个多个特殊点 则合并临近的结果 越多相同结果代表置信度越高
        merge_pos_list = []
        for pos_1 in cal_pos_list:
            merge = False
            for pos_2 in merge_pos_list:
                if cal_utils.distance_between((pos_1.x, pos_1.y), (pos_2.x, pos_2.y)) < 10:
                    merge = True
                    pos_2.confidence += 1

            if not merge:
                merge_pos_list.append(pos_1)

        # 找出合并个数最多的 如果有合并个数一样的 则放弃本次结果
        target_pos = None
        same_confidence = False
        for pos in merge_pos_list:
            if target_pos is None:
                target_pos = pos
            elif pos.confidence > target_pos.confidence:
                target_pos = pos
                same_confidence = False
            elif pos.confidence == target_pos.confidence:
                same_confidence = True

        return None if same_confidence else target_pos

    def cal_character_pos_by_road_mask(self,
                                       lm_info: LargeMapInfo, mm_info: MiniMapInfo,
                                       lm_rect: tuple = None,
                                       running: bool = False,
                                       show: bool = False) -> MatchResult:
        """
        使用模板匹配 在大地图上匹配小地图的位置 会对小地图进行缩放尝试
        :param lm_info: 大地图信息
        :param mm_info: 小地图信息
        :param lm_rect: 圈定的大地图区域 传入后更准确
        :param running: 任务是否在跑动
        :param show: 是否显示调试结果
        :return:
        """
        template_w = mm_info.gray.shape[1]
        template_h = mm_info.gray.shape[0]
        source = lm_info.gray if lm_rect is None else cv2_utils.crop_image(lm_info.gray, lm_rect)
        target: MatchResult = None
        target_scale = None
        # 使用道路掩码
        origin_template = mm_info.gray
        origin_template_mask = mm_info.center_mask
        for scale in mini_map.get_mini_map_scale_list(running):
            if scale > 1:
                dest_size = (int(template_w * scale), int(template_h * scale))
                template = cv2.resize(origin_template, dest_size)
                template_mask = cv2.resize(origin_template_mask, dest_size)
            else:
                template = origin_template
                template_mask = origin_template_mask

            result = self.im.match_image(source, template, mask=template_mask, threshold=0.4, ignore_inf=True)

            if show:
                cv2_utils.show_image(source, win_name='template_match_source')
                cv2_utils.show_image(cv2.bitwise_and(template, template_mask), win_name='template_match_template')
                # cv2_utils.show_image(template, win_name='template_match_template')
                cv2_utils.show_image(template_mask, win_name='template_match_template_mask')
                # cv2.waitKey(0)

            if result.max is not None:
                if target is None or result.max.confidence > target.confidence:
                    target = result.max
                    target_scale = scale
                    # break  # 节省点时间 其中一个缩放匹配到就可以了 也不用太精准
        if target is not None:
            offset_x = target.x + (lm_rect[0] if lm_rect is not None else 0)
            offset_y = target.y + (lm_rect[1] if lm_rect is not None else 0)
            return MatchResult(target.confidence, offset_x, offset_y, target.w, target.h, target_scale)
        else:
            return None