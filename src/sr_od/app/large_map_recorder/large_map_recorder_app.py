import time
from concurrent.futures import Future, ThreadPoolExecutor

import cv2
import numpy as np
import os
from collections import Counter

import pyautogui
from cv2.typing import MatLike
from typing import List, Optional, Any

from one_dragon.base.geometry.point import Point
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, cal_utils, os_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from sr_od.app.sim_uni.sim_uni_const import SimUniLevelTypeEnum
from sr_od.app.sr_application import SrApplication
from sr_od.config import game_const, operation_const
from sr_od.context.sr_context import SrContext
from sr_od.sr_map import large_map_utils
from sr_od.sr_map.operations.choose_floor import ChooseFloor
from sr_od.sr_map.operations.choose_planet import ChoosePlanet
from sr_od.sr_map.operations.choose_region import ChooseRegion
from sr_od.sr_map.operations.open_map import OpenMap
from sr_od.sr_map.sr_map_def import Region

_FLOOR_LIST = [-4, -3, -2, -1, 0, 1, 2, 3, 4]

_EXECUTOR = ThreadPoolExecutor(thread_name_prefix='sr_large_map_recorder', max_workers=32)

class OverlapResultWrapper:

    def __init__(self, region: Region,
                 future: Future[int],
                 row: Optional[int] = None,
                 col: Optional[int] = None
                 ):
        self.region: Region = region
        self.future: Future[int] = future
        self.row: int = row
        self.col: int = col


DRAG_NEXT_COL_START = Point(1350, 300)  # 大地图右方的空白区域 防止点击到地图的点 导致拖拽有问题



class LargeMapRecorder(SrApplication):
    """
    开发用的截图工具 只支持PC版 需要自己缩放大地图到最小比例
    把整个大地图记录下来
    """

    def __init__(self, ctx: SrContext, region: Region,
                 skip_height: Optional[int] = None,
                 max_row: Optional[int] = None,
                 max_column: Optional[int] = None,
                 drag_distance_to_next_col: int = 300,
                 drag_distance_to_next_row: int = 300,
                 drag_times_to_left_top: int = 3,
                 drag_times_to_left: int = 2,
                 floor_list_to_record: Optional[List[int]] = None,
                 row_list_to_record: Optional[List[int]] = None,
                 col_list_to_record: Optional[List[int]] = None,
                 rows_to_cal_overlap_width: List[int] = None,
                 cols_to_cal_overlap_height: List[int] = None,
                 overlap_width_mode: list[int] = None,
                 overlap_height_mode: list[int] = None,
                 fix_width_rows: list[int] = None,
                 debug: bool = False,
                 ):
        SrApplication.__init__(self, ctx, 'large_map_recorder', op_name='大地图录制 %s' % region.cn)

        self.debug: bool = debug  # 调试模式 会显示很多图片
        self.row_start_idx: int = 1  # 行坐标开始值s
        self.col_start_idx: int = 1  # 列坐标开始值

        self.region: Region = region
        self.row: int = 1  # 下标从1开始
        self.col: int = 1

        self.drag_distance_to_next_col: int = drag_distance_to_next_col
        self.drag_distance_to_next_row: int = drag_distance_to_next_row

        self.skip_height: Optional[int] = skip_height  # 部分地图上方较空 可以跳过部分高度不录制
        self.row_list_to_record: Optional[List[int]] = row_list_to_record  # 需要重新录制的行数
        self.col_list_to_record: Optional[List[int]] = col_list_to_record  # 需要重新录制的列数
        self.floor_list_to_record: Optional[List[int]] = floor_list_to_record  # 需要重新录制的楼层
        self.max_row: int = max_row  # 最多录制的行数 不传入时自动判断
        self.max_column: int = max_column  # 最多录制的列数 不传入时自动判断
        self.drag_times_to_left: int = drag_times_to_left  # 切换行时 拖到到最左边的次数
        self.drag_times_to_left_top: int = drag_times_to_left_top  # 切换楼层时 拖动到左上角次数

        self.region_list: List[Region] = []
        for floor in _FLOOR_LIST:
            if self.floor_list_to_record is not None and floor not in self.floor_list_to_record:
                continue
            current_region = self.ctx.map_data.best_match_region_by_name(
                gt(self.region.cn),
                planet=self.region.planet,
                target_floor=floor
            )
            if current_region is None:
                continue
            if current_region.pr_id != self.region.pr_id:
                continue
            self.region_list.append(current_region)

        self.current_region_idx: int = 0
        self.current_region: Optional[Region] = None

        self.overlap_width_mode: List[int] = overlap_width_mode  # 截图重叠的宽度
        self.overlap_height_mode: List[int] = overlap_height_mode  # 截图重叠的高度
        self.fix_width_rows: list[int] = fix_width_rows  # 固定使用重叠众数宽度的行

        self.rows_to_cal_overlap_width: List[int] = rows_to_cal_overlap_width  # 计算每列的重叠宽度时 只考虑哪些行
        self.cols_to_cal_overlap_height: List[int] = cols_to_cal_overlap_height  # 计算每行的重叠高度时 只考虑哪些列

    @operation_node(name='打开地图', is_start_node=True)
    def open_map(self) -> OperationRoundResult:
        op = OpenMap(self.ctx)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='打开地图')
    @operation_node(name='选择星球')
    def choose_planet(self) -> OperationRoundResult:
        op = ChoosePlanet(self.ctx, self.region.planet)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='选择星球')
    @operation_node(name='选择区域')
    def choose_region(self) -> OperationRoundResult:
        op = ChooseRegion(self.ctx, self.region)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='选择区域')
    @operation_node(name='识别最大行列数')
    def detect_max_row_col(self) -> OperationRoundResult:
        if self.max_column is None:
            self.back_to_left_top()
            self.drag_to_get_max_column()

        if self.max_row is None:
            self.back_to_left_top()
            self.drag_to_get_max_row()

        return self.round_success()

    @node_from(from_name='识别最大行列数')
    @operation_node(name='截图')
    def do_screenshot(self) -> OperationRoundResult:
        if self.current_region_idx >= len(self.region_list):
            return self.round_success()

        self.current_region = self.region_list[self.current_region_idx]

        op = ChooseFloor(self.ctx, self.current_region.floor)
        op_result = op.execute()
        if not op_result.success:
            return self.round_fail('选择区域失败')

        self._do_screenshot_1()
        if self.row_list_to_record is not None:
            while True:
                img = LargeMapRecorder.get_part_image(self.current_region, self.row, 0)
                if img is None:
                    break
                else:
                    self.row += 1
            while True:
                img = LargeMapRecorder.get_part_image(self.current_region, 0, self.col)
                if img is None:
                    break
                else:
                    self.col += 1

        self.current_region_idx += 1
        return self.round_wait()

    def _do_screenshot_1(self):
        """
        先拉到最左上角 然后一行一行地截图 最后再拼接起来。
        多层数的话需要一次性先将所有楼层截图再处理 保证各楼层大小一致
        :return:
        """
        self.back_to_left_top()
        while True:
            if not self.ctx.is_context_running:
                return False
            if self.row_list_to_record is not None and self.row > np.max(self.row_list_to_record):
                break
            if self.row_list_to_record is not None and self.row not in self.row_list_to_record:
                self.drag_to_next_row()
                continue

            self.screenshot_horizontally()  # 对一行进行水平的截图

            to_next_row: bool = False
            if self.max_row is not None:  # 如果有设定需要多少行 就按照设定行数进行截图
                if self.row < self.max_row:
                    to_next_row = True
            else:
                # 没有设定行数时 通过和上一行进行对比 判断是否到达底部
                if not LargeMapRecorder.same_as_last_row(self.current_region, self.row, self.col):
                    to_next_row = True

            if to_next_row:
                self.drag_to_next_row()
                self.back_to_left()
            else:
                break

    def screenshot_horizontally(self):
        """
        水平滚动地截取地图部分 并落盘保存
        :return: 拼接好的图片
        """
        img = []
        # 每秒往右拉一段距离截图
        while True:
            if not self.ctx.is_context_running:
                return
            log.info('当前截图 %02d行 %02d列' % (self.row, self.col))
            screen = self.screenshot()
            screen_map_rect = large_map_utils.get_screen_map_rect(self.region)
            map_part = cv2_utils.crop_image_only(screen, screen_map_rect)
            if self.col_list_to_record is None or self.col in self.col_list_to_record:
                LargeMapRecorder.save_part_image(self.current_region, self.row, self.col, map_part)
            img.append(map_part)

            to_next_col: bool = False
            if self.max_column is not None:  # 如果有设定需要多少列 就按照设定列数进行截图
                if self.col < self.max_column:
                    to_next_col = True
            else:
                if len(img) == 0 or not cv2_utils.is_same_image(img[len(img) - 1], map_part):
                    to_next_col = True

            if to_next_col:
                self.drag_to_next_col()
            else:
                if self.max_column is None:  # 没有设定多少列 最后一列会是重复的 丢弃
                    img.pop()
                break

    @node_from(from_name='截图')
    @operation_node(name='合并')
    def merge_screenshot(self) -> OperationRoundResult:
        row = self.row if self.max_row is None else self.max_row
        col = self.col if self.max_column is None else self.max_column

        if self.overlap_width_mode is None:
            self.overlap_width_mode = self.get_overlap_width_mode()
        for region in self.region_list:
            self.merge_screenshot_into_rows(region, row, col, show=self.debug)

        if self.overlap_height_mode is None:
            self.overlap_height_mode = self.get_overlap_height_mode()
        for region in self.region_list:
            self.merge_screenshot_into_one(region, row, show=self.debug)

        return self.round_success()

    @node_from(from_name='合并')
    @operation_node(name='保存')
    def do_save(self) -> OperationRoundResult:
        # 部分地图边缘较窄 与小地图做模板匹配会有问题 因此做一个边缘拓展
        lp, rp, tp, bp = None, None, None, None
        for region in self.region_list:
            # 不同楼层需要拓展的大小可能不一致 保留一个最大的
            screen_map_rect = large_map_utils.get_screen_map_rect(region)
            raw = self.ctx.map_data.get_large_map_image(region, 'raw')
            lp2, rp2, tp2, bp2 = large_map_utils.get_expand_arr(raw, self.ctx.game_config.mini_map_pos, screen_map_rect)
            if lp is None or lp2 > lp:
                lp = lp2
            if rp is None or rp2 > rp:
                rp = rp2
            if tp is None or tp2 > tp:
                tp = tp2
            if bp is None or bp2 > bp:
                bp = bp2

        # cv2.waitKey(0)

        for region in self.region_list:
            raw = self.ctx.map_data.get_large_map_image(region, 'raw')
            large_map_utils.init_large_map(self.ctx, region, raw,
                                           expand_arr=[lp, rp, tp, bp], save=True)

        return self.round_success()

    def back_to_left_top(self):
        """
        回到左上角
        """
        center = game_const.STANDARD_CENTER_POS
        rt = center + center + Point(-10, -10)
        for _ in range(self.drag_times_to_left_top):
            if not self.ctx.is_context_running:
                break
            self.ctx.controller.drag_to(end=rt, start=center, duration=0.2)  # 先拉到左上角
            time.sleep(1.5)
        self.col = 1
        self.row = 1

        if self.skip_height is not None:
            drag_from = Point(1350, 800)  # 大地图右方的空白区域 防止点击到地图的点 导致拖拽有问题
            skip_height = 0
            while skip_height < self.skip_height:
                to_skip = self.skip_height if self.skip_height <= 700 else 700
                skip_height += to_skip
                drag_to = drag_from + Point(0, -to_skip)
                self.ctx.controller.drag_to(end=drag_to, start=drag_from, duration=1)
                time.sleep(1.5)

    def back_to_top(self):
        """
        回到正上方
        """
        center = game_const.STANDARD_CENTER_POS
        bottom = Point(center.x, center.y + center.y - 10)
        for _ in range(6):
            if not self.ctx.is_context_running:
                break
            self.ctx.controller.drag_to(end=bottom, start=center, duration=1)  # 往上拉到尽头
            time.sleep(1.5)
        self.row = 1

    def back_to_left(self):
        """
        回到正左方
        """
        if self.max_column <= 1:
            return
        center = game_const.STANDARD_CENTER_POS
        right = Point(center.x + center.x - 10, center.y)
        for _ in range(self.drag_times_to_left):
            if not self.ctx.is_context_running:
                break
            self.ctx.controller.drag_to(end=right, start=center, duration=0.2)  # 往左拉到尽头
            time.sleep(1)
        self.col = 1

    def drag_to_next_row(self):
        """
        往下拖到下一行
        """
        center = Point(1350, 800)  # 大地图右方的空白区域 防止点击到地图的点 导致拖拽有问题
        top = center + Point(0, -self.drag_distance_to_next_row)
        self.special_drag_to(start=center, end=top)  # 往下拉一段
        time.sleep(1)
        self.row += 1

    def drag_to_next_col(self):
        """
        往右拖到下一列
        """
        start = DRAG_NEXT_COL_START  # 大地图右方的空白区域 防止点击到地图的点 导致拖拽有问题
        # center = game_const.STANDARD_CENTER_POS
        end = start + Point(-self.drag_distance_to_next_col, 0)
        self.special_drag_to(start=start, end=end)  # 往右拉一段
        time.sleep(1)
        self.col += 1

    @staticmethod
    def concat_vertically_by_list(img_list: List[MatLike], show: bool = False) -> MatLike:
        merge: MatLike = img_list[0]

        for i in range(1, len(img_list)):
            log.info('垂直合并 准备处理 %02d行', i)
            prev_img = img_list[i - 1]
            next_img = img_list[i]
            merge = LargeMapRecorder.concat_vertically(merge, prev_img, next_img, show=show)
        return merge

    @staticmethod
    def concat_vertically(merge: MatLike, img1: MatLike, img2: MatLike, decision_height: int = 150, show: bool = False):
        """
        垂直拼接图片。
        假设两张图片是通过垂直滚动得到的，即宽度一样，部分内容重叠
        :param merge: 合并前的图片
        :param img1: 上一张图
        :param img2: 下一张图
        :param decision_height: 用第一张图的最后多少高度来判断重叠部分
        :return:
        """
        overlap_h = LargeMapRecorder.get_overlap_height(img1, img2, decision_height=decision_height, show=show)
        extra_part = img2[overlap_h + 1:, :]
        # 垂直拼接两张图像
        return cv2.vconcat([merge, extra_part])

    @staticmethod
    def get_overlap_height(img1: MatLike, img2: MatLike, decision_height: int = 150, show: bool = False):
        """
        获取第二张图在第一图上的重叠高度
        """
        # empty_mask = cv2_utils.color_in_range(img1, [205, 205, 205], [215, 215, 215])
        # img1_mask = cv2.bitwise_not(empty_mask)
        # 截取一个横截面用来匹配 要用中心部分 四周空白较多容易误判
        for threshold in range(95, 70, -5):
            for dh in range(img2.shape[0] - decision_height, img2.shape[0] // 2, -10):
                prev_part = img1[-dh:, :]
                # prev_mask = img1_mask[-dh:, :]
                if show:
                    cv2_utils.show_image(prev_part, win_name='prev_part')
                    cv2_utils.show_image(img2, win_name='next_part')
                r = cv2_utils.match_template(img2, prev_part,
                                             # mask=prev_mask,
                                             threshold=threshold / 100.0).max
                if r is None:
                    continue
                return r.y + prev_part.shape[0]

        return -1

    @staticmethod
    def concat_horizontally_by_list(img_list: List[MatLike], show: bool = False) -> MatLike:
        merge: MatLike = img_list[0]
        for i in range(1, len(img_list)):
            log.info('处理 %02d', i)
            prev_img = img_list[i - 1]
            next_img = img_list[i]
            merge = LargeMapRecorder.concat_horizontally(merge, prev_img, next_img, show=show)
        return merge

    @staticmethod
    def concat_horizontally(whole: MatLike, img1: MatLike, img2: MatLike, decision_width: int = 150, show: bool = False):
        """
        水平拼接图片。
        假设两张图片是通过水平滚动得到的，即高度一样，部分内容重叠
        :param img1: 上一张图
        :param img2: 下一张图
        :param decision_width: 用第一张图的多少宽度来判断重叠部分
        :return:
        """
        overlap_w = LargeMapRecorder.get_overlap_width(img1, img2, decision_width=decision_width, show=show)
        extra_part = img2[:, overlap_w + 1:]
        # 水平拼接两张图像
        return cv2.hconcat([whole, extra_part])

    @staticmethod
    def get_overlap_width(img1: MatLike, img2: MatLike, decision_width: int = 200, show: bool = False):
        """
        获取第二张图在第一图上的重叠宽度
        """
        for threshold in range(95, 70, -5):
            for dw in range(img2.shape[1] - decision_width, img2.shape[1] // 2, -10):
                prev_part = img1[:, -dw:]
                # prev_mask = img1_mask[:, -dw:]
                if show:
                    cv2_utils.show_image(img1, win_name='prev_whole')
                    cv2_utils.show_image(prev_part, win_name='prev_part')
                    # cv2_utils.show_image(prev_mask, win_name='prev_mask')
                    cv2_utils.show_image(img2, win_name='next_part')
                r = cv2_utils.match_template(img2, prev_part,
                                             # mask=prev_mask,
                                             threshold=threshold / 100.0).max
                if r is None:
                    continue
                return r.x + prev_part.shape[1]
        return -1

    def get_overlap_width_mode(self) -> List[int]:
        """
        根据截图 计算各列重叠的宽度
        """
        max_row = self.row if self.max_row is None else self.max_row
        max_col = self.col if self.max_column is None else self.max_column

        overlap_width_list: List[List[int]] = []
        for i in range(max_col + 1):
            overlap_width_list.append([-1, -1])

        result_list: List[OverlapResultWrapper] = []

        # 先求出每列的重叠宽度
        for region in self.region_list:
            for row in range(1, max_row + 1):
                if self.rows_to_cal_overlap_width is not None and row not in self.rows_to_cal_overlap_width:
                    continue
                cur_col_img = None
                for col in range(1, max_col + 1):
                    last_col_img = cur_col_img
                    cur_col_img = LargeMapRecorder.get_part_image(region, row, col)

                    if last_col_img is not None:
                        f = _EXECUTOR.submit(LargeMapRecorder.get_overlap_width, last_col_img, cur_col_img, 200, False)
                        result_list.append(
                            OverlapResultWrapper(
                                region=region,
                                row=row,
                                col=col,
                                future=f
                            )
                        )

        for result in result_list:
            region = result.region
            row = result.row
            col = result.col
            cur_col_img = LargeMapRecorder.get_part_image(region, row, col)
            overlap_width = result.future.result()
            log.info('%d层 %02d行 %02d列 与前重叠宽度 %d', region.floor, row, col, overlap_width)
            if overlap_width == -1:
                log.info('获取失败 忽略')
                continue
            if overlap_width == cur_col_img.shape[1]:
                # 大概率是空白图 所以才和前一张完全一致 这种情况下忽略
                log.info('与图片宽度一致 忽略')
                continue

            overlap_width_list[col].append(overlap_width)

        overlap_width_mode: List[int] = [0, 0]
        if self.max_column is not None:
            # 如果已经指定了最大列数 则除了最后一列的其他列 与前一列的重叠宽度一致
            all_col_width = []
            if max_col >= 2:
                for col in range(2, max_col):
                    for width in overlap_width_list[col]:
                        all_col_width.append(width)
                all_col_width_mode = int(get_mode_in_list(all_col_width, ignored_set={-1}, empty_return=0))
                for col in range(2, max_col):
                    log.info('%02d列 与前重叠宽度众数 %d', col, all_col_width_mode)
                    overlap_width_mode.append(all_col_width_mode)
            for col in range(max_col, max_col + 1):
                width_mode = int(get_mode_in_list(overlap_width_list[col], ignored_set={-1}, empty_return=0))
                log.info('%02d列 与前重叠宽度众数 %d', col, width_mode)
                overlap_width_mode.append(width_mode)
        else:
            for col in range(2, max_col + 1):
                width_mode = int(get_mode_in_list(overlap_width_list[col], ignored_set={-1}, empty_return=0))
                log.info('%02d列 与前重叠宽度众数 %d', col, width_mode)
                overlap_width_mode.append(width_mode)

        log.info('重叠宽度众数 %s', overlap_width_mode)
        return overlap_width_mode

    def get_overlap_height_mode(self) -> List[int]:
        """
        根据截图 计算各行重叠的高度
        """
        max_row = self.row if self.max_row is None else self.max_row
        max_col = self.col if self.max_column is None else self.max_column

        overlap_height_list: List[List[int]] = []
        for i in range(max_row + 1):
            overlap_height_list.append([-1, -1])

        # 按格子 求出每行的重叠高度
        result_list: List[OverlapResultWrapper] = []
        for region in self.region_list:
            for col in range(1, max_col + 1):
                if self.cols_to_cal_overlap_height is not None and col not in self.cols_to_cal_overlap_height:
                    continue
                cur_row_img = None
                for row in range(1, max_row + 1):
                    last_row_img = cur_row_img
                    cur_row_img = LargeMapRecorder.get_part_image(region, row, col)

                    if last_row_img is not None:
                        f = _EXECUTOR.submit(LargeMapRecorder.get_overlap_height, last_row_img, cur_row_img, 150, False)
                        result_list.append(
                            OverlapResultWrapper(
                                region=region,
                                row=row,
                                col=col,
                                future=f
                            )
                        )

        for result in result_list:
            region = result.region
            row = result.row
            col = result.col
            cur_row_img = LargeMapRecorder.get_part_image(region, row, col)
            overlap_height = result.future.result()
            log.info('%d层 %02d行 %02d列 与前重叠高度 %d', region.floor, row, col, overlap_height)
            if overlap_height == -1:
                log.info('获取失败 忽略')
                continue
            if overlap_height == cur_row_img.shape[0]:
                # 大概率是空白图 所以才和前一张完全一致 这种情况下忽略
                log.info('与图片高度一致 忽略')
                continue

            overlap_height_list[row].append(overlap_height)

        # 按行 求出每行的重叠高度
        result_list: List[OverlapResultWrapper] = []
        for region in self.region_list:
            cur_row_img = None
            for row in range(1, max_row + 1):
                last_row_img = cur_row_img
                cur_row_img = LargeMapRecorder.get_row_image(region, row)

                if last_row_img is not None:
                    f = _EXECUTOR.submit(LargeMapRecorder.get_overlap_height, last_row_img, cur_row_img, 150, False)
                    result_list.append(
                        OverlapResultWrapper(
                            region=region,
                            row=row,
                            col=0,
                            future=f
                        )
                    )

        for result in result_list:
            region = result.region
            row = result.row
            cur_row_img = LargeMapRecorder.get_row_image(region, row)
            overlap_height = result.future.result()
            log.info('%d层 %02d行 与前重叠高度 %d', region.floor, row, overlap_height)
            if overlap_height == -1:
                log.info('获取失败 忽略')
                continue
            if overlap_height == cur_row_img.shape[0]:
                # 大概率是空白图 所以才和前一张完全一致 这种情况下忽略
                log.info('与图片高度一致 忽略')
                continue

            overlap_height_list[row].append(overlap_height)

        # 求众数
        overlap_height_mode: List[int] = [0, 0]
        if self.max_row is not None:
            # 如果已经指定了最大行数 则除了最后一行的其他行 与前一行的重叠高度一致
            all_row_height = []
            if max_row >= 2:
                for row in range(2, max_row):
                    for height in overlap_height_list[row]:
                        all_row_height.append(height)
                all_row_height_mode = int(get_mode_in_list(all_row_height, ignored_set={-1}, empty_return=0))
                for row in range(2, max_row):
                    log.info('%02d行 与前重叠高度众数 %d', row, all_row_height_mode)
                    overlap_height_mode.append(all_row_height_mode)
            for row in range(max_row, max_row + 1):
                height_mode = int(get_mode_in_list(overlap_height_list[row], ignored_set={-1}, empty_return=0))
                log.info('%02d行 与前重叠高度众数 %d', row, height_mode)
                overlap_height_mode.append(height_mode)
        else:
            for row in range(2, max_row + 1):
                height_mode = int(get_mode_in_list(overlap_height_list[row], ignored_set={-1}, empty_return=0))
                log.info('%02d行 与前重叠高度众数 %d', row, height_mode)
                overlap_height_mode.append(height_mode)

        log.info('重叠高度度众数 %s', overlap_height_mode)
        return overlap_height_mode

    def merge_screenshot_into_rows(self, region: Region, max_row: int, max_col: int, show=False):
        """
        将每行的截图进行合并
        """
        img_list: List[List[Optional[MatLike]]] = [[]]
        for row in range(1, max_row + 1):
            img_list.append([None])  # 每一行的第0列 都置为空
            for col in range(1, max_col + 1):
                img = LargeMapRecorder.get_part_image(region, row, col)
                img_list[row].append(img)

        # 根据重合宽度 先计算最终的宽度
        image_width: int = img_list[1][1].shape[1]  # 每张图片的宽度
        image_height: int = img_list[1][1].shape[0]  # 每张图片的高度
        total_width: int = image_width  # 最终的总宽度
        for col in range(2, max_col + 1):
            total_width += (image_width - self.overlap_width_mode[col])

        # 按重叠宽度的众数对每行图片进行合并
        row_image_list: List[MatLike] = []
        for row in range(1, max_row + 1):
            # 初始化一张完整的背景
            row_image: MatLike = np.full((image_height, total_width, 3),
                                              210,
                                              dtype=np.uint8)
            # 水平合并图片
            merge = img_list[row][1]
            for col in range(2, max_col + 1):
                if self.fix_width_rows is not None and row not in self.fix_width_rows:
                    overlap_w = self.get_overlap_width(img_list[row][col-1], img_list[row][col])
                else:
                    overlap_w = -1
                if overlap_w == -1:
                    overlap_w = self.overlap_width_mode[col]
                extra_part = img_list[row][col][:, overlap_w + 1:]
                # 水平拼接两张图像
                merge = cv2.hconcat([merge, extra_part])

            # 将合并后的图片赋值到背景上
            row_image[:, :merge.shape[1], :] = merge[:, :, :]

            log.info('%d层 %02d行 合并后size为 %s', region.floor, row, row_image.shape)
            LargeMapRecorder.save_row_image(region, row, row_image)
            row_image_list.append(row_image)
            if show:
                cv2_utils.show_image(row_image, win_name='row_%02d' % row)

    def merge_screenshot_into_one(self, region: Region, max_row: int, show=False):
        """
        合并成最终一张图片
        """
        row_image_list = [None]
        for row in range(1, max_row + 1):
            img = LargeMapRecorder.get_row_image(region, row)
            row_image_list.append(img)

        # 按重叠高度的众数对多行图片进行合并
        merge = row_image_list[1]
        LargeMapRecorder.save_merge_image(region, 1, merge)
        for i in range(2, max_row + 1):
            overlap_h = self.overlap_height_mode[i]
            row_image = row_image_list[i]
            extra_part = row_image[overlap_h + 1:, :]
            # 垂直拼接两张图像
            merge = cv2.vconcat([merge, extra_part])
            LargeMapRecorder.save_merge_image(region, i, merge)

        log.info('%d层 最终合并后size为 %s', region.floor, merge.shape)
        if show:
            cv2_utils.show_image(merge, win_name='final_merge', wait=0)
        LargeMapRecorder.save_floor_image(region, merge)

        self.ctx.map_data.save_large_map_image(merge, region, 'raw')

    @staticmethod
    def same_as_last_row(region: Region, row: int, max_col: int) -> bool:
        """
        是否跟前一行一样
        """
        if row <= 1:
            return False
        for col in range(max_col):
            prev_image = LargeMapRecorder.get_part_image(region, row - 1, col)
            next_image = LargeMapRecorder.get_part_image(region, row, col)
            if prev_image is None or next_image is None:
                return False
            if not cv2_utils.is_same_image(prev_image, next_image, threshold=10):
                return False
        return True

    def fix_all_after_map_record(self, region: Region, dx: int, dy: int):
        """
        大地图重新绘制后 修改对应的文件
        :param region: 区域
        :param dx: 新地图与旧地图的偏移量
        :param dy: 新地图与旧地图的偏移量
        :return:
        """
        self.fix_world_patrol_route_after_map_record(region, dx, dy)
        self.fix_sim_uni_route_after_map_record(region, dx, dy)

    def fix_world_patrol_route_after_map_record(self, region: Region, dx: int, dy: int):
        """
        大地图重新绘制后 修改对应的路线
        :param region: 区域
        :param dx: 新地图与旧地图的偏移量
        :param dy: 新地图与旧地图的偏移量
        :return:
        """

        to_fix_op = [
            operation_const.OP_MOVE,
            operation_const.OP_SLOW_MOVE,
            operation_const.OP_NO_POS_MOVE,
            operation_const.OP_UPDATE_POS
        ]

        for floor in _FLOOR_LIST:
            floor_region = self.ctx.map_data.best_match_region_by_name(
                gt(region.cn),
                planet=region.planet,
                target_floor=floor
            )
            if floor_region is None:
                continue

            all_route_list = self.ctx.world_patrol_route_data.load_all_route()

            for route in all_route_list:
                if route.tp.region != floor_region:
                    continue
                for route_item in route.route_list:
                    if route_item.op in to_fix_op:
                        route_item.data[0] += dx
                        route_item.data[1] += dy
                route.save()

    def fix_sim_uni_route_after_map_record(self, region: Region, dx: int, dy: int):
        """
        大地图重新绘制后 修改模拟宇宙对应的路线
        :param region: 区域
        :param dx: 新地图与旧地图的偏移量
        :param dy: 新地图与旧地图的偏移量
        :return:
        """

        to_fix_op = [
            operation_const.OP_MOVE,
            operation_const.OP_SLOW_MOVE,
            operation_const.OP_NO_POS_MOVE,
            operation_const.OP_UPDATE_POS
        ]

        for floor in _FLOOR_LIST:
            floor_region = self.ctx.map_data.best_match_region_by_name(
                gt(region.cn),
                planet=region.planet,
                target_floor=floor
            )
            if floor_region is None:
                continue

            for level_type_enum in SimUniLevelTypeEnum:
                level_type = level_type_enum.value
                if level_type.route_id != level_type.type_id:
                    continue
                route_list = self.ctx.sim_uni_route_data.get_route_list(level_type)
                for route in route_list:
                    if route.region != floor_region:
                        continue

                    if route.op_list is not None and len(route.op_list) > 0:
                        for route_item in route.op_list:
                            if route_item.op in to_fix_op:
                                route_item.data[0] += dx
                                route_item.data[1] += dy

                    if route.start_pos is not None:
                        route.start_pos += Point(dx, dy)
                    if route.reward_pos is not None:
                        route.reward_pos += Point(dx, dy)
                    if route.next_pos_list is not None and len(route.next_pos_list) > 0:
                        for pos in route.next_pos_list:
                            pos.x += dx
                            pos.y += dy
                    route.save()

    def drag_to_get_max_column(self) -> None:
        """
        在地图上找到一个图像多的位置
        在最左方开始 尝试往右滑动 看最多需要滑动多少次到底
        """
        self.col = 1
        last_map_part = None
        overlap_width: List[int] = [-1, -1]
        while True:
            if not self.ctx.is_context_running:
                break
            log.info(f'正在截图 列{self.col}')

            screen = self.screenshot()
            screen_map_rect = large_map_utils.get_screen_map_rect(self.region)
            map_part = cv2_utils.crop_image_only(screen, screen_map_rect)

            if last_map_part is not None:
                overlap_width.append(LargeMapRecorder.get_overlap_width(last_map_part, map_part))

                if cv2_utils.is_same_image(last_map_part, map_part, threshold=0.9):
                    log.info(f'已经到达最右端 列数为{self.col - 1}')
                    break

            last_map_part = map_part
            self.drag_to_next_col()

        log.info('重叠宽度 %s', overlap_width)
        self.max_column = self.col - 1
        self.col = 1

    def drag_to_get_max_row(self) -> None:
        """
        在地图上找到一个图像多的位置
        在最上方开始 尝试往下滑动 看最多需要滑动多少次到底
        """
        self.row = 1
        last_map_part = None
        overlap_height_list: List[int] = [-1, -1]
        while True:
            if not self.ctx.is_context_running:
                break
            log.info(f'正在截图 行{self.row}')

            screen = self.screenshot()
            screen_map_rect = large_map_utils.get_screen_map_rect(self.region)
            map_part = cv2_utils.crop_image_only(screen, screen_map_rect)

            if last_map_part is not None:
                overlap_height_list.append(LargeMapRecorder.get_overlap_height(last_map_part, map_part))
                if cv2_utils.is_same_image(last_map_part, map_part, threshold=0.9):
                    log.info(f'已经到达最下端 行数为{self.row - 1}')
                    break

            last_map_part = map_part
            self.drag_to_next_row()

        log.info('重叠高度 %s', overlap_height_list)
        self.max_row = self.row - 1
        self.row = 1

    @staticmethod
    def get_part_image_path(region: Region, row: int, col: int) -> str:
        """
        地图格子的图片路径
        """
        return os.path.join(
            os_utils.get_path_under_work_dir('.debug', 'world_patrol', region.pr_id, 'part'),
            f'{region.pr_id}_part_{region.l_str}_{row:02d}_{col:02d}.png'
        )

    @staticmethod
    def get_part_image(region: Region, row: int, col: int) -> MatLike:
        """
        地图格子的图片
        """
        return cv2_utils.read_image(LargeMapRecorder.get_part_image_path(region, row, col))

    @staticmethod
    def save_part_image(region: Region, row: int, col: int, image: MatLike) -> None:
        """
        地图格子的图片
        """
        path = LargeMapRecorder.get_part_image_path(region, row, col)
        cv2_utils.save_image(image, path)

    @staticmethod
    def get_row_image_path(region: Region, row: int) -> str:
        """
        地图某一行的图片路径
        """
        return os.path.join(
            os_utils.get_path_under_work_dir('.debug', 'world_patrol', region.pr_id, 'row'),
            f'{region.pr_id}_row_{region.l_str}_{row:02d}.png'
        )

    @staticmethod
    def get_row_image(region: Region, row: int) -> MatLike:
        """
        地图某一行的图片
        """
        return cv2_utils.read_image(LargeMapRecorder.get_row_image_path(region, row))

    @staticmethod
    def save_row_image(region: Region, row: int, image: MatLike) -> None:
        """
        地图某一行的图片
        """
        path = LargeMapRecorder.get_row_image_path(region, row)
        cv2_utils.save_image(image, path)

    @staticmethod
    def get_merge_image_path(region: Region, row: int) -> str:
        """
        地图格子的图片路径
        """
        return os.path.join(
            os_utils.get_path_under_work_dir('.debug', 'world_patrol', region.pr_id, 'merge'),
            f'{region.pr_id}_merge_{region.l_str}_{row:02d}.png'
        )

    @staticmethod
    def save_merge_image(region: Region, row: int, image: MatLike) -> None:
        """
        地图格子的图片
        """
        path = LargeMapRecorder.get_merge_image_path(region, row)
        cv2_utils.save_image(image, path)

    @staticmethod
    def get_floor_image_path(region: Region) -> str:
        """
        地图格子的图片路径
        """
        return os.path.join(
            os_utils.get_path_under_work_dir('.debug', 'world_patrol', region.pr_id, 'floor'),
            f'{region.pr_id}_merge_{region.l_str}.png'
        )

    @staticmethod
    def save_floor_image(region: Region, image: MatLike) -> None:
        """
        地图格子的图片
        """
        path = LargeMapRecorder.get_floor_image_path(region)
        cv2_utils.save_image(image, path)

    def special_drag_to(self, start: Point, end: Point) -> None:
        """
        特殊实现的拖动 拖动前 先按下鼠标一段时间
        """
        start_pos = self.ctx.controller.game_win.game2win_pos(start)
        end_pos = self.ctx.controller.game_win.game2win_pos(end)

        pyautogui.moveTo(start_pos.x, start_pos.y)
        time.sleep(0.2)
        pyautogui.mouseDown()
        time.sleep(0.2)
        pyautogui.dragTo(end_pos.x, end_pos.y, duration=1)
        time.sleep(0.2)
        pyautogui.mouseUp()
        time.sleep(0.2)


def get_mode_in_list(arr: List[Any], ignored_set: set[Any] = None, empty_return: Any = None) -> Any:
    """
    获取一个数组中出现最多的元素
    :param arr: 输入的数组
    :return: 出现次数最多的元素
    """
    if arr is None:
        return empty_return  # 如果数组为空，返回None

    if ignored_set is not None:
        arr = [item for item in arr if item not in ignored_set]

    if len(arr) == 0:
        return empty_return

    # 使用Counter统计每个元素的出现次数
    counter = Counter(arr)

    # 返回出现次数最多的元素
    return counter.most_common(1)[0][0]

def __debug(planet_name, region_name, run_mode: str = 'all'):
    ctx = SrContext()

    special_conditions = {
        '空间站黑塔 基座舱段': {'max_column': 1, 'max_row': 3},
        # map_const.P03_R11_F1.pr_id: {'max_row': 7, 'max_column': 6},  # 罗浮仙舟 - 幽囚狱 右边有较多空白
        # 'P04_PNKN_R10_PNKNDJY': {'skip_height': 700, 'max_row': 4, 'max_column': 4},  # 匹诺康尼 - 匹诺康尼大剧院 上下方有大量空白 skip_hegiht=700 下方报错需要手动保存
        '翁法罗斯 「浴血战端」悬锋城': {'max_column': 4, 'max_row': 11, 'drag_times_to_left_top': 6,
                                 'cols_to_cal_overlap_height': [1]},
        '翁法罗斯 「神谕圣地」雅努萨波利斯': { 'max_row': 8, 'max_column': 1, 'drag_times_to_left_top': 6},
        '翁法罗斯 「纷争荒墟」悬锋城': { 'max_row': 13, 'max_column': 11, 'drag_times_to_left': 6, 'drag_times_to_left_top': 10,},
        '翁法罗斯 「命运重渊」雅努萨波利斯': { 'max_row': 8, 'max_column': 1, 'drag_times_to_left_top': 6},
        '翁法罗斯 「呓语密林」神悟树庭': {
            'max_row': 9, 'max_column': 3, 'drag_times_to_left_top': 6,
            'overlap_width_mode': [0, 0, 786, 983],
            'overlap_height_mode': [0, 0, 426, 426, 426, 426, 426, 426, 426, 713],
        },
        '翁法罗斯 「半神议院」黎明云崖': {
            'max_row': 17, 'max_column': 5,
            'overlap_width_mode': [0, 0, 785, 785, 785, 991],
            'overlap_height_mode': [0, 0, 426, 426, 426, 426, 426, 426, 426, 426, 426, 426, 426, 426, 426, 426, 426, 426, 423]
        },
        '翁法罗斯 「穹顶关塞」晨昏之眼': {
            'max_row': 6, 'max_column': 8,
            'overlap_width_mode': [0, 0, 785, 785, 785, 785, 785, 785, 994],
            'overlap_height_mode': [0, 0, 426, 426, 426, 426, 423],
            'fix_width_rows': [6],
        },
        '翁法罗斯 「无晖祈堂」黎明云崖': {
            'max_row': 17, 'max_column': 5,
            'overlap_width_mode': [0, 0, 785, 785, 785, 991],
            'overlap_height_mode': [0, 0, 426, 426, 426, 426, 426, 426, 426, 426, 426, 426, 426, 426, 426, 426, 426, 426, 423]
        },
        '翁法罗斯 「龙骸古城」斯缇科西亚': {
            'max_row': 8, 'max_column': 7,
            'overlap_width_mode': [0, 0, 786, 786, 786, 786, 786, 965],
            'overlap_height_mode': [0, 0, 426, 426, 426, 426, 426, 426, 529],
        },
        '翁法罗斯 「云端遗堡」晨昏之眼': {
            'drag_times_to_left': 5,
            'max_row': 6, 'max_column': 9,
            'overlap_width_mode': [0, 0, 786, 786, 786, 786, 786, 786, 786, 890],
            'overlap_height_mode': [0, 0, 426, 426, 426, 426, 426],
            # 'fix_width_rows': [4],
        }
    }

    planet = ctx.map_data.best_match_planet_by_name(gt(planet_name))
    region = ctx.map_data.best_match_region_by_name(gt(region_name), planet=planet)

    key = f'{region.planet.cn} {region.cn}'
    log.info('当前录制 %s', key)
    sc = special_conditions.get(key, {})
    sc['ctx'] = ctx
    sc['region'] = region
    # sc['floor_list_to_record'] = [2]
    # sc['row_list_to_record'] = [5]
    # sc['col_list_to_record'] = [1, 2, 3]
    # sc['drag_times_to_left_top'] = 0  # 手动拖到左上会快一点
    # sc['drag_times_to_left'] = 0  # 只录一行时可以使用

    app = LargeMapRecorder(**sc)

    ctx.init_by_config()
    ctx.init_for_world_patrol()

    if run_mode == 'all':
        app.execute()  # 正常录制
    elif run_mode == 'screenshot':  # 只进行截图
        ctx.start_running()
        app.open_map()
        app.choose_planet()

        app.current_region_idx = 0
        app.choose_region()
        app.do_screenshot()
        app.merge_screenshot()

        ctx.stop_running()
    elif run_mode == 'merge':
        # app.debug = True
        app.merge_screenshot()
    elif run_mode == 'save':
        app.do_save()
    elif run_mode == 'fix':
        app.fix_all_after_map_record(region, 0, +231)
    elif run_mode == 'find_max_col':
        ctx.start_running()
        app.drag_to_get_max_column()
        ctx.stop_running()
    elif run_mode == 'find_max_row':
        ctx.start_running()
        app.drag_to_get_max_row()
        ctx.stop_running()
    elif run_mode == 'test_drag_to_left':  # 测试需要几次拉到最左边 需要先预测一个数值 drag_times_to_left 再运行观察结果
        ctx.start_running()
        app.back_to_left()
        ctx.stop_running()
    else:
        pass


if __name__ == '__main__':
    __debug('翁法罗斯', '「无晖祈堂」黎明云崖', 'save')
