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


class ChooseCharacterInForgottenHall(Operation):

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
                return Operation.round_retry('点击头像失败')
        else:
            drag_from = ChooseCharacterInForgottenHall.CHARACTER_LIST_RECT.center
            drag_to = drag_from + (Point(0, -200) if self.op_round % 2 == 0 else Point(0, 200))
            self.ctx.controller.drag_to(drag_to, drag_from)
            return Operation.round_retry('找不到对应头像')

    def _get_character_pos(self, screen: Optional[MatLike] = None) -> Optional[MatchResult]:
        """
        获取目标角色的位置
        :param screen: 游戏截图
        :return: 位置
        """
        if screen is None:
            screen: MatLike = self.screenshot()
        part, _ = cv2_utils.crop_image(screen, ChooseCharacterInForgottenHall.CHARACTER_LIST_RECT)

        template = self.ctx.ih.get_character_avatar_template(self.character.id)
        if template is None:
            log.error('找不到角色头像模板 %s', self.character.id)
            return None

        source_kps, source_desc = cv2_utils.feature_detect_and_compute(part)
        character_pos = cv2_utils.feature_match_for_one(
            source_kps, source_desc,
            template.kps, template.desc,
            template.origin.shape[1], template.origin.shape[0],
            knn_distance_percent=0.5
        )

        if character_pos is not None:
            character_pos.x += ChooseCharacterInForgottenHall.CHARACTER_LIST_RECT.left_top.x
            character_pos.y += ChooseCharacterInForgottenHall.CHARACTER_LIST_RECT.left_top.y
            return character_pos

        return None


if __name__ == '__main__':
    # ctx = get_context()
    # ctx.init_image_matcher()
    ih = ImageHolder()
    screen = get_debug_image('5')
    # part, _ = cv2_utils.crop_image(screen, CHARACTER_RECT)
    source_kps, source_desc = cv2_utils.feature_detect_and_compute(screen)
    template = ih.get_character_avatar_template('danhengimbibitorlunae')
    source_kps, source_desc = cv2_utils.feature_detect_and_compute(screen)
    template_kps, template_desc = cv2_utils.feature_detect_and_compute(template.origin)
    good_matches, offset_x, offset_y, scale = cv2_utils.feature_match(source_kps, source_desc, template_kps, template_desc, None)

    if offset_x is not None:
        template_w = template.origin.shape[1]
        template_h = template.origin.shape[0]
        # 小地图缩放后的宽度和高度
        scaled_width = int(template_w * scale)
        scaled_height = int(template_h * scale)

        result = MatchResult(1, offset_x, offset_y, scaled_width, scaled_height, template_scale=scale)
        print(result)

        cv2_utils.show_image(screen, result, win_name='screen', wait=0)

    # op = ChooseCharacter(ctx, DANHENGIMBIBITORLUNAE)
    #
    # op._get_character_pos(screen)