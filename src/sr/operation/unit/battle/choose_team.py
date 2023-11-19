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
    TEAM_1_RECT = Rect(620, 60, 700, 120)
    TEAM_2_RECT = Rect(720, 60, 830, 120)
    TEAM_3_RECT = Rect(860, 60, 940, 120)
    TEAM_4_RECT = Rect(980, 60, 1060, 120)
    TEAM_5_RECT = Rect(1110, 60, 1170, 120)
    TEAM_6_RECT = Rect(1230, 60, 1300, 120)

    TURN_ON_RECT = Rect(1590, 960, 1760, 1000)

    RECT_ARR = [
        TEAM_1_RECT, TEAM_2_RECT, TEAM_3_RECT,
        TEAM_4_RECT, TEAM_5_RECT, TEAM_6_RECT,
        TEAM_NUM_RECT
    ]

    def __init__(self, ctx: Context, team_num: int, on: bool = False):
        super().__init__(ctx, try_times=3, op_name=gt('选择配队', 'ui'))
        self.team_num: int = team_num
        self.on: bool = on

    def _execute_one_round(self) -> int:
        screen: MatLike = self.screenshot()

        for rect in ChooseTeam.RECT_ARR:
            part, _ = cv2_utils.crop_image(screen, rect)
            ocr_result = self.ctx.ocr.match_words(part, ['%d' % self.team_num])

            if len(ocr_result) == 0:
                continue

            result: MatchResult = ocr_result.popitem()[1].max
            to_click: Point = rect.left_top + result.center
            if self.ctx.controller.click(to_click):
                time.sleep(0.5)
                if self.ctx.controller.click(ChooseTeam.TURN_ON_RECT.center):
                    return Operation.SUCCESS

        time.sleep(1)
        return Operation.RETRY
