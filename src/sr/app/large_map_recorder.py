import time

from basic import Point
from basic.img import cv2_utils
from basic.log_utils import log
from sr.app import Application
from sr.const import map_const
from sr.const.map_const import Region, region_with_another_floor
from sr.context import Context, get_context
from sr.image.sceenshot import large_map
from sr.operation import Operation
from sr.operation.unit.choose_planet import ChoosePlanet
from sr.operation.unit.choose_region import ChooseRegion
from sr.operation.unit.open_map import OpenMap
from sr.operation.unit.scale_large_map import ScaleLargeMap
from sr.win import Window, WinRect


class LargeMapRecorder(Application):
    """
    开发用的截图工具 只支持PC版
    把整个大地图记录下来
    """

    def __init__(self, ctx: Context, region: Region):
        super().__init__(ctx)
        self.planet = region.planet
        self.region = region

    def _execute_one_round(self) -> bool:
        """
        先拉到最左上角 然后一行一行地截图 最后再拼接起来。
        多层数的话需要一次性先将所有楼层截图再处理 保证各楼层大小一致
        :return:
        """
        region_list = []
        for l in [-1, 0, 1, 2, 3]:
            region = region_with_another_floor(self.region, l)
            if region is not None:
                region_list.append(region)

        raw_img = {}

        ops = [OpenMap(ctx), ScaleLargeMap(ctx, -5)]
        if not self.run_ops(ops):
            return False

        for region in region_list:
            ops = [ChoosePlanet(ctx, region.planet), ChooseRegion(ctx, region)]
            if not self.run_ops(ops):
                return False

            win: Window = self.ctx.controller.win
            rect: WinRect = win.get_win_rect()

            center = Point(rect.w // 2, rect.h // 2)
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
                else:
                    break

            merge = img[0]
            for i in range(len(img)):
                if i == 0:
                    merge = img[i]
                else:
                    merge = cv2_utils.concat_vertically(merge, img[i], decision_height=large_map.CUT_MAP_RECT.y2 - large_map.CUT_MAP_RECT.y1 - 300)

            raw_img[region.prl_id] = merge
            cv2_utils.show_image(merge, win_name='region.prl_id')

        # 检测几个楼层是否大小一致
        shape = None
        lp, rp, tp, bp = None, None, None, None
        for region in region_list:
            raw = raw_img[region.prl_id]
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

        for region in region_list:
            raw = raw_img[region.prl_id]
            large_map.save_large_map_image(raw, region, 'raw')
            large_map.init_large_map(region, raw, self.ctx.im,
                                     expand_arr=[lp, rp, tp, bp], save=True)

        return Operation.SUCCESS

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
            map_part, _ = cv2_utils.crop_image(screen, large_map.CUT_MAP_RECT)
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

    def run_ops(self, ops) -> bool:
        for op in ops:
            if not op.execute().success:
                log.error('前置打开地图失败')
                return False
        return True


if __name__ == '__main__':
    # 执行前先传送到别的地图
    ctx = get_context()
    ctx.init_all(renew=True)
    r = map_const.P01_R05_L1
    app = LargeMapRecorder(ctx, r)
    app.execute()
