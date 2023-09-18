import cv2
import numpy as np
from PIL.Image import Image

import sr
from basic.img import ImageMatcher, MatchResult, cv2_utils, MatchResultList
from basic.img.cv2_matcher import CvImageMatcher
from basic.log_utils import log
from sr import constants
from sr.config import ConfigHolder


class LittleMapPos:

    def __init__(self, x, y, r):
        # 原点
        self.x = int(x)
        self.y = int(y)
        self.r = int(r)
        # 矩形左上角
        self.lx = self.x - self.r
        self.ly = self.y - self.r
        # 矩形右下角
        self.rx = self.x + self.r
        self.ry = self.y + self.r

    def __str__(self):
        return "(%d, %d) %.2f" % (self.x, self.y, self.r)


class MapCalculator:

    def __init__(self, im: CvImageMatcher,
                 screen_width: int = 1920, screen_height: int = 1080,
                 config: ConfigHolder = None):
        self.im = im
        self.x_scale = screen_width / 1920
        self.y_scale = screen_height / 1080
        self.scale: bool = self.x_scale != 1 or self.y_scale != 1
        self.map_pos: LittleMapPos = None
        if config is not None:
            lmc = config.get_config('game', 'little_map')
            self.map_pos = LittleMapPos(lmc['x'], lmc['y'], lmc['r'])

    def get_game_pos(self, x, y):
        """
        将计算过程的坐标换算成游戏分辨率的坐标
        :param x: 计算过程坐标
        :param y: 计算过程坐标
        :return: 游戏分辨率的坐标
        """
        return (x, y) if not self.scale else (x * self.x_scale, y * self.y_scale)

    def get_cal_pos(self, x, y):
        """
        将游戏分辨率的坐标换算成计算过程的坐标
        :param x: 游戏分辨率的坐标
        :param y: 游戏分辨率的坐标
        :return: 计算过程的坐标
        """
        return (x, y) if not self.scale else (x / self.x_scale, y / self.y_scale)

    def cut_little_map(self, screen: cv2.typing.MatLike):
        """
        从整个游戏窗口截图中 裁剪出小地图部分
        :param screen: 屏幕截图
        :return:
        """
        if self.map_pos is not None:
            # 截取圆圈的正方形
            lm = screen[self.map_pos.ly:self.map_pos.ry, self.map_pos.lx:self.map_pos.rx]
            # 将圆圈外的区域变透明
            lm = cv2_utils.mark_area_as_transparent(lm, [lm.shape[1] // 2, lm.shape[0] // 2, self.map_pos.r - 2], outside=True)
        else:
            x, y = 60, 110  # 默认的小地图坐标
            x2, y2 = 240, 280
            lm = screen[y:y2, x:x2]

        return lm

    def cal_little_map_pos(self, screen: cv2.typing.MatLike):
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

            self.map_pos = LittleMapPos(tx, ty, tr)
            log.debug('计算小地图所在坐标为 %s', self.map_pos)
        else:
            log.error('无法找到小地图的圆')

    def cut_little_map_arrow(self, little_map: cv2.typing.MatLike):
        """
        裁剪出小地图里的方向箭头
        :param little_map: 小地图
        :return:
        """
        l = constants.TEMPLATE_ARROW_LEN  # 箭头图片的宽高
        x, y = little_map.shape[1] // 2, little_map.shape[0] // 2
        return little_map[y - l:y + l, x - l:x + l]

    def get_cv_angle_from_arrow_angle(self, arrow_angle):
        cv_angle = None
        if arrow_angle is not None:
            cv_angle = 270 - arrow_angle if arrow_angle <= 270 else 360 - (arrow_angle - 270)
        return cv_angle

    def get_direction_by_little_map(self, little_map: cv2.typing.MatLike, matcher: ImageMatcher, threshold: float = 0.5,
                                    show_match_result: bool = False) -> int:
        """
        在整个游戏窗口的截图中，找到小地图部分，通过匹配箭头判断当前方向。
        使用前需要先按一次w前进 确保人物方向与视角朝向一致
        :param little_map: 小地图截图
        :param matcher: 图片匹配器
        :param threshold: 阈值
        :param show_match_result 显示匹配结果
        :return: 当前方向 正右方为0度
        """
        angle_result = matcher.match_template_with_rotation(little_map, constants.TEMPLATE_ARROW, threshold,
                                                            ignore_template_alpha=True)
        target: MatchResult = None
        angle: int = None  # 正上方为0度 逆时针旋转
        for k, v in angle_result.items():
            for r in v:
                if target is None or r.confidence > target.confidence:
                    target = r
                    angle = k

        convert_angle = self.get_cv_angle_from_arrow_angle(angle)

        log.debug('当前小地图匹配方向 %d 置信度 %.2f' % (convert_angle, target.confidence) if convert_angle is not None else '当前小地图未匹配到方向')
        if show_match_result:
            cv2_utils.show_image(little_map, target)

        return convert_angle

    def auto_cut_map(self, map_image: cv2.typing.MatLike,
                     is_little_map: bool = False, angle: int = -1,
                     show: bool = False):
        """
        自动剪裁地图 - 在地图中 提取道路有关的部分 其余设置为透明
        :param map_image: 原地图
        :param is_little_map: 是否小地图 小地图部分会额外补偿中心点散发出来的扇形朝向部分
        :param angle: 只有小地图上需要传入 表示当前朝向
        :param show: 是否显示
        :return: 道路有关部分的掩码、提取后的图片、特殊点的匹配结果
        """

        arrow_mask, angle = self.find_map_arrow_mask(map_image, angle=angle) if is_little_map else np.zeros(map_image.shape[:2], dtype=np.uint8)
        road_mask = self.find_map_road_mask(map_image, is_little_map=is_little_map, angle=angle)
        sp_mask, sp_match_result = self.find_map_special_point_mask(map_image,
                                                                    is_little_map=is_little_map)
        all_mask = cv2.bitwise_or(cv2.bitwise_or(road_mask, sp_mask), arrow_mask)
        usage = map_image.copy()
        usage[np.where(all_mask == 0)] = [0, 0, 0, 0]
        if show:
            cv2_utils.show_image(road_mask, win_name='road_mask')
            cv2_utils.show_image(sp_mask, win_name='sp_mask')
            cv2_utils.show_image(arrow_mask, win_name='arrow_mask')
            cv2_utils.show_image(all_mask, win_name='all_mask')
            cv2_utils.show_image(usage, win_name='usage')
        return all_mask, usage, sp_match_result

    def find_map_road_mask(self, map_image: cv2.typing.MatLike,
                           is_little_map: bool = False,
                           angle: int = -1) -> cv2.typing.MatLike:
        """
        在地图中 按接近道路的颜色圈出地图的主体部分 过滤掉无关紧要的背景
        :param map_image: 地图图片
        :param is_little_map: 是否小地图 小地图部分会额外补偿中心点散发出来的扇形朝向部分
        :param angle: 只有小地图上需要传入 表示当前朝向
        :return: 道路掩码图 能走的部分是白色255
        """
        # 按道路颜色圈出
        lower_color = np.array([45, 45, 45, 255] if map_image.shape[2] == 4 else [45, 45, 45], dtype=np.uint8)
        upper_color = np.array([75, 75, 75, 255] if map_image.shape[2] == 4 else [75, 75, 75], dtype=np.uint8)
        road_mask = cv2.inRange(map_image, lower_color, upper_color)

        # 对于小地图 要特殊扫描中心点附近的区块
        if is_little_map:
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
            upper_color = np.array([150, 140, 100, 255] if map_image.shape[2] == 4 else [150, 140, 100], dtype=np.uint8)
            road_radio_mask = cv2.inRange(radio_map, lower_color, upper_color)
            # cv2_utils.show_image(road_radio_mask, win_name='road_radio_mask')
            road_mask = cv2.bitwise_or(road_mask, road_radio_mask)

        # 找到多于500个像素点的连通块 这些才是真的路
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(road_mask, connectivity=8)
        large_components = []
        for label in range(1, num_labels):
            if stats[label, cv2.CC_STAT_AREA] > 500:
                large_components.append(label)

        # 创建一个新的 只保留连通部分
        real_road_mask = np.zeros(map_image.shape[:2], dtype=np.uint8)
        for label in large_components:
            real_road_mask[labels == label] = 255

        return real_road_mask

    def find_map_special_point_mask(self, map_image: cv2.typing.MatLike,
                                    is_little_map: bool = False):
        """
        在地图中 圈出传送点、商铺点等可点击交互的的特殊点
        :param map_image: 地图
        :param arrow_mask: 箭头掩码 只有小地图有 会忽略掉再匹配
        :return: 特殊点组成的掩码图 特殊点是白色255、特殊点的匹配结果
        """
        sp_match_result = {}
        mask = np.zeros(map_image.shape[:2], dtype=np.uint8)
        source_image = map_image
        if is_little_map:
            cx, cy = source_image.shape[1] // 2, source_image.shape[0] // 2
            cr = constants.TEMPLATE_ARROW_LEN + constants.TEMPLATE_TRANSPORT_LEN
            center_image = source_image[cy-cr:cy+cr, cx-cr:cx+cr, :]
        # 找出特殊点位置
        for prefix in ['transport_', 'exit_']:
            for i in range(100):
                if i == 0:
                    continue
                template_id = prefix + str(i)
                template_image = self.im.get_template(template_id)
                if template_image is None:
                    break
                alpha = template_image[:,:,3]

                match_result = cv2_utils.match_template(
                    source_image, template_image,
                    constants.THRESHOLD_SP_TEMPLATE_IN_LITTLE_MAP if is_little_map else constants.THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP,
                    ignore_template_alpha=True,
                    ignore_inf=True)

                if is_little_map:
                    # 小地图时 需要降低置信度 对中心点进行匹配
                    match_result_2 = cv2_utils.match_template(
                        center_image, template_image,
                        constants.THRESHOLD_SP_TEMPLATE_IN_LITTLE_MAP_CENTER,
                        ignore_template_alpha=True,
                        ignore_inf=True)
                    for r in match_result_2:
                        match_result.append(MatchResult(r.confidence, cx-cr+r.x, cy-cr+r.y, r.w, r.h))

                if len(match_result) > 0:
                    sp_match_result[template_id] = match_result
                for r in match_result:
                    mask[r.y:r.y+r.h, r.x:r.x+r.w] = cv2.bitwise_or(mask[r.y:r.y+r.h, r.x:r.x+r.w], alpha)
        return mask, sp_match_result

    def find_map_arrow_mask(self, little_map: cv2.typing.MatLike, angle: int = -1):
        """
        在小地图中间 匹配箭头
        :param little_map: 小地图图片
        :param angle: 不传入时 自动识别方向 较为耗时
        :return: 对应掩码
        """
        arrow_image = self.cut_little_map_arrow(little_map)
        target: MatchResult = None
        if angle == -1:
            angle_result = self.im.match_template_with_rotation(arrow_image, constants.TEMPLATE_ARROW,
                                                                ignore_template_alpha=True)
            angle: int = None  # 正上方为0度 逆时针旋转
            for k, v in angle_result.items():
                for r in v:
                    if target is None or r.confidence > target.confidence:
                        target = r
                        angle = k
        else:
            arrow_template = self.im.get_rotate_template(constants.TEMPLATE_ARROW, angle)
            math_result_list = self.im.match_template(arrow_image, arrow_template, ignore_template_alpha=True,
                                                      ignore_inf=True)
            for r in math_result_list:
                if target is None or r.confidence > target.confidence:
                    target = r

        angle = self.get_cv_angle_from_arrow_angle(angle)

        arrow_mask = np.zeros(arrow_image.shape[:2], dtype=np.uint8)
        lm_mask = np.zeros(little_map.shape[:2], dtype=np.uint8)

        arrow = self.im.get_rotate_template(constants.TEMPLATE_ARROW, angle)
        if target is not None:
            l = constants.TEMPLATE_ARROW_LEN  # 箭头图片的宽高
            x, y = little_map.shape[1] // 2, little_map.shape[0] // 2
            arrow_mask[target.y:target.y+target.h, target.x:target.x+target.w] = arrow[:, :, 3]
            lm_mask[y - l:y + l, x - l:x + l] = arrow_mask

        log.debug('当前人物方向为 %d', angle)
        return lm_mask, angle

    def cal_character_pos_by_feature(self, little_map: cv2.typing.MatLike, large_map: cv2.typing.MatLike, show: bool = False):
        """
        根据截图里的小地图 匹配大地图 判断当前的坐标
        :param little_map: 小地图图片
        :param large_map: 大地图图片
        :param show: 是否显示中间结果
        :return:
        """
        little_map_bw, little_map_usage, _ = self.auto_cut_map(little_map, is_little_map=True)
        source = cv2.cvtColor(large_map, cv2.COLOR_BGR2GRAY)
        template = cv2.cvtColor(little_map_usage, cv2.COLOR_BGR2GRAY)
        sift = cv2.ORB_create()

        # 创建BFMatcher对象
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

        # 检测和计算大图片的关键点和描述符
        kp1, des1 = sift.detectAndCompute(source, None)

        # 检测和计算小图片的关键点和描述符
        kp2, des2 = sift.detectAndCompute(template, None)

        # 执行特征匹配
        matches = bf.match(des1, des2)

        # 按照特征匹配的距离进行排序
        matches = sorted(matches, key=lambda x: x.distance)

        best_match = matches[0]  # 选择最佳匹配
        print(best_match)

        query_idx = best_match.queryIdx  # 大图中的关键点索引
        train_idx = best_match.trainIdx  # 小图中的关键点索引
        query_point = kp1[query_idx].pt  # 大图中的关键点坐标 (x, y)
        train_point = kp2[train_idx].pt  # 小图中的关键点坐标 (x, y)

        # 获取最佳匹配的特征点的缩放比例 小地图在人物跑动时会缩放
        query_scale = kp1[query_idx].size
        train_scale = kp2[train_idx].size
        scale = query_scale / train_scale

        # 小地图缩放后偏移量
        offset_x = query_point[0] - train_point[0] * scale
        offset_y = query_point[1] - train_point[1] * scale

        # 小地图缩放后的宽度和高度
        scaled_width = int(little_map.shape[1] * scale)
        scaled_height = int(little_map.shape[0] * scale)

        # 小地图缩放后中心点在大地图的位置 即人物坐标
        center_x = offset_x + scaled_width // 2
        center_y = offset_y + scaled_height // 2

        if show:
            result = cv2.drawMatches(source, kp1, template, kp2, [best_match], None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
            cv2_utils.show_image(result, win_name='feature_match')
            # cv2_utils.show_overlap(source, template, offset_x, offset_y, template_scale=scale, win_name='小地图覆盖大地图')

        return center_x, center_y

    def cal_character_pos_by_match(self, little_map: cv2.typing.MatLike,
                                   large_map: cv2.typing.MatLike,
                                   possible_pos: tuple = None,
                                   show: bool = False):
        """
        根据小地图 匹配大地图 判断当前的坐标 - 使用模板匹配
        :param little_map: 小地图图片 原图即可
        :param large_map: 大地图图片 usage版本
        :param possible_pos: 可能在大地图的位置 (x,y,r) 即只在大地图这个位置上匹配。 (x,y) 是上次在的位置 r是移动的距离
        :param show: 是否显示中间结果
        :return:
        """
        little_map_bw, little_map_usage, sp_match_result = self.auto_cut_map(little_map, is_little_map=True)
        if possible_pos is not None:
            lr = little_map.shape[0] // 2
            x, y, r = possible_pos[0], possible_pos[1], possible_pos[2]
            ur = r + lr + lr // 2
            offset_x = x-ur
            offset_y = y-ur
            if offset_x < 0:
                offset_x = 0
            if offset_y < 0:
                offset_y = 0
            large_map_usage = large_map[offset_y:y+ur, offset_x:x+ur, :]
        else:
            offset_x = 0
            offset_y = 0
            large_map_usage = large_map

        if show:
            cv2_utils.show_image(large_map_usage, win_name='large_map_usage')
            cv2_utils.show_image(little_map_usage, win_name='little_map_usage')
        result = self.im.match_template(large_map_usage, little_map_usage, ignore_template_alpha=True,
                                        threshold=0.45, ignore_inf=True)

        target = self.find_best_match_pos_in_large_map(large_map_usage, result, sp_match_result, show=show)

        if show:
            cv2_utils.show_image(large_map_usage, target, win_name='all')
            cv2_utils.show_image(large_map_usage, target, win_name='target')
            # cv2_utils.show_overlap(large_map, little_map, result.x, result.y, win_name='cal_character_pos_by_match')

        return (offset_x + target.x, offset_y + target.y) if target is not None else (-1, -1)


    def find_best_match_pos_in_large_map(self, large_map_usage: cv2.typing.MatLike,
                                         match_result: MatchResultList,
                                         little_map_sp_match_result: dict,
                                         show: bool = False):
        """
        在小地图可能匹配的位置中，找出最佳位置。
        如果小地图中有特殊点，大地图中也要有。但小地图中容易匹配错，所以找到尽量多的特殊点即可。
        最后筛选匹配程度最高的结果
        :param large_map_usage: 用于匹配的大地图 可能裁剪过
        :param match_result: 匹配结果
        :param little_map_sp_match_result: 小地图中特殊点的匹配结果
        :param show: 是否显示
        :return: 最佳结果
        """
        max_sp_count = 0
        target = None
        for r in match_result:
            sp_count = 0
            # 小地图中有特殊点 在大地图结果中需要全部找到
            if len(little_map_sp_match_result) > 0:
                large_map_match_part = large_map_usage[r.y:r.y+r.h, r.x:r.x+r.w, :]
                if show:
                    cv2_utils.show_image(large_map_match_part, win_name='large_map_match_part')
                for sp_template_id in little_map_sp_match_result.keys():
                    sp_in_large_map = self.im.match_template(large_map_match_part, sp_template_id,
                                                             threshold=constants.THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP,
                                                             ignore_template_alpha=True,
                                                             ignore_inf=True)
                    if len(sp_in_large_map) > 0:
                        sp_count += 1

            if target is None\
                    or sp_count > max_sp_count \
                    or (sp_count == max_sp_count and r.confidence > target.confidence):
                target = r
                max_sp_count = sp_count

        return target