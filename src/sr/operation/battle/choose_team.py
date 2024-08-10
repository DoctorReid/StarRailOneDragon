import time
from typing import ClassVar, Optional

import cv2
from cv2.typing import MatLike

from basic import Rect, Point, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.context.context import Context
from sr.image.sceenshot.screen_state import in_secondary_ui
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.operation import Operation, OperationOneRoundResult


class ChooseTeam(Operation):

    TEAM_NUM_RECT: ClassVar[Rect] = Rect(505, 40, 1380, 105)  # 配队号码
    TURN_ON_RECT: ClassVar[Rect] = Rect(1590, 960, 1760, 1000)  # 【启用】按钮

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

    def _execute_one_round(self) -> OperationOneRoundResult:
        if self.team_num == 0:
            return self.round_success()

        screen: MatLike = self.screenshot()

        if not self.in_secondary_ui(screen):
            return self.round_retry('未在配队页面', wait=1)

        num_pos = self.get_all_num_pos(screen)

        if self.team_num not in num_pos:
            with_larger: bool = False  # 是否有存在比目标数字大的
            for num in num_pos.keys():
                if num > self.team_num:
                    with_larger = True
                    break

            drag_from = ChooseTeam.TEAM_NUM_RECT.center
            drag_to = drag_from + (Point(200, 0) if with_larger else Point(-200, 0))
            self.ctx.controller.drag_to(drag_to, drag_from)

            return self.round_retry('未找到配队', wait=0.5)
        else:
            to_click: Point = num_pos[self.team_num]
            if self.ctx.controller.click(to_click):
                time.sleep(0.5)
                if not self.on:
                    return self.round_success()
                if self.ctx.controller.click(ChooseTeam.TURN_ON_RECT.center):
                    # 因为有可能本次选择配队没有改变队伍 即有可能不需要点启用 这里就偷懒不判断启用按钮是否出现了
                    return self.round_success()

            return self.round_retry('点击配队失败')

    def in_secondary_ui(self, screen: Optional[MatLike] = None) -> bool:
        """
        是否在组队的界面
        :param screen: 屏幕截图
        :return:
        """
        if screen is None:
            screen = self.screenshot()

        return in_secondary_ui(screen, self.ctx.ocr, ScreenState.TEAM.value)

    def get_all_num_pos(self, screen: Optional[MatLike] = None) -> dict[int, Point]:
        """
        获取所有数字的位置
        :param screen: 屏幕截图
        :return:
        """
        if screen is None:
            screen = self.screenshot()

        part, _ = cv2_utils.crop_image(screen, ChooseTeam.TEAM_NUM_RECT)
        mask1 = cv2.inRange(part, (185, 225, 250), (195, 235, 255))
        mask2 = cv2.inRange(part, (135, 135, 135), (165, 165, 165))
        mask = cv2.bitwise_or(mask1, mask2)
        # cv2_utils.show_image(mask1, win_name='mask1')
        # cv2_utils.show_image(mask2, win_name='mask2')
        # cv2_utils.show_image(mask, win_name='get_all_num_pos', wait=0)

        to_ocr = cv2.bitwise_or(part, part, mask=mask)
        ocr_map = self.ctx.ocr.run_ocr(to_ocr)

        team_num_pos: dict[int, Point] = {}

        for word, mrl in ocr_map.items():
            if mrl.max is None:
                continue
            team_num = str_utils.get_positive_digits(word, err=None)
            if team_num is None:
                continue

            team_num_pos[team_num] = mrl.max.center + ChooseTeam.TEAM_NUM_RECT.left_top

        return team_num_pos
