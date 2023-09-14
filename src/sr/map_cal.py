import cv2
import numpy as np
from PIL.Image import Image

from basic.img import ImageMatcher, MatchResult, cv2_utils
from basic.log_utils import log


class LittleMapPos:

    def __init__(self, x, y, r):
        # 原点
        self.x = x
        self.y = y
        self.r = r
        # 矩形左上角
        self.lx = x - r
        self.ly = y - r
        # 矩形右下角
        self.rx = x + r
        self.ry = y + r

    def __str__(self):
        return "(%d, %d) %.2f" % (self.x, self.y, self.r)


class MapCalculator:

    def __init__(self, screen_width: int = 1920, screen_height: int = 1080):
        self.x_scale = screen_width / 1920
        self.y_scale = screen_height / 1080
        self.scale: bool = self.x_scale != 1 or self.y_scale != 1
        self.map_pos: LittleMapPos = None

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
        :param screen:
        :return:
        """
        if self.map_pos is not None:
            lm = screen[self.map_pos.ly:self.map_pos.ry, self.map_pos.lx:self.map_pos.rx]
            # 创建一个与图像大小相同的掩码图像，其中圆圈内的区域为白色（255），圆圈外的区域为黑色（0）
            mask = np.zeros(lm.shape[:2], dtype=np.uint8)
            center = (lm.shape[1] // 2, lm.shape[0] // 2)
            radius = self.map_pos.r - 1
            color = (255, 255, 255)  # 白色
            thickness = -1  # 填充内部区域
            cv2.circle(mask, center, radius, color, thickness)
            # 使用掩码图像将原始图像的透明通道中的像素值设置为0，从而将圆圈外的区域变为透明
            lm = cv2.bitwise_and(lm, lm, mask=mask)
        else:
            x, y = 60, 110  # 默认的小地图坐标
            x2, y2 = 240, 280
            lm = screen[y:y2, x:x2]
        return lm

    def cal_little_map_pos(self, screen: cv2.typing.MatLike):
        """
        计算小地图的坐标
        通过截取屏幕左上方部分 找出最大的圆圈 就是小地图
        :param screen: 屏幕截图
        """
        # 左上角部分
        x, y = 0, 0
        x2, y2 = 340, 380
        image = screen[y:y2, x:x2]

        # 对图像进行预处理
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1.2, 100)

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

    def get_direction_by_screenshot(self, screen: Image, matcher: ImageMatcher, threshold: float = 0.5,
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
