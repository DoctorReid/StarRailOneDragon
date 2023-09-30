import time

from cv2.typing import MatLike

from basic.log_utils import log
from sr.context import Context, get_context
from sr.control import GameController
from sr.image import ImageMatcher
from sr.operation import Operation


class ScaleLargeMap(Operation):

    rect = (600, 960, 1040, 1020)

    def __init__(self, ctx: Context, scale: int):
        """
        默认在大地图页面 点击缩放按钮
        :param scale: 缩放次数。负数为缩小，正数为放大
        """
        self.ctx = ctx
        self.scale: int = scale

    def execute(self) -> bool:
        try_times = 0

        while self.ctx.running and try_times < 5:
            if not self.ctx.running:
                return False
            try_times += 1
            screen = self.ctx.controller.screenshot()
            if self.click_scale(screen, self.ctx):
                return True

        return False

    def click_scale(self, screen: MatLike, ctx: Context) -> bool:
        ctrl: GameController = ctx.controller
        im: ImageMatcher = ctx.im
        template_id = 'plus' if self.scale > 0 else 'minus'
        x1, y1, x2, y2 = ScaleLargeMap.rect
        source = screen[y1:y2, x1:x2]
        result = im.match_template(source, template_id, template_type='origin')
        if len(result) > 0:
            for _ in range(abs(self.scale)):
                if not ctx.running:
                    return False
                x, y = result.max.x + x1, result.max.y + y1
                log.info('准备缩放地图 点击 (%d, %d) %s', x, y, ctrl.click((x, y)))
                time.sleep(0.5)
            return True

        return False
