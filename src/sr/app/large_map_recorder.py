import time
from typing import List, Optional

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import Point
from basic.img import cv2_utils
from basic.img.os import save_debug_image, get_debug_image
from basic.log_utils import log
from sr.app import Application2
from sr.const import map_const, STANDARD_CENTER_POS, STANDARD_RESOLUTION_W
from sr.const.map_const import Region, region_with_another_floor, PLANET_2_REGION
from sr.context import Context, get_context
from sr.image.sceenshot import large_map
from sr.operation import Operation, StateOperationNode, OperationOneRoundResult
from sr.operation.unit.choose_planet import ChoosePlanet
from sr.operation.unit.choose_region import ChooseRegion
from sr.operation.unit.open_map import OpenMap
from sr.operation.unit.scale_large_map import ScaleLargeMap
from sr.win import Window, WinRect


class LargeMapRecorder(Application2):
    """
    开发用的截图工具 只支持PC版 需要自己缩放大地图到最小比例
    把整个大地图记录下来
    """

    def __init__(self, ctx: Context, region: Region,
                 skip_height: Optional[int] = None,
                 floor_list: Optional[List[int]] = None,
                 row_list: Optional[List[int]] = None):
        nodes = []

        nodes.append(StateOperationNode('打开地图', op=OpenMap(ctx)))
        nodes.append(StateOperationNode('选择星球', op=ChoosePlanet(ctx, region.planet)))
        nodes.append(StateOperationNode('截图', self._do_screenshot))
        nodes.append(StateOperationNode('保存', self.do_save))

        super().__init__(ctx, op_name='大地图录制 %s' % region.cn,
                         nodes=nodes)

        self.region: Region = region
        self.current_floor: int = -1
        self.current_region: Optional[Region] = None
        self.row: int = 0
        self.col: int = 0
        self.skip_height: Optional[int] = skip_height  # 部分地图上方较空 可以跳过部分高度不录制
        self.row_list: Optional[List[int]] = row_list  # 需要重新录制的行数
        self.floor_list: Optional[List[int]] = floor_list  # 需要重新录制的楼层

    def _init_before_execute(self):
        super()._init_before_execute()
        self.current_floor = -1
        self.current_region = None
        self.row = 0
        self.col = 0

    def _do_screenshot(self) -> OperationOneRoundResult:
        if self.current_floor > 3:
            return Operation.round_success()

        if self.floor_list is not None and self.current_floor not in self.floor_list:
            self.current_floor += 1
            return Operation.round_wait()

        self.current_region = region_with_another_floor(self.region, self.current_floor)
        self.current_floor += 1

        if self.current_region is None:
            return Operation.round_wait()

        op = ChooseRegion(self.ctx, self.current_region)
        op_result = op.execute()
        if not op_result.success:
            return Operation.round_fail('选择区域失败')

        self._do_screenshot_1()
        if self.row_list is not None:
            while True:
                img = get_debug_image(LargeMapRecorder.region_part_image_name(self.current_region, self.row, 0))
                if img is None:
                    break
                else:
                    self.row += 1
            while True:
                img = get_debug_image(LargeMapRecorder.region_part_image_name(self.current_region, 0, self.col))
                if img is None:
                    break
                else:
                    self.col += 1
        LargeMapRecorder.do_merge_1(self.current_region, self.row, self.col, skip_height=self.skip_height)

        return Operation.round_wait()

    def _do_screenshot_1(self):
        """
        先拉到最左上角 然后一行一行地截图 最后再拼接起来。
        多层数的话需要一次性先将所有楼层截图再处理 保证各楼层大小一致
        :return:
        """
        self.back_to_left_top()
        while True:
            if not self.ctx.running:
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

    def screenshot_horizontally(self):
        """
        水平滚动地截取地图部分 并罗盘保存
        :return: 拼接好的图片
        """
        img = []
        # 每秒往右拉一段距离截图
        while True:
            if not self.ctx.running:
                return
            screen = self.screenshot()
            map_part = cv2_utils.crop_image_only(screen, large_map.CUT_MAP_RECT)
            save_debug_image(map_part, '%s_%02d_%02d' % (self.current_region.prl_id, self.row, self.col))
            if len(img) == 0 or not cv2_utils.is_same_image(img[len(img) - 1], map_part):
                img.append(map_part)
                self.drag_to_next_col()
            else:
                break

    def _do_screenshot_2(self, region: Region):
        """
        先拉到最左上角 然后一列一列地截图 最后再拼接起来。
        多层数的话需要一次性先将所有楼层截图再处理 保证各楼层大小一致
        :return:
        """
        win: Window = self.ctx.controller.win
        rect: WinRect = win.get_win_rect()

        center = Point(rect.w // 2, rect.h // 2)
        self.back_to_left_top()

        img = []
        i = 0
        while True:
            if not self.ctx.running:
                return False
            row_img = self.screenshot_vertically(center)  # 对一列进行垂直的截图
            cv2_utils.show_image(row_img, win_name='row %d' % i)
            i += 1
            if len(img) == 0 or not cv2_utils.is_same_image(img[len(img) - 1], row_img):
                img.append(row_img)
                self.ctx.controller.drag_to(end=Point(center.x - 200, center.y), start=center, duration=1)  # 往右拉一段
                time.sleep(1)
                self.back_to_top()
            else:
                break

        merge = img[0]
        for i in range(len(img)):
            if i == 0:
                merge = img[i]
            else:
                merge = cv2_utils.concat_horizontally(merge, img[i], decision_width=large_map.CUT_MAP_RECT.x2 - large_map.CUT_MAP_RECT.x1 - 300)

        cv2_utils.show_image(merge, win_name='region.prl_id')

    def screenshot_vertically(self, center):
        """
        垂直滚动地截取地图部分 然后拼接在一起
        :param center: 中心点
        :return: 拼接好的图片
        """
        img = []
        # 每秒往右拉一段距离截图
        while True:
            if not self.ctx.running:
                return
            screen = self.screenshot()
            map_part = cv2_utils.crop_image_only(screen, large_map.CUT_MAP_RECT)
            save_debug_image(map_part, LargeMapRecorder.region_part_image_name(self.current_region, self.row, self.col))
            cv2_utils.show_image(map_part, win_name='screenshot_vertically_map_part')
            if len(img) == 0 or not cv2_utils.is_same_image(img[len(img) - 1], map_part):
                img.append(map_part)
                self.ctx.controller.drag_to(end=Point(center.x, center.y - 200), start=center, duration=1)  # 往下拉一段
                time.sleep(1.5)
            else:
                break

        merge = img[0]
        for i in range(len(img)):
            if i == 0:
                merge = img[i]
            else:
                merge = LargeMapRecorder.concat_vertically(merge, img[i])

        return merge

    def do_save(self) -> OperationOneRoundResult:
        # 检测几个楼层是否大小一致
        shape = None
        lp, rp, tp, bp = None, None, None, None
        for l in [-1, 0, 1, 2, 3]:
            target_region = region_with_another_floor(self.region, l)
            if target_region is None:
                continue

            raw = large_map.get_large_map_image(target_region, 'raw')
            if shape is None:
                shape = raw.shape
            else:
                shape2 = raw.shape
                if shape[0] != shape2[0] or shape[1] != shape2[1]:
                    log.error('层数截图大小不一致')

            # 不同楼层需要拓展的大小可能不一致 保留一个最大的
            lp2, rp2, tp2, bp2 = large_map.get_expand_arr(raw)
            if lp is None or lp2 > lp:
                lp = lp2
            if rp is None or rp2 > rp:
                rp = rp2
            if tp is None or tp2 > tp:
                tp = tp2
            if bp is None or bp2 > bp:
                bp = bp2

        # cv2.waitKey(0)

        for l in [-1, 0, 1, 2, 3]:
            target_region = region_with_another_floor(self.region, l)
            if target_region is None:
                continue
            raw = large_map.get_large_map_image(target_region, 'raw')
            large_map.init_large_map(target_region, raw, self.ctx.im,
                                     expand_arr=[lp, rp, tp, bp], save=True)

        return Operation.round_success()

    def back_to_left_top(self):
        """
        回到左上角
        """
        center = STANDARD_CENTER_POS
        rt = center + center
        for _ in range(3):
            if not self.ctx.running:
                break
            self.ctx.controller.drag_to(end=rt, start=center, duration=1)  # 先拉到左上角
            time.sleep(1.5)
        self.col = 0
        self.row = 0

        if self.skip_height is not None:
            drag_from = Point(1350, 800)  # 大地图有方的空白区域 防止点击到地图的点 导致拖拽有问题
            drag_to = drag_from + Point(0, -self.skip_height)
            self.ctx.controller.drag_to(end=drag_to, start=drag_from, duration=1)
            time.sleep(1.5)

    def back_to_top(self):
        """
        回到正上方
        """
        center = STANDARD_CENTER_POS
        bottom = Point(center.x, center.y + center.y)
        for _ in range(6):
            if not self.ctx.running:
                break
            self.ctx.controller.drag_to(end=bottom, start=center, duration=1)  # 往上拉到尽头
            time.sleep(1.5)
        self.row = 0

    def back_to_left(self):
        """
        回到正左方
        """
        center = STANDARD_CENTER_POS
        right = Point(center.x + center.x, center.y)
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

    @staticmethod
    def do_merge_1(region: Region, max_row: int, max_col: int, skip_height: Optional[int] = None, show=False):
        img_list: List[List[MatLike]] = []
        for row in range(max_row):
            img_list.append([])
            for col in range(max_col):
                img = get_debug_image(LargeMapRecorder.region_part_image_name(region, row, col))
                img_list[row].append(img)

        # # 先求出每列的重叠宽度
        overlap_width_list: List[List[int]] = []
        for i in range(max_col):
            overlap_width_list.append([])
        for row in range(max_row):
            for col in range(1, max_col):
                prev_img = img_list[row][col - 1]
                next_img = img_list[row][col]
                overlap_width = LargeMapRecorder.get_overlap_width(prev_img, next_img, show=show)
                log.info('%02d行 %02d列 与前重叠宽度 %d', row, col, overlap_width)
                overlap_width_list[col].append(overlap_width)

        overlap_width_median: List[int] = [0]
        for col in range(1, max_col):
            overlap_width_median.append(int(np.median(overlap_width_list[col])))

        for row in range(max_row):
            for col in range(1, max_col):
                if abs(overlap_width_list[col][row] - overlap_width_median[col]) > 5:
                    log.info('%02d行 %02d列 重叠宽度偏离较大 %d', row, col, overlap_width_list[row][col])

        # overlap_width_median = [0, 890, 890, 890, 890, 890, 1055, 1100]
        log.info('重叠宽度中位数 %s', overlap_width_median)

        # 按重叠宽度的中位数对每行图片进行合并
        row_image_list: List[MatLike] = []
        for row in range(max_row):
            merge = img_list[row][0]
            for col in range(1, max_col):
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

        if skip_height is not None:
            empty = np.full((skip_height, final_merge.shape[1], 3),
                            fill_value=large_map.EMPTY_COLOR, dtype=np.uint8)
            final_merge = cv2.vconcat([empty, final_merge])

        log.info('最终合并后size为 %s', final_merge.shape)
        if show:
            cv2_utils.show_image(final_merge, win_name='final_merge', wait=0)

        large_map.save_large_map_image(final_merge, region, 'raw')

    @staticmethod
    def same_as_last_row(region: Region, row: int, max_col: int) -> bool:
        """
        是否跟前一行一样
        """
        if row == 0:
            return False
        for col in range(max_col):
            prev_image = get_debug_image(LargeMapRecorder.region_part_image_name(region, row - 1, col))
            next_image = get_debug_image(LargeMapRecorder.region_part_image_name(region, row, col))
            if not cv2_utils.is_same_image(prev_image, next_image):
                return False
        return True

def _init_map_for_sim_uni():
    """
    初始化模拟宇宙用的大地图
    :return:
    """
    ctx = get_context()
    ctx.init_image_matcher()
    for regions in PLANET_2_REGION.values():
        for region in regions:
            lm_info = ctx.ih.get_large_map(region)
            sp_mask, _ = large_map.get_sp_mask_by_template_match(lm_info, ctx.im)
            sim_uni_origin = large_map.get_origin_for_sim_uni(lm_info.origin, sp_mask)
            sim_uni_mask = large_map.get_road_mask_for_sim_uni(lm_info.origin, sp_mask)
            large_map.save_large_map_image(sim_uni_origin, region, 'sim_uni_origin')
            large_map.save_large_map_image(sim_uni_mask, region, 'sim_uni_mask')


if __name__ == '__main__':
    r = map_const.P03_R06_F1
    # LargeMapRecorder.do_merge_1(r, 5, 3, show=True)
    # exit(0)

    # 执行前先传送到别的地图
    ctx = get_context()
    app = LargeMapRecorder(ctx, r,
                           #skip_height=200,
                           floor_list=[1]
                           )

    ctx.init_all(renew=True)
    app.do_save()
    # app.execute()
