import random
import time
from typing import ClassVar

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import str_utils, Point, Rect
from basic.i18_utils import gt
from basic.img import MatchResultList, MatchResult, cv2_utils
from basic.log_utils import log
from sr import const
from sr.config import game_config
from sr.const import game_config_const
from sr.const.map_const import TransportPoint
from sr.context import Context
from sr.image.sceenshot import LargeMapInfo, large_map
from sr.operation import Operation


class ChooseTransportPoint(Operation):

    tp_name_rect: ClassVar[Rect] = Rect(1485, 120, 1870, 170)  # 右侧显示传送点名称的区域
    drag_distance: ClassVar[int] = -200

    def __init__(self, ctx: Context, tp: TransportPoint):
        super().__init__(ctx, 10, op_name=gt('选择传送点 %s') % tp.display_name)
        self.tp: TransportPoint = tp
        self.lm_info: LargeMapInfo = self.ctx.ih.get_large_map(self.tp.region)

    def _execute_one_round(self) -> int:
        screen = self.screenshot()

        # 判断地图中间是否有目标点中文可选
        if self.check_and_click_sp_cn(screen):
            time.sleep(1)
            return Operation.WAIT

        # 先判断右边是不是出现传送了
        if self.check_and_click_transport(screen):
            time.sleep(2)
            return Operation.SUCCESS

        # 目标点中文 不是传送 或者不是目标传送点 点击一下地图空白位置
        self.ctx.controller.click(large_map.EMPTY_MAP_POS)
        time.sleep(0.5)

        screen_map, _ = cv2_utils.crop_image(screen, large_map.CUT_MAP_RECT)
        # cv2_utils.show_image(screen_map, win_name='ChooseTransportPoint-screen_map')

        offset: MatchResult = self.get_map_offset(screen_map)
        if offset is None:
            log.error('匹配大地图失败')
            self.random_drag()
            time.sleep(0.5)
            return Operation.RETRY

        dx, dy = self.get_map_next_drag(offset)

        if dx == 0 and dy == 0:  # 当前就能找传送点
            target: MatchResult = self.get_tp_pos(screen_map, offset)
            if target is None:  # 没找到的话 按计算坐标点击
                to_click = self.tp.lm_pos - offset.left_top + large_map.CUT_MAP_RECT.left_top
                self.ctx.controller.click(to_click)
                time.sleep(0.5)
            else:
                to_click = target.center + large_map.CUT_MAP_RECT.left_top
                self.ctx.controller.click(to_click)
                time.sleep(0.5)

        if dx != 0 or dy != 0:
            self.drag(dx, dy)
            time.sleep(0.5)

        return Operation.RETRY

    def check_and_click_transport(self, screen: MatLike):
        """
        判断右侧是否出现传送 已经是否对应的传送点
        如果是 则点击
        :param screen: 屏幕截图
        :return: 是否点击传送
        """
        tp_btn_part, _ = cv2_utils.crop_image(screen, large_map.TP_BTN_RECT)
        # cv2_utils.show_image(tp_btn_part, win_name='tp_btn_part')
        tp_btn_ocr = self.ctx.ocr.match_words(tp_btn_part, ['传送'])
        if len(tp_btn_ocr) > 0:
            # 看看是否目标传送点
            tp_name_part, _ = cv2_utils.crop_image(screen, ChooseTransportPoint.tp_name_rect)
            lower_color = np.array([55, 55, 55], dtype=np.uint8)
            upper_color = np.array([255, 255, 255], dtype=np.uint8)
            gold_part = cv2.inRange(tp_name_part, lower_color, upper_color)
            current_lang: str = self.ctx.game_config.lang
            if current_lang == game_config_const.LANG_CN:
                gold_part = cv2_utils.dilate(gold_part, 1)
            tp_name_str: str = None
            if current_lang == game_config_const.LANG_CN:
                tp_name_str = self.ctx.ocr.ocr_for_single_line(gold_part)
            elif current_lang == game_config_const.LANG_EN:
                ocr_result: dict = self.ctx.ocr.run_ocr(gold_part)
                tp_name_str = None
                for k in ocr_result.keys():
                    if tp_name_str is None:
                        tp_name_str = k
                    else:
                        tp_name_str += ' ' + k

            log.info('当前选择传送点名称 %s', tp_name_str)
            # cv2_utils.show_image(gold_part, win_name='gold_part')
            if (tp_name_str is not None and
                    str_utils.find_by_lcs(gt(self.tp.cn, 'ocr'), tp_name_str, ignore_case=True, percent=self.gc.special_point_lcs_percent)):
                # 点击传送
                to_click = large_map.TP_BTN_RECT.left_top
                for r in tp_btn_ocr.values():
                    to_click = to_click + r.max.center
                    break
                return self.ctx.controller.click(to_click)
        return False

    def get_map_offset(self, screen_map: MatLike) -> MatchResult:
        """
        在完整大地图中获取当前界面地图的偏移量
        :param screen_map: 屏幕上的地图部分
        :return: 匹配结果 里面就有偏移量
        """
        result: MatchResultList = self.ctx.im.match_image(self.lm_info.origin, screen_map)
        return result.max

    def get_map_next_drag(self, offset: MatchResult):
        """
        判断当前地图是否已经涵盖到目标点
        如果没有 则返回需要往哪个方向拖动
        :param offset: 偏移量
        :return: 后续拖动方向 正代表坐标需要增加 正代表坐标需要减少
        """
        # 匹配结果矩形
        x1, y1 = offset.x, offset.y
        x2, y2 = x1 + offset.w, y1 + offset.h
        # 目标点坐标
        x, y = self.tp.lm_pos.x, self.tp.lm_pos.y

        dx, dy = 0, 0
        if x > x2:
            dx = 1
        elif x < x1:
            dx = -1
        if y > y2:
            dy = 1
        elif y < y1:
            dy = -1
        return dx, dy

    def get_tp_pos(self, screen_map: MatLike, offset: MatchResult):
        """
        在当前屏幕地图上匹配传送点 在传送点位置
        :param screen_map: 屏幕上的地图部分
        :param offset: 屏幕上的地图在完整大地图上的偏移量
        :return:
        """
        if self.tp.lm_pos is not None:
            sm_offset_x = self.tp.lm_pos.x - offset.x
            sm_offset_y = self.tp.lm_pos.y - offset.y
            sp_rect = Rect(sm_offset_x - 100, sm_offset_y - 100, sm_offset_x + 100, sm_offset_y + 100)
            crop_screen_map, sp_rect = cv2_utils.crop_image(screen_map, sp_rect)
            result: MatchResultList = self.ctx.im.match_template(crop_screen_map, self.tp.template_id, threshold=const.THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP)

            if result.max is not None:
                return MatchResult(result.max.confidence,
                                   result.max.x + sp_rect.x1,
                                   result.max.y + sp_rect.y1,
                                   result.max.w,
                                   result.max.h
                                   )
            else:
                return None
        else:
            result: MatchResultList = self.ctx.im.match_template(screen_map, self.tp.template_id, threshold=const.THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP)
            return result.max

    def random_drag(self):
        dx = 1 if random.randint(0, 1) == 1 else -1
        dy = 1 if random.randint(0, 1) == 1 else -1
        self.drag(dx, dy)

    def drag(self, dx: int, dy: int):
        fx, fy = large_map.EMPTY_MAP_POS.tuple()
        tx, ty = fx + ChooseTransportPoint.drag_distance * dx, fy + ChooseTransportPoint.drag_distance * dy
        log.info('当前未找到传送点 即将拖动地图 %s -> %s', (fx, fy), (tx, ty))
        self.ctx.controller.drag_to(end=Point(tx, ty), start=Point(fx, fy), duration=1)

    def check_and_click_sp_cn(self, screen) -> bool:
        """
        判断地图中间是否有目标点中文可选 两个特殊点重叠的时候会出现
        发现的话进行点击
        :param screen: 屏幕截图
        :return:
        """
        screen_map, _ = cv2_utils.crop_image(screen, large_map.CUT_MAP_RECT)

        l = 190
        u = 255
        lower_color = np.array([l, l, l], dtype=np.uint8)
        upper_color = np.array([u, u, u], dtype=np.uint8)
        white_part = cv2.inRange(screen_map, lower_color, upper_color)  # 提取白色部分方便匹配

        # cv2_utils.show_image(white_part, win_name='check_and_click_sp_cn')
        ocr_result = self.ctx.ocr.match_words(white_part, words=[self.tp.cn],
                                              lcs_percent=self.gc.special_point_lcs_percent)

        for r in ocr_result.values():
            to_click = r.max.center + large_map.CUT_MAP_RECT.left_top
            return self.ctx.controller.click(to_click)

        return False
