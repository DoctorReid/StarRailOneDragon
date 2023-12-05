import time
from typing import Callable, Union, ClassVar, Optional, List

import cv2
import numpy as np
from cv2.typing import MatLike
from pydantic import BaseModel

from basic import Rect
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.img.os import get_debug_image
from basic.log_utils import log
from sr.const.character_const import CharacterCombatType, CHARACTER_COMBAT_TYPE_LIST, Character
from sr.context import Context, get_context
from sr.operation import Operation, OperationOneRoundResult
from sr.operation.combine import CombineOperation
from sr.operation.unit.click import Click
from sr.operation.unit.forgotten_hall.choose_character import ChooseCharacterInForgottenHall


class SessionInfo(BaseModel):  # 关卡的信息

    num: int
    """关卡编码"""

    combat_type_rect_list: List[Rect]
    """属性框"""

    character_rect_list: List[Rect]
    """角色框"""


class ChooseTeamInForgottenHall(Operation):

    SESSION_1: ClassVar[SessionInfo] = SessionInfo(
        num=1,
        combat_type_rect_list=[
            Rect(1100, 720, 1145, 770),
            Rect(1135, 720, 1180, 770),
            Rect(1170, 720, 1215, 770),
        ],
        character_rect_list=[
            Rect(1380, 695, 1455, 765),
            Rect(1480, 695, 1555, 765),
            Rect(1580, 695, 1655, 765),
            Rect(1680, 695, 1755, 765),
        ]
    )

    SESSION_2: ClassVar[SessionInfo] = SessionInfo(
        num=2,
        combat_type_rect_list=[
            Rect(1100, 820, 1145, 870),
            Rect(1135, 820, 1180, 870),
            Rect(1170, 820, 1215, 870),
        ],
        character_rect_list=[
            Rect(1380, 795, 1455, 870),
            Rect(1480, 795, 1555, 870),
            Rect(1580, 795, 1655, 870),
            Rect(1680, 795, 1755, 870),
        ]
    )

    ALL_SESSION_LIST: ClassVar[List[SessionInfo]] = [SESSION_1, SESSION_2]

    def __init__(self, ctx: Context, cal_team_member_func: Callable):
        """
        需要已经在
        :param ctx:
        :param cal_team_member_func:
        """
        super().__init__(ctx, op_name=gt('忘却之庭配队', 'ui'))
        self.cal_team_func: Callable = cal_team_member_func
        self.phase: int = 0
        self.teams: List[List[Character]] = []

    def _execute_one_round(self) -> OperationOneRoundResult:
        if self.phase == 0:  # 按照BOSS属性计算配队
            if self._cal_team_member():
                self.phase += 1
                return Operation.round_wait()
            else:
                time.sleep(1)
                return Operation.round_retry('cal_team_fail')
        elif self.phase == 1:  # 取消原有的角色选择
            if self._cancel_all_chosen():
                self.phase += 1
                return Operation.round_wait()
            else:
                return Operation.round_retry('cancel_all_fail')
        elif self.phase == 2:  # 选择配队:
            if self._choose_character():
                self.phase += 1
                return Operation.round_success()
            else:
                return Operation.round_retry('choose_team_fail')

        return Operation.round_retry('unknown')

    def _cal_team_member(self) -> bool:
        """
        按照BOSS属性计算配队
        :return:
        """
        screen: MatLike = self.screenshot()
        combat_type_in_session = []
        for session in ChooseTeamInForgottenHall.ALL_SESSION_LIST:
            combat_types = []
            for rect in session.combat_type_rect_list:
                t = self._get_boss_combat_type(screen, rect)
                if t is not None:
                    combat_types.append(t)
            combat_type_in_session.append(combat_types)

        self.teams = self.cal_team_func(combat_type_in_session)
        if self.teams is None:
            return False
        for t in self.teams:
            if t is None:
                return False

        return True

    def _get_boss_combat_type(self, screen: MatLike, rect: Rect) -> Optional[CharacterCombatType]:
        """
        获取BOSS对应的属性
        :param screen: 屏幕截图
        :param rect: 属性区域
        :return:
        """
        part, _ = cv2_utils.crop_image(screen, rect)

        gray = cv2.cvtColor(part, cv2.COLOR_BGR2GRAY)
        _, bw = cv2.threshold(gray, np.mean(gray), 255, cv2.THRESH_BINARY)
        bw = cv2_utils.connection_erase(bw)
        origin, mask = cv2_utils.convert_to_standard(part, bw, width=55, height=55, bg_color=(0, 0, 0))  # 扣出属性图标
        source_kps, source_desc = cv2_utils.feature_detect_and_compute(origin, mask)

        for t in CHARACTER_COMBAT_TYPE_LIST:
            template = self.ctx.ih.get_character_combat_type(t.id)
            if template is None:
                log.error('找不到属性模板 %s', t.id)
                continue

            pos = cv2_utils.feature_match_for_one(
                source_kps, source_desc,
                template.kps, template.desc,
                template.origin.shape[1], template.origin.shape[0],
                source_mask=mask,
                knn_distance_percent=0.7)

            if pos is not None:
                return t

            # result_list = self.ctx.im.match_template(origin, t.id, template_sub_dir='character_combat_type')
            # if len(result_list) > 0:
            #     return t

        return None

    def _cancel_all_chosen(self) -> bool:
        """
        取消原有的所有选择
        :return:
        """
        for session in ChooseTeamInForgottenHall.ALL_SESSION_LIST:
            for rect in session.character_rect_list:
                if not self.ctx.controller.click(rect.center):
                    return False
                time.sleep(0.2)
        return True

    def _choose_character(self) -> bool:
        ops: List[Operation] = []

        idx: int = -1
        for session in ChooseTeamInForgottenHall.ALL_SESSION_LIST:
            idx += 1
            team = self.teams[idx]
            ops.append(Click(self.ctx, session.character_rect_list[0].center))
            for character in team:
                ops.append(ChooseCharacterInForgottenHall(self.ctx, character.id))
        op = CombineOperation(
            self.ctx,
            ops=ops
        )
        return op.execute().success


if __name__ == '__main__':
    ctx = get_context()
    ctx.init_image_matcher()

    op = ChooseTeamInForgottenHall(ctx, None)

    screen = get_debug_image('_1701098324039')
    print(op._get_boss_combat_type(screen, ChooseTeamInForgottenHall.SESSION_2_COMBAT_TYPE_1_RECT))