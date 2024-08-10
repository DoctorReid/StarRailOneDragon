from typing import ClassVar, List, Optional

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.const.character_const import Character, CHARACTER_LIST
from sr.context.context import Context
from sr.operation import Operation, OperationOneRoundResult


class GetTeamMemberInWorld(Operation):

    CHARACTER_NAME_RECT_LIST: ClassVar[List[Rect]] = [
        Rect(1655, 285, 1765, 330),
        Rect(1655, 385, 1765, 430),
        Rect(1655, 485, 1765, 530),
        Rect(1655, 585, 1765, 630),
    ]

    def __init__(self, ctx: Context, character_num: int):
        """
        需要在大世界 右侧显示4名角色头像时使用
        根据角色名 获取对应的角色
        :param ctx: 上下文
        :param character_num: 第几位角色 从1开始
        """
        super().__init__(ctx, op_name='%s %d' % (gt('组队角色判断', 'ui'), character_num))
        self.character_num: int = character_num

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        character_id = self._get_character_id(screen)
        if character_id is not None:
            return self.round_success(character_id)

        return self.round_retry('无法匹配角色名称')

    def _get_character_id(self, screen: MatLike) -> Optional[str]:
        """
        获取对应的角色ID
        :param screen: 屏幕截图
        :return:
        """
        rect = GetTeamMemberInWorld.CHARACTER_NAME_RECT_LIST[self.character_num - 1]
        part, _ = cv2_utils.crop_image(screen, rect)

        character_name = self.ctx.ocr.run_ocr_single_line(part)
        best_character: Optional[Character] = None
        best_lcs: Optional[int] = None
        for character in CHARACTER_LIST:
            lcs = str_utils.longest_common_subsequence_length(gt(character.cn, 'ocr'), character_name)
            if lcs == 0:
                continue
            if best_character is None or lcs > best_lcs:
                best_character = character
                best_lcs = lcs
        return best_character.id if best_character is not None else None
