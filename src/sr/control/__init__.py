from typing import Union, Optional

from cv2.typing import MatLike

from basic import cal_utils, Point, Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.image.ocr_matcher import OcrMatcher


class GameController:

    MOVE_INTERACT_TYPE = 0
    TALK_INTERACT_TYPE = 1

    def __init__(self, ocr: OcrMatcher):
        self.ocr: OcrMatcher = ocr
        self.turn_dx: float = None
        self.run_speed: float = None
        self.walk_speed: float = None
        self.is_moving: bool = False

    def init(self):
        pass

    def esc(self) -> bool:
        return False

    def open_map(self) -> bool:
        pass

    def click_ocr(self, screen: MatLike, word: str, threshold: float = 0.5, rect: Rect = None, click_offset: Optional[Point] = None,
                  press_time: float = 0, same_word: bool = False, ignore_case: bool = True, lcs_percent: float = -1,
                  merge_line_distance: float = -1
                  ) -> bool:
        """
        在屏幕中点击关键词所在位置 多个关键词时点击公共子串最长的一个
        :param screen: 屏幕截图
        :param word: 关键词
        :param threshold: 阈值
        :param rect: 圈定区域 (x,y,w,h) 默认分辨率下的游戏窗口里的坐标
        :param click_offset: 在匹配结果后 偏移多少进行点击
        :param press_time: 持续按的时间
        :param same_word: 要求整个词一样
        :param ignore_case: 忽略大小写
        :param lcs_percent: 最长公共子序列长度百分比 -1代表不使用
        :param merge_line_distance: 多少行距内合并OCR结果 -1为不合并
        :return:
        """
        part, _ = cv2_utils.crop_image(screen, rect)
        km = self.ocr.match_words(part,
                                  words=[word], threshold=threshold, same_word=same_word,
                                  ignore_case=ignore_case, lcs_percent=lcs_percent,
                                  merge_line_distance=merge_line_distance)
        if len(km) == 0:
            return False

        target_point = None
        target_lcs_percent = None

        target_word = gt(word, 'ocr')
        for ocr_str, match_result_list in km.items():
            lcs = str_utils.longest_common_subsequence_length(target_word, ocr_str)
            lcs_percent = lcs / len(target_word)

            if target_point is None or target_lcs_percent is None or lcs_percent > target_lcs_percent:
                target_point = match_result_list.max.center
                target_lcs_percent = lcs_percent

        if target_point is None:
            return False
        if rect is not None:
            target_point = target_point + rect.left_top
        if click_offset is not None:
            target_point = target_point + click_offset
        log.debug('OCR识别 %s 成功 准备点击 %s', gt(word, 'ui'), target_point)
        return self.click(target_point, press_time=press_time)

    def click(self, pos: Point = None, press_time: float = 0) -> bool:
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

    def scroll(self, down: int, pos: Point = None):
        """
        向下滚动
        :param down: 负数时为相上滚动
        :param pos: 滚动位置 默认分辨率下的游戏窗口里的坐标
        :return:
        """
        pass

    def drag_to(self, end: Point, start: Point = None, duration: float = 0.5):
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

    def start_moving_forward(self, run: bool = False):
        """
        开始往前走
        :param run: 是否启用疾跑
        :return:
        """
        pass

    def stop_moving_forward(self):
        """
        停止向前移动
        :return:
        """
        pass

    def move(self, direction: str, press_time: float = 0):
        """
        往固定方向移动
        :param direction: 方向 wsad
        :param press_time: 持续秒数
        :return:
        """
        pass

    def cal_move_distance_by_time(self, seconds: float, run: bool = False):
        """
        根据时间计算移动距离
        :param seconds: 秒
        :param run: 是否疾跑
        :return:
        """
        return (self.run_speed if run else self.walk_speed) * seconds

    def move_towards(self, pos1: Point, pos2: Point, angle: float, run: bool = False) -> bool:
        """
        朝目标点行走
        :param pos1: 起始点
        :param pos2: 目标点
        :param angle: 当前角度
        :param run: 是否疾跑
        :return:
        """
        if angle is None:
            log.error('当前角度为空 无法判断移动方向')
            return False
        target_angle = cal_utils.get_angle_by_pts(pos1, pos2)
        # 保证计算的转动角度为正
        delta_angle = target_angle - angle if target_angle >= angle else target_angle + 360 - angle
        # 正方向转太远的话就用负方向转
        if delta_angle > 180:
            delta_angle -= 360
        log.info('寻路中 当前点: %s 目标点: %s 当前角度: %.2f度 目标角度: %.2f度 转动朝向: %.2f度', pos1, pos2, angle, target_angle, delta_angle)

        self.turn_by_angle(delta_angle)
        self.start_moving_forward(run=run)
        return True

    def initiate_attack(self):
        """
        主动发起攻击
        :return:
        """
        pass

    def interact(self, pos: Point, interact_type: int = 0) -> bool:
        """
        交互
        :param pos: 如果是模拟器的话 需要传入交互内容的坐标
        :param interact_type: 交互类型
        :return:
        """
        pass

    def switch_character(self, idx: int):
        """
        切换角色
        :param idx: 第几位角色 从1开始
        :return:
        """
        pass

    def use_technique(self):
        """
        使用秘技
        :return:
        """
        pass

    def close_game(self):
        """
        关闭游戏
        :return:
        """
        pass
