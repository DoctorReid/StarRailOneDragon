import time

from cv2.typing import MatLike

from basic import Rect, Point
from basic.i18_utils import gt
from basic.img import cv2_utils, MatchResult
from sr.context import Context
from sr.operation import Operation


class ChooseTeam(Operation):

    """
    选择配队
    """

    TEAM_NUM_RECT = Rect(620, 60, 1330, 120)

    def __init__(self, ctx: Context, team_num: int):
        super().__init__(ctx, try_times=3, op_name=gt('选择配队', 'ui'))
        self.team_num: int = team_num

    def _execute_one_round(self) -> int:
        screen: MatLike = self.screenshot()

        part, _ = cv2_utils.crop_image(screen, ChooseTeam.TEAM_NUM_RECT)
        ocr_result = self.ctx.ocr.match_words(part, ['%d' % self.team_num])

        if len(ocr_result) == 0:
            time.sleep(1)
            return Operation.RETRY

        result: MatchResult = ocr_result.popitem()[1].max
        to_click: Point = ChooseTeam.TEAM_NUM_RECT.left_top + result.center
        if self.ctx.controller.click(to_click):
            return Operation.SUCCESS
        else:
            return Operation.RETRY
