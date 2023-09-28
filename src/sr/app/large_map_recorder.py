import time

import cv2

from basic.img import cv2_utils
from basic.log_utils import log
from sr import constants
from sr.app import Application
from sr.constants import get_planet_region_by_cn
from sr.context import Context, get_context
from sr.image.sceenshot.large_map import save_large_map_image
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

    def __init__(self, ctx: Context, planet_cn: str, region_cn: str):
        self.ctx: Context = ctx
        self.ops = [OpenMap(), ScaleLargeMap(-5), ChoosePlanet(planet_cn), ChooseRegion(planet_cn, region_cn)] # TODO 缺少一个缩小地图操作
        self.planet = get_planet_region_by_cn(planet_cn)
        self.region = get_planet_region_by_cn(region_cn)

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

        win: Window = self.ctx.controller.win
        rect: WinRect = win.get_win_rect()

        center = (rect.w // 2, rect.h // 2)
        self.ctx.controller.drag_to(end=(rect.w, rect.h), start=center, duration=1)  # 先拉到左上角
        time.sleep(0.5)
        img = []
        for i in range(10):
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
        self.convert_and_save(merge)
        cv2.waitKey(0)

    def screenshot_horizontally(self, center):
        """
        水平滚动地截取地图部分 然后拼接在一起
        :param center: 中心点
        :return: 拼接好的图片
        """
        img = []
        # 每秒往右拉一段距离截图
        for i in range(10):
            screen = self.ctx.controller.screenshot()
            map_part = screen[200: 900, 200: 1400]
            if len(img) == 0 or not cv2_utils.is_same_image(img[len(img) - 1], map_part):
                img.append(map_part)
                self.ctx.controller.drag_to(end=(center[0] - 200, center[1]), start=center, duration=1)  # 往右拉一段
                time.sleep(0.5)
            else:
                break

        merge = img[0]
        for i in range(len(img)):
            if i == 0:
                merge = img[i]
            else:
                merge = cv2_utils.concat_horizontally(merge, img[i])
        return merge

    def convert_and_save(self, origin):
        lm = self.ctx.map_cal.analyse_large_map(origin)
        cv2_utils.show_image(lm.gray, win_name='gray')
        cv2_utils.show_image(lm.mask, win_name='mask')
        save_large_map_image(origin, self.planet.id, self.region.id, 'origin')
        save_large_map_image(lm.gray, self.planet.id, self.region.id, 'gray')
        save_large_map_image(lm.mask, self.planet.id, self.region.id, 'mask')


if __name__ == '__main__':
    ctx = get_context()
    app = LargeMapRecorder(ctx, constants.P1_KZJ.cn, constants.R1_01_ZKCD.cn)
    app.run()