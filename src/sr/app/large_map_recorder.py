import time

from cv2.typing import MatLike

from basic import Point
from basic.img import cv2_utils
from basic.log_utils import log
from sr.app import Application2
from sr.const import map_const
from sr.const.map_const import Region, region_with_another_floor, PLANET_2_REGION
from sr.context import Context, get_context
from sr.image.sceenshot import large_map
from sr.operation import Operation, StateOperationNode, OperationOneRoundResult
from sr.operation.unit.choose_planet import ChoosePlanet
from sr.operation.unit.open_map import OpenMap
from sr.operation.unit.scale_large_map import ScaleLargeMap
from sr.win import Window, WinRect


class LargeMapRecorder(Application2):
    """
    开发用的截图工具 只支持PC版
    把整个大地图记录下来
    """

    def __init__(self, ctx: Context, region: Region, way: int = 1):
        nodes = []

        nodes.append(StateOperationNode('打开地图', op=OpenMap(ctx)))
        nodes.append(StateOperationNode('缩放地图', op=ScaleLargeMap(ctx, -5)))
        nodes.append(StateOperationNode('选择星球', op=ChoosePlanet(ctx, region.planet)))
        nodes.append(StateOperationNode('截图', self._do_screenshot))
        nodes.append(StateOperationNode('保存', self._do_save))

        super().__init__(ctx, op_name='大地图录制 %s' % region.cn,
                         nodes=nodes)

        self.region: Region = region
        self.current_floor: int = -1
        self.raw_image: dict[str, MatLike] = {}
        self.way: int = way

    def _init_before_execute(self):
        super()._init_before_execute()
        self.current_floor = -1
        self.raw_image = {}

    def _do_screenshot(self) -> OperationOneRoundResult:
        if self.current_floor > 3:
            return Operation.round_success()

        region = region_with_another_floor(self.region, self.current_floor)
        self.current_floor += 1

        if region is None:
            return Operation.round_wait()

        if self.way == 1:
            self._do_screenshot_1(region)

        return Operation.round_wait()

    def _do_screenshot_1(self, region: Region):
        """
        先拉到最左上角 然后一行一行地截图 最后再拼接起来。
        多层数的话需要一次性先将所有楼层截图再处理 保证各楼层大小一致
        :return:
        """
        win: Window = self.ctx.controller.win
        rect: WinRect = win.get_win_rect()

        center = Point(rect.w // 2, rect.h // 2)
        for _ in range(2):
            self.ctx.controller.drag_to(end=Point(rect.w, rect.h), start=center, duration=1)  # 先拉到左上角
            time.sleep(1)
        img = []
        for i in range(10):
            if not self.ctx.running:
                return False
            row_img = self.screenshot_horizontally(center)  # 对一行进行水平的截图
            cv2_utils.show_image(row_img, win_name='row %d' % i)
            if len(img) == 0 or not cv2_utils.is_same_image(img[len(img) - 1], row_img):
                img.append(row_img)
                self.ctx.controller.drag_to(end=Point(center.x, center.y - 200), start=center, duration=1)  # 往下拉一段
                time.sleep(1)
                self.ctx.controller.drag_to(end=Point(rect.w, center.y), start=center, duration=1)  # 往左拉到尽头
                time.sleep(1)
                self.ctx.controller.drag_to(end=Point(rect.w, center.y), start=center, duration=1)  # 往左拉到尽头
                time.sleep(1)
            else:
                break

        merge = img[0]
        for i in range(len(img)):
            if i == 0:
                merge = img[i]
            else:
                merge = cv2_utils.concat_vertically(merge, img[i], decision_height=large_map.CUT_MAP_RECT.y2 - large_map.CUT_MAP_RECT.y1 - 300)

        self.raw_image[region.prl_id] = merge
        cv2_utils.show_image(merge, win_name='region.prl_id')

    def screenshot_horizontally(self, center):
        """
        水平滚动地截取地图部分 然后拼接在一起
        :param center: 中心点
        :return: 拼接好的图片
        """
        img = []
        # 每秒往右拉一段距离截图
        for i in range(10):
            if not self.ctx.running:
                return
            screen = self.screenshot()
            map_part = cv2_utils.crop_image_only(screen, large_map.CUT_MAP_RECT)
            print(map_part.shape)
            cv2_utils.show_image(map_part, win_name='screenshot_horizontally_map_part')
            if len(img) == 0 or not cv2_utils.is_same_image(img[len(img) - 1], map_part):
                img.append(map_part)
                self.ctx.controller.drag_to(end=Point(center.x - 200, center.y), start=center, duration=1)  # 往右拉一段
                time.sleep(1)
            else:
                break

        merge = img[0]
        for i in range(len(img)):
            if i == 0:
                merge = img[i]
            else:
                merge = cv2_utils.concat_horizontally(merge, img[i])
        return merge

    def _do_screenshot_2(self, region: Region):
        """
        先拉到最左上角 然后一列一列地截图 最后再拼接起来。
        多层数的话需要一次性先将所有楼层截图再处理 保证各楼层大小一致
        :return:
        """
        win: Window = self.ctx.controller.win
        rect: WinRect = win.get_win_rect()

        center = Point(rect.w // 2, rect.h // 2)
        for _ in range(2):
            self.ctx.controller.drag_to(end=Point(rect.w, rect.h), start=center, duration=1)  # 先拉到左上角
            time.sleep(1)
        img = []
        for i in range(10):
            if not self.ctx.running:
                return False
            row_img = self.screenshot_vertically(center)  # 对一列进行垂直的截图
            cv2_utils.show_image(row_img, win_name='row %d' % i)
            if len(img) == 0 or not cv2_utils.is_same_image(img[len(img) - 1], row_img):
                img.append(row_img)
                self.ctx.controller.drag_to(end=Point(center.x, center.y - 200), start=center, duration=1)  # 往右拉一段
                time.sleep(1)
                for _ in range(2):
                    self.ctx.controller.drag_to(end=Point(center.x, rect.h), start=center, duration=1)  # 往上拉到尽头
                    time.sleep(1)
            else:
                break

        merge = img[0]
        for i in range(len(img)):
            if i == 0:
                merge = img[i]
            else:
                merge = cv2_utils.concat_horizontally(merge, img[i], decision_width=large_map.CUT_MAP_RECT.x2 - large_map.CUT_MAP_RECT.x1 - 300)

        self.raw_image[region.prl_id] = merge
        cv2_utils.show_image(merge, win_name='region.prl_id')

    def screenshot_vertically(self, center):
        """
        垂直滚动地截取地图部分 然后拼接在一起
        :param center: 中心点
        :return: 拼接好的图片
        """
        img = []
        # 每秒往右拉一段距离截图
        for i in range(10):
            if not self.ctx.running:
                return
            screen = self.screenshot()
            map_part = cv2_utils.crop_image_only(screen, large_map.CUT_MAP_RECT)
            print(map_part.shape)
            cv2_utils.show_image(map_part, win_name='screenshot_vertically_map_part')
            if len(img) == 0 or not cv2_utils.is_same_image(img[len(img) - 1], map_part):
                img.append(map_part)
                self.ctx.controller.drag_to(end=Point(center.x, center.y - 200), start=center, duration=1)  # 往下拉一段
                time.sleep(1)
            else:
                break

        merge = img[0]
        for i in range(len(img)):
            if i == 0:
                merge = img[i]
            else:
                merge = cv2_utils.concat_vertically(merge, img[i])
        return merge

    def _do_save(self) -> OperationOneRoundResult:
        # 检测几个楼层是否大小一致
        shape = None
        lp, rp, tp, bp = None, None, None, None
        for l in [-1, 0, 1, 2, 3]:
            target_region = region_with_another_floor(self.region, l)
            if target_region is None:
                continue

            raw = self.raw_image[target_region.prl_id]
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
            raw = self.raw_image[target_region.prl_id]
            large_map.save_large_map_image(raw, target_region, 'raw')
            large_map.init_large_map(target_region, raw, self.ctx.im,
                                     expand_arr=[lp, rp, tp, bp], save=True)

        return Operation.round_success()


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
    # _init_map_for_sim_uni()
    # 执行前先传送到别的地图
    ctx = get_context()
    ctx.init_all(renew=True)
    r = map_const.P04_R05_F1
    app = LargeMapRecorder(ctx, r)
    app.execute()
