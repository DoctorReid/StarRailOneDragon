from typing import Optional, ClassVar

from cv2.typing import MatLike

from basic import Rect, Point
from basic.i18_utils import gt
from basic.img import MatchResult, cv2_utils
from basic.img.os import get_debug_image
from basic.log_utils import log
from sr.const import character_const
from sr.const.character_const import Character
from sr.context import Context
from sr.image.image_holder import ImageHolder
from sr.operation import Operation, OperationOneRoundResult


class TlChooseCharacter(Operation):

    CHARACTER_LIST_RECT: ClassVar[Rect] = Rect(40, 140, 560, 930)

    def __init__(self, ctx: Context, character_id: str):
        """
        需要已经在选择配队的页面
        在左方列表点击角色
        :param ctx: 上下文
        :param character_id: 角色ID
        """
        self.character: Character = character_const.get_character_by_id(character_id)
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('选择角色', 'ui'), gt(self.character.cn, 'ui')))

    def _execute_one_round(self) -> OperationOneRoundResult:
        pos = self._get_character_pos()
        if pos is not None:
            if self.ctx.controller.click(pos.center):
                return Operation.round_success()
            else:
                return Operation.round_retry('点击头像失败', wait=1)
        else:
            drag_from = TlChooseCharacter.CHARACTER_LIST_RECT.center
            drag_to = drag_from + (Point(0, -300) if self.op_round % 2 == 0 else Point(0, 300))
            self.ctx.controller.drag_to(drag_to, drag_from)
            return Operation.round_retry('找不到对应头像', wait=1)

    def _get_character_pos(self, screen: Optional[MatLike] = None) -> Optional[MatchResult]:
        """
        获取目标角色的位置
        :param screen: 游戏截图
        :return: 位置
        """
        if screen is None:
            screen: MatLike = self.screenshot()
        part, _ = cv2_utils.crop_image(screen, TlChooseCharacter.CHARACTER_LIST_RECT)

        template = self.ctx.ih.get_character_avatar_template(self.character.id)
        if template is None:
            log.error('找不到角色头像模板 %s', self.character.id)
            return None

        source_kps, source_desc = cv2_utils.feature_detect_and_compute(part)
        character_pos = cv2_utils.feature_match_for_one(
            source_kps, source_desc,
            template.kps, template.desc,
            template.origin.shape[1], template.origin.shape[0],
            knn_distance_percent=0.4
        )

        if character_pos is not None:
            character_pos.x += TlChooseCharacter.CHARACTER_LIST_RECT.left_top.x
            character_pos.y += TlChooseCharacter.CHARACTER_LIST_RECT.left_top.y
            return character_pos

        return None
