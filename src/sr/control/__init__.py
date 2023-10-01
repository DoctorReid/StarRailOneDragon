from cv2.typing import MatLike

from basic.img import cv2_utils
from basic.log_utils import log
from sr.image import OcrMatcher


class GameController:

    def __init__(self):
        self.ocr: OcrMatcher = None
        self.turn_dx: float = None
        self.walk_speed: float = None
        self.is_moving: bool = False
        pass

    def init(self):
        pass

    def esc(self) -> bool:
        return False

    def open_map(self) -> bool:
        pass

    def click_ocr(self, screen: MatLike, word: str, threshold: float = 0.5, rect: tuple = None, click_offset: tuple = None,
                  press_time: int = 0,
                  ) -> bool:
        """
        在屏幕中点击关键词所在位置 多个关键词时随机点击一个
        :param screen: 屏幕截图
        :param word: 关键词
        :param threshold: 阈值
        :param rect: 圈定区域 (x,y,w,h) 默认分辨率下的游戏窗口里的坐标
        :param click_offset: 在匹配结果后 偏移多少进行点击
        :param press_time: 持续按的时间
        :return:
        """
        if rect is not None:
            x1, y1, x2, y2 = rect
            # cv2_utils.show_image(screen[y1:y2, x1:x2], win_name='ocr_part')
        km = self.ocr.match_words(screen if rect is None else screen[y1:y2, x1:x2], words=[word], threshold=threshold)
        if len(km) == 0:
            return False
        for v in km.values():
            x, y = v.max.cx, v.max.cy
            if rect is not None:
                x += rect[0]
                y += rect[1]
            if click_offset is not None:
                x += click_offset[0]
                y += click_offset[1]
            log.debug('OCR识别 %s 成功 准备点击 (%d, %d)', word, x, y)
            return self.click((x, y), press_time=press_time)

    def click(self, pos: tuple = None, press_time: int = 0) -> bool:
        """
        点击位置
        :param pos: 点击位置 (x,y) 默认分辨率下的游戏窗口里的坐标
        :param press_time: 大于0时长按若干秒
        :return: 不在窗口区域时不点击 返回False
        """
        pass

    def screenshot(self) -> MatLike:
        """
        截图 如果分辨率和默认不一样则进行缩放
        :return: 缩放到默认分辨率的截图
        """
        pass

    def scroll(self, down: int, pos: tuple = None):
        """
        向下滚动
        :param down: 负数时为相上滚动
        :param pos: 滚动位置 默认分辨率下的游戏窗口里的坐标
        :return:
        """
        pass

    def drag_to(self, end: tuple, start: tuple = None, duration: float = 0.5):
        """
        按住拖拽
        :param end: 拖拽目的点
        :param start: 拖拽开始点
        :param duration: 拖拽持续时间
        :return:
        """
        pass

    def turn_by_distance(self, d: float):
        """
        横向转向 按距离转
        :param d: 正数往右转 人物角度增加；负数往左转 人物角度减少
        :return:
        """
        pass

    def turn_by_angle(self, angle: float):
        self.turn_by_distance(self.turn_dx * angle)

    def start_moving_forward(self):
        """
        开始往前走
        :return:
        """
        pass

    def stop_moving_forward(self):
        """
        停止向前移动
        :return:
        """
        pass

    def move(self, direction: str, press_time: int = 0):
        """
        往固定方向移动
        :param direction: 方向 wsad
        :param press_time: 持续秒数
        :return:
        """
        pass

    def cal_move_distance_by_time(self, seconds: float):
        """
        根据时间计算移动距离
        :param seconds:
        :return:
        """
        return self.walk_speed * seconds

    def move_towards(self, pos1: tuple, pos2: tuple, angle: float):
        """
        朝目标点行走
        :param pos1: 起始点
        :param pos2: 目标点
        :param angle: 当前角度
        :return:
        """
        target_angle = cv2_utils.get_angle_by_pts(pos1, pos2)
        # 保证计算的转动角度为正
        delta_angle = target_angle - angle if target_angle >= angle else target_angle + 360 - angle
        # 正方向转太远的话就用负方向转
        if delta_angle > 180:
            delta_angle -= 360
        log.info('寻路中 当前点: %s 目标点: %s 当前角度: %.2f度 目标角度: %.2f度 转动朝向: %.2f度', pos1, pos2, angle, target_angle, delta_angle)

        self.turn_by_angle(delta_angle)
        self.start_moving_forward()

    def initiate_attack(self):
        """
        主动发起攻击
        :return:
        """
        pass