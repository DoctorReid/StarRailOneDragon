import os
import time

import cv2

from basic.img import cv2_utils
from basic.log_utils import log
from sr import constants
from sr.app import Application
from sr.constants.map import Region
from sr.context import Context, get_context
from sr.image.sceenshot import large_map, LargeMapInfo
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
        self.ctx: Context = ctx
        self.ops = [OpenMap(ctx), ScaleLargeMap(ctx, -5), ChoosePlanet(ctx, region.planet), ChooseRegion(ctx, region)]
        self.planet = region.planet
        self.region = region

    def run(self) -> bool:
        """
        先拉到最左上角
        然后一行一行地截图 最后再拼接起来
        :return:
        """
        self.ctx.running = True
        self.ctx.controller.init()
        for op in self.ops:
            r = op.execute()
            if not r:
                log.error('前置打开地图失败')
                return False
            else:
                log.info('完成步骤')

        win: Window = self.ctx.controller.win
        rect: WinRect = win.get_win_rect()

        center = (rect.w // 2, rect.h // 2)
        self.ctx.controller.drag_to(end=(rect.w, rect.h), start=center, duration=1)  # 先拉到左上角
        time.sleep(0.5)
        img = []
        for i in range(10):
            if not self.ctx.running:
                return False
            row_img = self.screenshot_horizontally(center)  # 对一行进行水平的截图
            cv2_utils.show_image(row_img, win_name='row %d' % i)
            if len(img) == 0 or not cv2_utils.is_same_image(img[len(img) - 1], row_img):
                img.append(row_img)
                self.ctx.controller.drag_to(end=(center[0], center[1] - 200), start=center, duration=1)  # 往下拉一段
                time.sleep(0.5)
                self.ctx.controller.drag_to(end=(rect.w, center[1]), start=center, duration=1)  # 往左拉到尽头
                time.sleep(0.5)
            else:
                break

        merge = img[0]
        for i in range(len(img)):
            if i == 0:
                merge = img[i]
            else:
                merge = cv2_utils.concat_vertically(merge, img[i])

        cv2_utils.show_image(merge, win_name='final')
        large_map.init_large_map(self.region, merge, self.ctx.im, save=True)

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
            screen = self.ctx.controller.screenshot()
            map_part = cv2_utils.crop_image(screen, large_map.CUT_MAP_RECT)
            cv2_utils.show_image(map_part, win_name='screenshot_horizontally_map_part')
            if len(img) == 0 or not cv2_utils.is_same_image(img[len(img) - 1], map_part):
                img.append(map_part)
                self.ctx.controller.drag_to(end=(center[0] - 200, center[1]), start=center, duration=1)  # 往右拉一段
                time.sleep(1)
            else:
                break

        merge = img[0]
        for i in range(len(img)):
            if i == 0:
                merge = img[i]
            else:
                merge = cv2_utils.concat_horizontally(merge, img[i], decision_width=large_map.CUT_MAP_RECT[2] - large_map.CUT_MAP_RECT[0] - 300)
        return merge


if __name__ == '__main__':
    # 执行前先传送到别的地图
    ctx = get_context()
    r = constants.map.P02_R02
    app = LargeMapRecorder(ctx, r)
    app.run()
