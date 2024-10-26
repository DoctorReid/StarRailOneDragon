import time
from typing import List, Optional

import cv2
import numpy as np
from cv2.typing import MatLike

from one_dragon.base.controller.pc_game_window import PcGameWindow
from one_dragon.base.geometry.point import Point
from one_dragon.base.geometry.rectangle import Rect
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
                 floor_list: Optional[List[int]] = None,
                 row_list: Optional[List[int]] = None,
                 max_row: Optional[int] = None,
                 max_column: Optional[int] = None
                 ):
        SrApplication.__init__(self, ctx, 'large_map_recorder', op_name='大地图录制 %s' % region.cn)

        self.region: Region = region
        self.current_floor: int = _FLOOR_LIST[0]
        self.current_region: Optional[Region] = None
        self.row: int = 0
        self.col: int = 0
        self.skip_height: Optional[int] = skip_height  # 部分地图上方较空 可以跳过部分高度不录制
        self.row_list: Optional[List[int]] = row_list  # 需要重新录制的行数
        self.floor_list: Optional[List[int]] = floor_list  # 需要重新录制的楼层
        self.max_row: int = max_row  # 最多录制的行数 不传入时自动判断
        self.max_column: int = max_column  # 最多录制的列数 不传入时自动判断

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
        if self.current_floor > 3:
            return self.round_success()

        if self.floor_list is not None and self.current_floor not in self.floor_list:
            self.current_floor += 1
            return self.round_wait()

        self.current_region = self.ctx.map_data.best_match_region_by_name(
            gt(self.region.cn),
            planet=self.region.planet,
            target_floor=self.current_floor
        )
        self.current_floor += 1

        if self.current_region is None:
            return self.round_wait()

        op = ChooseFloor(self.ctx, self.current_region.floor)
        op_result = op.execute()
        if not op_result.success:
            return self.round_fail('选择区域失败')

        self._do_screenshot_1()
        if self.row_list is not None:
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

        row = self.row if self.max_row is None else self.max_row
        col = self.col if self.max_column is None else self.max_column

        self.do_merge_1(self.current_region, row, col, skip_height=self.skip_height)

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
            if self.row_list is not None and self.row > np.max(self.row_list):
                break
            if self.row_list is not None and self.row not in self.row_list:
                self.drag_to_next_row()
                continue

            self.screenshot_horizontally()  # 对一行进行水平的截图

            if not LargeMapRecorder.same_as_last_row(self.current_region, self.row, self.col):
                self.drag_to_next_row()
                self.back_to_left()
            else:
                break

            if self.max_row is not None and self.row > self.max_row:
                break

    def screenshot_horizontally(self):
        """
        水平滚动地截取地图部分 并罗盘保存
        :return: 拼接好的图片
        """
        img = []
        # 每秒往右拉一段距离截图
        while True:
            if not self.ctx.is_context_running:
                return
            screen = self.screenshot()
            screen_map_rect = large_map_utils.get_screen_map_rect(self.region)
            map_part = cv2_utils.crop_image_only(screen, screen_map_rect)
            debug_utils.save_debug_image(map_part, '%s_%02d_%02d' % (self.current_region.prl_id, self.row, self.col))
            if len(img) == 0 or not cv2_utils.is_same_image(img[len(img) - 1], map_part):
                img.append(map_part)
                self.drag_to_next_col()
            else:
                break

            if self.max_column is not None and self.col > self.max_column:
                break

    def do_save(self) -> OperationRoundResult:
        # 检测几个楼层是否大小一致
        shape = None
        lp, rp, tp, bp = None, None, None, None
        for l in _FLOOR_LIST:
            target_region = self.ctx.map_data.best_match_region_by_name(
                gt(self.region.cn),
                planet=self.region.planet,
                target_floor=l
            )
            if target_region is None:
                continue

            raw = self.ctx.map_data.get_large_map_image(target_region, 'raw')
            if shape is None:
                shape = raw.shape
            else:
                shape2 = raw.shape
                if shape[0] != shape2[0] or shape[1] != shape2[1]:
                    log.error('层数截图大小不一致 %s %s', shape, shape2)

            # 不同楼层需要拓展的大小可能不一致 保留一个最大的
            screen_map_rect = large_map_utils.get_screen_map_rect(target_region)
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
        for _ in range(3):
            if not self.ctx.is_context_running:
                break
            self.ctx.controller.drag_to(end=rt, start=center, duration=1)  # 先拉到左上角
            time.sleep(1.5)
        self.col = 0
        self.row = 0

        if self.skip_height is not None:
            drag_from = Point(1350, 800)  # 大地图有方的空白区域 防止点击到地图的点 导致拖拽有问题
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
        self.row = 0

    def back_to_left(self):
        """
        回到正左方
        """
        center = game_const.STANDARD_CENTER_POS
        right = Point(center.x + center.x - 1, center.y)
        for _ in range(2):
            self.ctx.controller.drag_to(end=right, start=center, duration=1)  # 往左拉到尽头
            time.sleep(1)
        self.col = 0

    def drag_to_next_row(self):
        """
        往下拖到下一行
        """
        center = Point(1350, 800)  # 大地图右方的空白区域 防止点击到地图的点 导致拖拽有问题
        top = center + Point(0, -200)
        self.ctx.controller.drag_to(end=top, start=center, duration=1)  # 往下拉一段
        time.sleep(1)
        self.row += 1

    def drag_to_next_col(self):
        """
        往右拖到下一列
        """
        center = Point(1350, 800)  # 大地图右方的空白区域 防止点击到地图的点 导致拖拽有问题
        left = center + Point(-200, 0)
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
    def get_overlap_width(img1: MatLike, img2: MatLike, decision_width: int = 150, show: bool = False):
        """
        获取第二张图在第一图上的重叠宽度
        """
        # empty_mask = cv2_utils.color_in_range(img1, [200, 200, 200], [220, 220, 220])  # 空白部分的掩码
        # img1_mask = cv2.bitwise_not(empty_mask)  # 非空白部分的掩码
        # img1_mask = large_map.get_large_map_road_mask(img1)
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

    def do_merge_1(self, region: Region, max_row: int, max_col: int, skip_height: Optional[int] = None, show=False):
        img_list: List[List[MatLike]] = []
        for row in range(max_row + 1):
            img_list.append([])
            for col in range(max_col + 1):
                img = debug_utils.get_debug_image(LargeMapRecorder.region_part_image_name(region, row, col))
                img_list[row].append(img)

        # # 先求出每列的重叠宽度
        overlap_width_list: List[List[int]] = []
        for i in range(max_col + 1):
            overlap_width_list.append([])
        for row in range(max_row + 1):
            for col in range(1, max_col + 1):
                prev_img = img_list[row][col - 1]
                next_img = img_list[row][col]
                overlap_width = LargeMapRecorder.get_overlap_width(prev_img, next_img, show=show)
                log.info('%02d行 %02d列 与前重叠宽度 %d', row, col, overlap_width)
                overlap_width_list[col].append(overlap_width)

        overlap_width_median: List[int] = [0]
        for col in range(1, max_col + 1):
            overlap_width_median.append(int(np.median(overlap_width_list[col])))

        for row in range(max_row + 1):
            for col in range(1, max_col + 1):
                if abs(overlap_width_list[col][row] - overlap_width_median[col]) > 5:
                    log.info('%02d行 %02d列 重叠宽度偏离较大 %d', row, col, overlap_width_list[col][row])

        # overlap_width_median = [0, 890, 890, 890, 890, 890, 1055, 1100]
        log.info('重叠宽度中位数 %s', overlap_width_median)

        # 按重叠宽度的中位数对每行图片进行合并
        row_image_list: List[MatLike] = []
        for row in range(max_row + 1):
            merge = img_list[row][0]
            for col in range(1, max_col + 1):
                overlap_w = overlap_width_median[col]
                extra_part = img_list[row][col][:, overlap_w + 1:]
                # 水平拼接两张图像
                merge = cv2.hconcat([merge, extra_part])

            log.info('行%02d 合并后size为 %s', row, merge.shape)
            row_image_list.append(merge)
            if show:
                cv2_utils.show_image(merge, win_name='row_%02d' % row)

        # 进行垂直合并
        final_merge = LargeMapRecorder.concat_vertically_by_list(row_image_list)

        # if skip_height is not None:
        #     empty = np.full((skip_height, final_merge.shape[1], 3),
        #                     fill_value=large_map.EMPTY_COLOR, dtype=np.uint8)
        #     final_merge = cv2.vconcat([empty, final_merge])

        log.info('最终合并后size为 %s', final_merge.shape)
        if show:
            cv2_utils.show_image(final_merge, win_name='final_merge', wait=0)

        self.ctx.map_data.save_large_map_image(final_merge, region, 'raw')

    @staticmethod
    def same_as_last_row(region: Region, row: int, max_col: int) -> bool:
        """
        是否跟前一行一样
        """
        if row == 0:
            return False
        for col in range(max_col):
            prev_image = debug_utils.get_debug_image(LargeMapRecorder.region_part_image_name(region, row - 1, col))
            next_image = debug_utils.get_debug_image(LargeMapRecorder.region_part_image_name(region, row, col))
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


def __debug(planet_name, region_name, run_mode: str = 'all'):
    ctx = SrContext()

    special_conditions = {
        # map_const.P03_R11_F1.pr_id: {'max_row': 7, 'max_column': 6},  # 罗浮仙舟 - 幽囚狱 右边有较多空白
        'P04_PNKN_R10_PNKNDJY': {'skip_height': 700, 'max_row': 4, 'max_column': 4},  # 匹诺康尼 - 匹诺康尼大剧院 上下方有大量空白 skip_hegiht=700 下方报错需要手动保存
    }

    planet = ctx.map_data.best_match_planet_by_name(gt(planet_name))
    region = ctx.map_data.best_match_region_by_name(gt(region_name), planet=planet, target_floor=0)

    log.info('当前录制 %s', region.pr_id)
    sc = special_conditions.get(region.pr_id, {})

    app = LargeMapRecorder(ctx, region,
                           skip_height=sc.get('skip_height', None),
                           max_row=sc.get('max_row', None),
                           max_column=sc.get('max_column', None),
                           # floor_list=[-3],
                           )

    ctx.init_by_config()
    ctx.init_for_world_patrol()

    if run_mode == 'all':
        app.execute()  # 正常录制
    elif run_mode == 'merge':
        app.do_merge_1(region,
                       skip_height=sc.get('skip_height', None),
                       max_row=sc.get('max_row', None),
                       max_col=sc.get('max_column', None),
                       show=True
                       )
    elif run_mode == 'save':
        app.do_save()
    elif run_mode == 'fix':
        app.fix_all_after_map_record(region, 0, 0)



if __name__ == '__main__':
    __debug('匹诺康尼', '匹诺康尼大剧院', 'save')
