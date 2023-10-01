import time

from cv2.typing import MatLike

from basic.img import MatchResult
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
        super().__init__(ctx, 5)
        self.scale: int = scale
        self.click_times = 0
        self.pos = None

    def run(self) -> int:
        if self.pos is None:
            self.pos = self.get_click_pos()

        if self.pos is not None:
            log.info('准备缩放地图 点击 (%d, %d) %s', self.pos.x, self.pos.y,
                     self.ctx.controller.click((self.pos.x, self.pos.y)))
            time.sleep(0.5)
            self.click_times += 1
            if self.click_times == abs(self.scale):
                return Operation.SUCCESS
            else:
                return Operation.WAIT
        else:
            return Operation.RETRY

    def get_click_pos(self) -> MatchResult:
        screen = self.ctx.controller.screenshot()
        template_id = 'plus' if self.scale > 0 else 'minus'
        x1, y1, x2, y2 = ScaleLargeMap.rect
        source = screen[y1:y2, x1:x2]
        result = self.ctx.im.match_template(source, template_id, template_type='origin')
        if result.max is not None:
            result.max.x += x1
            result.max.y += y1
        return result.max

    def on_resume(self):
        self.pos = self.get_click_pos()
        super().on_resume()
