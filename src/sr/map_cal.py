import cv2
import numpy as np
from PIL.Image import Image

from basic.img import ImageMatcher, MatchResult, cv2_utils
from basic.log_utils import log
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

    def __init__(self, screen_width: int = 1920, screen_height: int = 1080, config: ConfigHolder = None):
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

    def cut_little_map(self, screen: cv2.typing.MatLike, no_center: bool = False):
        """
        从整个游戏窗口截图中 裁剪出小地图部分
        :param screen: 屏幕截图
        :param no_center: 是否将中心含箭头部分裁掉
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

        if no_center:
            y, x = lm.shape[:2]
            lm = cv2_utils.mark_area_as_transparent(lm, [(x // 2) - 20, (y // 2) - 20, 40, 40])

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

    def cut_little_map_arrow(self, screen: cv2.typing.MatLike):
        """
        从整个游戏窗口截图中 裁剪出小地图里的方向箭头
        :param screen:
        :return:
        """
        arrow_len = 24  # 箭头图片的宽高
        if self.map_pos is not None:
            arrow = screen[self.map_pos.y - arrow_len:self.map_pos.y + arrow_len,
                 self.map_pos.x - arrow_len:self.map_pos.x + arrow_len]
        else:
            x, y = 130, 180  # 箭头默认坐标
            x2, y2 = 170, 220
            arrow = screen[y:y2, x:x2]
        return arrow

    def get_direction_by_screenshot(self, screen: cv2.typing.MatLike, matcher: ImageMatcher, threshold: float = 0.5,
                                    show_match_result: bool = False) -> int:
        """
        在整个游戏窗口的截图中，找到小地图部分，通过匹配箭头判断当前方向。
        使用前需要先按一次w前进 确保人物方向与视角朝向一致
        :param screen: 全屏截图
        :param matcher: 图片匹配器
        :param threshold: 阈值
        :param show_match_result 显示匹配结果
        :return: 当前方向
        """
        little_map = self.cut_little_map_arrow(screen)
        angle_result = matcher.match_template_with_rotation(little_map, 'loc_arrow', threshold)
        target: MatchResult = None
        angle: int = None
        for k, v in angle_result.items():
            for r in v:
                if target is None or r.confidence > target.confidence:
                    target = r
                    angle = k

        log.debug('当前小地图匹配方向 %d 置信度 %.2f' % (angle, target.confidence) if angle is not None else '当前小地图未匹配到方向')
        if show_match_result:
            cv2_utils.show_image(little_map, target)

        return angle

    def cal_character_pos(self, screen: cv2.typing.MatLike, large_map: cv2.typing.MatLike, show: bool = False):
        """
        根据截图里的小地图 匹配大地图 判断当前的坐标
        :param screen: 屏幕截图
        :param large_map: 大地图图片
        :param show: 是否显示中间结果
        :return:
        """
        little_map = self.cut_little_map(screen)

        source = cv2.cvtColor(large_map, cv2.COLOR_BGR2GRAY)
        template = cv2.cvtColor(little_map, cv2.COLOR_BGR2GRAY)
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
            cv2_utils.show_image(result, win_name='小地图匹配大地图')
            cv2_utils.show_overlap(source, template, offset_x, offset_y, template_scale=scale, win_name='小地图覆盖大地图')

        return center_x, center_y
