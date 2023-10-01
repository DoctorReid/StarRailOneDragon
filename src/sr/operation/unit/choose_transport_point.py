import random
import time

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import MatchResultList, MatchResult, cv2_utils
from basic.log_utils import log
from sr import constants
from sr.constants.map import TransportPoint
from sr.context import Context
from sr.operation import Operation


class ChooseTransportPoint(Operation):

    map_rect = (200, 200, 1400, 900)  # 大地图界面裁剪地图区域 应该需要比 大地图录制的区域小一点
    tp_btn_rect = (1500, 800, 1800, 1000)  # 右侧显示传送按钮的区域
    tp_name_rect = (1480, 120, 1640, 170)  # 右侧显示传送点名称的区域
    empty_map_pos = (1350, 800)  # 地图空白区域 用于取消选择传送点 和 拖动地图
    drag_distance = -200

    def __init__(self, ctx: Context, tp: TransportPoint):
        super().__init__(ctx, 10)
        self.tp: TransportPoint = tp
        self.large_map = self.ctx.ih.get_large_map(self.tp.region, 'origin')

    def run(self) -> int:
        mx1, my1, mx2, my2 = ChooseTransportPoint.map_rect

        screen = self.ctx.controller.screenshot()

        # 先判断右边是不是出现传送了
        if self.check_and_click_transport(screen):
            time.sleep(2)
            return Operation.SUCCESS
        else:
            # 不是传送 或者不是目标传送点
            self.ctx.controller.click(ChooseTransportPoint.empty_map_pos)
            time.sleep(0.5)

        screen_map = screen[my1: my2, mx1: mx2]
        offset: MatchResult = self.get_map_offset(screen_map)
        if offset is None:
            log.error('匹配大地图失败')
            self.random_drag()
            time.sleep(0.5)
            return Operation.RETRY

        dx, dy = self.get_map_next_drag(offset)

        if dx == 0 and dy == 0:  # 当前就能找传送点
            target: MatchResult = self.get_tp_pos(screen_map, offset)
            if target is None:  # 没找到的话 随机滑动一下
                self.random_drag()
            else:
                x = target.cx + mx1
                y = target.cy + my1
                self.ctx.controller.click((x, y))

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
        tp_btn_part = cv2_utils.crop_image(screen, ChooseTransportPoint.tp_btn_rect)
        cv2_utils.show_image(tp_btn_part, win_name='tp_btn_part')
        tp_btn_ocr = self.ctx.ocr.match_words(tp_btn_part, [gt('传送')], threshold=0.4)
        if len(tp_btn_ocr) > 0:
            # 看看是否目标传送点
            tp_name_part = cv2_utils.crop_image(screen, ChooseTransportPoint.tp_name_rect)
            tp_name_ocr = self.ctx.ocr.match_words(tp_name_part, [gt(self.tp.cn)], threshold=0.4)
            cv2_utils.show_image(tp_name_part, win_name='tp_name_part')
            if len(tp_name_ocr) > 0:
                # 点击传送
                tx = ChooseTransportPoint.tp_btn_rect[0]
                ty = ChooseTransportPoint.tp_btn_rect[1]
                for r in tp_btn_ocr.values():
                    tx += r.max.cx
                    ty += r.max.cy
                    break
                return self.ctx.controller.click((tx, ty))
        return False


    def get_map_offset(self, screen_map: MatLike) -> MatchResult:
        """
        在完整大地图中获取当前界面地图的偏移量
        :param screen_map: 屏幕上的地图部分
        :return: 匹配结果 里面就有偏移量
        """
        result: MatchResultList = self.ctx.im.match_image(self.large_map, screen_map)
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
        x, y = self.tp.lm_pos

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
            sm_offset_x = self.tp.lm_pos[0] - offset.x
            sm_offset_y = self.tp.lm_pos[1] - offset.y
            crop_screen_map = cv2_utils.crop_image(screen_map, (sm_offset_x - 100, sm_offset_y - 100, sm_offset_x + 100, sm_offset_y + 100))
            result: MatchResultList = self.ctx.im.match_template(crop_screen_map, self.tp.template_id, threshold=constants.THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP)

            if result.max is not None:
                return MatchResult(result.max.confidence,
                                   result.max.x + sm_offset_x - 100,
                                   result.max.y + sm_offset_y - 100,
                                   result.max.w,
                                   result.max.h
                                   )
            else:
                return None
        else:
            result: MatchResultList = self.ctx.im.match_template(screen_map, self.tp.template_id, threshold=constants.THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP)
            return result.max

    def random_drag(self):
        dx = 1 if random.randint(0, 1) == 1 else -1
        dy = 1 if random.randint(0, 1) == 1 else -1
        self.drag(dx, dy)

    def drag(self, dx: int, dy: int):
        fx, fy = ChooseTransportPoint.empty_map_pos
        tx, ty = fx + ChooseTransportPoint.drag_distance * dx, fy + ChooseTransportPoint.drag_distance * dy
        log.info('当前未找到传送点 即将拖动地图 %s -> %s', (fx, fy), (tx, ty))
        self.ctx.controller.drag_to(end=(tx, ty), start=(fx, fy), duration=1)
