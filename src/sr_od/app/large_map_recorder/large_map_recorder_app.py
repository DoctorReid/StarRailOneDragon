import time

import cv2
import numpy as np
from cv2.typing import MatLike
from typing import List, Optional

from one_dragon.base.geometry.point import Point
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import debug_utils, cv2_utils
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

_FLOOR_LIST = [-4, -3, -2, -1, 0, 1, 2, 3]


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
                 floor_list_to_record: Optional[List[int]] = None,
                 row_list_to_record: Optional[List[int]] = None,
                 rows_to_cal_overlap_width: List[int] = None,
                 cols_to_cal_overlap_height: List[int] = None,
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
        self.floor_list_to_record: Optional[List[int]] = floor_list_to_record  # 需要重新录制的楼层
        self.max_row: int = max_row  # 最多录制的行数 不传入时自动判断
        self.max_column: int = max_column  # 最多录制的列数 不传入时自动判断
        self.drag_times_to_left_top: int = drag_times_to_left_top  # 切换楼层时 拖动到左上角次数

        self.region_list: List[Region] = []
        for floor in _FLOOR_LIST:
            current_region = self.ctx.map_data.best_match_region_by_name(
                gt(self.region.cn),
                planet=self.region.planet,
                target_floor=floor
            )
            if current_region is not None:
                self.region_list.append(current_region)
        self.current_region_idx: int = 0
        self.current_region: Optional[Region] = None

        self.overlap_width_median: List[int] = []  # 截图重叠的宽度
        self.overlap_height_median: List[int] = []  # 截图重叠的高度

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
    @operation_node(name='截图')
    def do_screenshot(self) -> OperationRoundResult:
        if self.current_region_idx >= len(self.region_list):
            return self.round_success()

        self.current_region = self.region_list[self.current_region_idx]
        if self.floor_list_to_record is not None and self.current_region.floor not in self.floor_list_to_record:
            self.current_region_idx += 1
            return self.round_wait()

        op = ChooseFloor(self.ctx, self.current_region.floor)
        op_result = op.execute()
        if not op_result.success:
            return self.round_fail('选择区域失败')

        self._do_screenshot_1()
        if self.row_list_to_record is not None:
            while True:
                img = debug_utils.get_debug_image(LargeMapRecorder.region_part_image_name(self.current_region, self.row, 0))
                if img is None:
                    break
                else:
                    self.row += 1
            while True:
                img = debug_utils.get_debug_image(LargeMapRecorder.region_part_image_name(self.current_region, 0, self.col))
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
            debug_utils.save_debug_image(map_part, '%s_%02d_%02d' % (self.current_region.prl_id, self.row, self.col))
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

        self.overlap_width_median = self.get_overlap_width_median()
        self.overlap_height_median = self.get_overlap_height_median()
        for region in self.region_list:
            self.merge_region_screenshot(region, row, col)

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

        for l in _FLOOR_LIST:
            target_region = self.ctx.map_data.best_match_region_by_name(
                gt(self.region.cn),
                planet=self.region.planet,
                target_floor=l
            )
            if target_region is None:
                continue
            raw = self.ctx.map_data.get_large_map_image(target_region, 'raw')
            large_map_utils.init_large_map(self.ctx, target_region, raw,
                                           expand_arr=[lp, rp, tp, bp], save=True)

        return self.round_success()

    def back_to_left_top(self):
        """
        回到左上角
        """
        center = game_const.STANDARD_CENTER_POS
        rt = center + center + Point(-1, -1)
        for _ in range(self.drag_times_to_left_top):
            if not self.ctx.is_context_running:
                break
            self.ctx.controller.drag_to(end=rt, start=center, duration=1)  # 先拉到左上角
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
        bottom = Point(center.x, center.y + center.y)
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
        center = game_const.STANDARD_CENTER_POS
        right = Point(center.x + center.x - 1, center.y)
        for _ in range(2):
            self.ctx.controller.drag_to(end=right, start=center, duration=1)  # 往左拉到尽头
            time.sleep(1)
        self.col = 1

    def drag_to_next_row(self):
        """
        往下拖到下一行
        """
        center = Point(1350, 800)  # 大地图右方的空白区域 防止点击到地图的点 导致拖拽有问题
        top = center + Point(0, -self.drag_distance_to_next_row)
        self.ctx.controller.drag_to(end=top, start=center, duration=1)  # 往下拉一段
        time.sleep(1)
        self.row += 1

    def drag_to_next_col(self):
        """
        往右拖到下一列
        """
        center = Point(1350, 800)  # 大地图右方的空白区域 防止点击到地图的点 导致拖拽有问题
        left = center + Point(-self.drag_distance_to_next_col, 0)
        self.ctx.controller.drag_to(end=left, start=center, duration=1)  # 往右拉一段
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

        raise Exception('获取重叠高度失败')

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
        raise Exception('获取重叠宽度失败')

    @staticmethod
    def region_part_image_name(region: Region, row: int, col: int):
        return '%s_%02d_%02d' % (region.prl_id, row, col)

    def get_overlap_width_median(self) -> List[int]:
        """
        根据截图 计算各列重叠的宽度
        """
        max_row = self.row if self.max_row is None else self.max_row
        max_col = self.col if self.max_column is None else self.max_column

        overlap_width_list: List[List[int]] = []
        for i in range(max_col + 1):
            overlap_width_list.append([-1, -1])

        # 先求出每列的重叠宽度
        for region in self.region_list:
            for row in range(1, max_row + 1):
                if self.rows_to_cal_overlap_width is not None and row not in self.rows_to_cal_overlap_width:
                    continue
                last_col_img = None
                for col in range(1, max_col + 1):
                    cur_col_img = debug_utils.get_debug_image(LargeMapRecorder.region_part_image_name(region, row, col))

                    if last_col_img is not None:
                        overlap_width = LargeMapRecorder.get_overlap_width(last_col_img, cur_col_img, show=self.debug)
                        log.info('%d层 %02d行 %02d列 与前重叠宽度 %d', region.floor, row, col, overlap_width)

                        overlap_width_list[col].append(overlap_width)

                    last_col_img = cur_col_img

        overlap_width_median: List[int] = [0, 0]
        if self.max_column is not None:
            # 如果已经指定了最大列数 则除了最后一列的其他列 与前一列的重叠宽度一致
            all_col_width = []
            if max_col >= 2:
                for col in range(2, max_col):
                    for width in overlap_width_list[col]:
                        all_col_width.append(width)
                all_col_width_median = int(np.median(all_col_width))
                for col in range(2, max_col):
                    log.info('%02d列 与前重叠宽度中位数 %d', col, all_col_width_median)
                    overlap_width_median.append(all_col_width_median)
            for col in range(max_col, max_col + 1):
                width_median = int(np.median(overlap_width_list[col]))
                log.info('%02d列 与前重叠宽度中位数 %d', col, width_median)
                overlap_width_median.append(width_median)
        else:
            for col in range(2, max_col + 1):
                width_median = int(np.median(overlap_width_list[col]))
                log.info('%02d列 与前重叠宽度中位数 %d', col, width_median)
                overlap_width_median.append(width_median)

        log.info('重叠宽度中位数 %s', overlap_width_median)
        return overlap_width_median

    def get_overlap_height_median(self) -> List[int]:
        """
        根据截图 计算各行重叠的高度
        """
        max_row = self.row if self.max_row is None else self.max_row
        max_col = self.col if self.max_column is None else self.max_column

        overlap_height_list: List[List[int]] = []
        for i in range(max_row + 1):
            overlap_height_list.append([-1, -1])

        # 先求出每行的重叠高度
        for region in self.region_list:
            for col in range(1, max_col + 1):
                if self.cols_to_cal_overlap_height is not None and col not in self.cols_to_cal_overlap_height:
                    continue
                last_row_img = None
                for row in range(1, max_row + 1):
                    cur_row_img = debug_utils.get_debug_image(LargeMapRecorder.region_part_image_name(region, row, col))

                    if last_row_img is not None:
                        overlap_height = LargeMapRecorder.get_overlap_height(last_row_img, cur_row_img, show=self.debug)
                        log.info('%d层 %02d行 %02d列 与前重叠高度 %d', region.floor, row, col, overlap_height)

                        overlap_height_list[row].append(overlap_height)

                    last_row_img = cur_row_img

        overlap_height_median: List[int] = [0, 0]
        if self.max_row is not None:
            # 如果已经指定了最大行数 则除了最后一行的其他行 与前一行的重叠高度一致
            all_row_height = []
            if max_row >= 2:
                for row in range(2, max_row):
                    for height in overlap_height_list[row]:
                        all_row_height.append(height)
                all_row_height_median = int(np.median(all_row_height))
                for row in range(2, max_row):
                    log.info('%02d行 与前重叠高度中位数 %d', row, all_row_height_median)
                    overlap_height_median.append(all_row_height_median)
            for row in range(max_row, max_row + 1):
                height_median = int(np.median(overlap_height_list[row]))
                log.info('%02d行 与前重叠高度中位数 %d', row, height_median)
                overlap_height_median.append(height_median)
        else:
            for row in range(2, max_row + 1):
                height_median = int(np.median(overlap_height_list[row]))
                log.info('%02d行 与前重叠高度中位数 %d', row, height_median)
                overlap_height_median.append(height_median)

        log.info('重叠宽度中位数 %s', overlap_height_median)
        return overlap_height_median

    def merge_region_screenshot(self, region: Region, max_row: int, max_col: int, show=False):
        img_list: List[List[Optional[MatLike]]] = [[]]
        for row in range(1, max_row + 1):
            img_list.append([None])  # 每一行的第0列 都置为空
            for col in range(1, max_col + 1):
                img = debug_utils.get_debug_image(LargeMapRecorder.region_part_image_name(region, row, col))
                img_list[row].append(img)

        # 按重叠宽度的中位数对每行图片进行合并
        row_image_list: List[MatLike] = []
        for row in range(1, max_row + 1):
            merge = img_list[row][1]
            for col in range(2, max_col + 1):
                overlap_w = self.overlap_width_median[col]
                extra_part = img_list[row][col][:, overlap_w + 1:]
                # 水平拼接两张图像
                merge = cv2.hconcat([merge, extra_part])

            log.info('%d层 %02d行 合并后size为 %s', region.floor, row, merge.shape)
            debug_utils.save_debug_image(merge, '%s_row_%02d' % (region.prl_id, row))
            row_image_list.append(merge)
            if show:
                cv2_utils.show_image(merge, win_name='row_%02d' % row)

        # 进行垂直合并
        final_merge = LargeMapRecorder.concat_vertically_by_list(row_image_list, show=show)

        log.info('%d层 最终合并后size为 %s', region.floor, final_merge.shape)
        if show:
            cv2_utils.show_image(final_merge, win_name='final_merge', wait=0)

        self.ctx.map_data.save_large_map_image(final_merge, region, 'raw')

    @staticmethod
    def same_as_last_row(region: Region, row: int, max_col: int) -> bool:
        """
        是否跟前一行一样
        """
        if row <= 1:
            return False
        for col in range(max_col):
            prev_image = debug_utils.get_debug_image(LargeMapRecorder.region_part_image_name(region, row - 1, col))
            next_image = debug_utils.get_debug_image(LargeMapRecorder.region_part_image_name(region, row, col))
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
                route_list = get_sim_uni_route_list(level_type)
                for route in route_list:
                    if route.region != floor_region:
                        continue

                    if route.op_list is not None and len(route.op_list) > 0:
                        for route_item in route.op_list:
                            if route_item['op'] in to_fix_op:
                                route_item['data'][0] += dx
                                route_item['data'][1] += dy

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
        while True:
            if not self.ctx.is_context_running:
                break
            log.info(f'正在截图 列{self.col}')

            screen = self.screenshot()
            screen_map_rect = large_map_utils.get_screen_map_rect(self.region)
            map_part = cv2_utils.crop_image_only(screen, screen_map_rect)

            if last_map_part is not None and cv2_utils.is_same_image(last_map_part, map_part, threshold=0.9):
                log.info(f'已经到达最右端 列数为{self.col - 1}')
                break

            last_map_part = map_part
            self.drag_to_next_col()

    def drag_to_get_max_row(self) -> None:
        """
        在地图上找到一个图像多的位置
        在最上方开始 尝试往下滑动 看最多需要滑动多少次到底
        """
        self.row = 1
        last_map_part = None
        while True:
            if not self.ctx.is_context_running:
                break
            log.info(f'正在截图 行{self.row}')

            screen = self.screenshot()
            screen_map_rect = large_map_utils.get_screen_map_rect(self.region)
            map_part = cv2_utils.crop_image_only(screen, screen_map_rect)

            if last_map_part is not None and cv2_utils.is_same_image(last_map_part, map_part, threshold=0.9):
                log.info(f'已经到达最下端 行数为{self.row - 1}')
                break

            last_map_part = map_part
            self.drag_to_next_row()


def __debug(planet_name, region_name, run_mode: str = 'all'):
    ctx = SrContext()

    special_conditions = {
        # map_const.P03_R11_F1.pr_id: {'max_row': 7, 'max_column': 6},  # 罗浮仙舟 - 幽囚狱 右边有较多空白
        # 'P04_PNKN_R10_PNKNDJY': {'skip_height': 700, 'max_row': 4, 'max_column': 4},  # 匹诺康尼 - 匹诺康尼大剧院 上下方有大量空白 skip_hegiht=700 下方报错需要手动保存
        'P05_WFLS_R02_YXZDXFC': {'max_column': 4, 'max_row': 11, 'drag_times_to_left_top': 6,
                                 'cols_to_cal_overlap_height': [1]},
        'P05_WFLS_R04_FZHX': { 'max_row': 8, 'max_column': 1, }
    }

    planet = ctx.map_data.best_match_planet_by_name(gt(planet_name))
    region = ctx.map_data.best_match_region_by_name(gt(region_name), planet=planet)

    log.info('当前录制 %s', region.pr_id)
    sc = special_conditions.get(region.pr_id, {})
    sc['ctx'] = ctx
    sc['region'] = region
    # sc['row_list_to_record'] = [2, 3]

    app = LargeMapRecorder(**sc)

    ctx.init_by_config()
    ctx.init_for_world_patrol()

    if run_mode == 'all':
        app.execute()  # 正常录制
    elif run_mode == 'merge':
        # app.debug = True
        app.merge_screenshot()
    elif run_mode == 'save':
        app.do_save()
    elif run_mode == 'fix':
        app.fix_all_after_map_record(region, 6, 3)
    elif run_mode == 'find_max_col':
        ctx.start_running()
        app.drag_to_get_max_column()
        ctx.stop_running()
    elif run_mode == 'find_max_row':
        ctx.start_running()
        app.drag_to_get_max_row()
        ctx.stop_running()



if __name__ == '__main__':
    __debug('翁法罗斯', '「命运重渊」雅努萨波利斯', 'save')
