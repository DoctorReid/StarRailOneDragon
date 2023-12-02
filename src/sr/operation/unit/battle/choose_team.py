import time
from typing import ClassVar, List, Optional

from cv2.typing import MatLike

from basic import Rect, Point
from basic.i18_utils import gt
from basic.img import cv2_utils, MatchResult
from sr.context import Context
from sr.operation import Operation


class ChooseTeam(Operation):

    TEAM_NUM_RECT: ClassVar[Rect] = Rect(620, 60, 1330, 120)
    TEAM_1_RECT: ClassVar[Rect] = Rect(620, 60, 700, 120)
    TEAM_2_RECT: ClassVar[Rect] = Rect(720, 60, 830, 120)
    TEAM_3_RECT: ClassVar[Rect] = Rect(860, 60, 940, 120)
    TEAM_4_RECT: ClassVar[Rect] = Rect(980, 60, 1060, 120)
    TEAM_5_RECT: ClassVar[Rect] = Rect(1110, 60, 1170, 120)
    TEAM_6_RECT: ClassVar[Rect] = Rect(1230, 60, 1300, 120)

    TURN_ON_RECT: ClassVar[Rect] = Rect(1590, 960, 1760, 1000)  # 【启用】按钮

    RECT_ARR: ClassVar[List[Rect]] = [
        TEAM_1_RECT, TEAM_2_RECT, TEAM_3_RECT,
        TEAM_4_RECT, TEAM_5_RECT, TEAM_6_RECT,
        TEAM_NUM_RECT
    ]

    def __init__(self, ctx: Context, team_num: int, on: bool = False):
        """
        需要在配队管理页面使用 选择对应配队
        :param ctx: 上下文
        :param team_num: 队伍编号
        :param on: 是否需要点击【启用】
        """
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
                if not self.on:
                    return Operation.SUCCESS
                if self.ctx.controller.click(ChooseTeam.TURN_ON_RECT.center):
                    # 因为有可能本次选择配队没有改变队伍 即有可能不需要点启用 这里就偷懒不判断启用按钮是否出现了
                    return Operation.SUCCESS

        time.sleep(1)
        return Operation.RETRY
