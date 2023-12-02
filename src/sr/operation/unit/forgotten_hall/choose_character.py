from typing import Optional

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import Rect
from basic.i18_utils import gt
from basic.img import MatchResult, cv2_utils
from basic.img.os import get_debug_image
from sr.image.image_holder import ImageHolder

# from sr.const.character_const import Character, DANHENGIMBIBITORLUNAE
# from sr.context import Context
# from sr.operation import Operation, OperationOneRoundResult
#
#
# CHARACTER_RECT = Rect(40, 140, 560, 930)
#
#
# class ChooseCharacter(Operation):
#
#     def __init__(self, ctx: Context, character: Character):
#         super().__init__(ctx, try_times=5,
#                          op_name='%s %s' % (gt('选择角色', 'ui'), gt(character.cn, 'ui')))
#         self.character: Character = character
#
#     def _execute_one_round(self) -> OperationOneRoundResult:
#         screen: MatLike = self.screenshot()
#
#     def _get_character_pos(self, screen: MatLike) -> Optional[MatchResult]:
#         """
#         获取目标角色的位置
#         :param screen: 游戏截图
#         :return: 位置
#         """
#         part, _ = cv2_utils.crop_image(screen, CHARACTER_RECT)
#
#         match_result_list = self.ctx.im.match_template(part, self.character.id,
#                                                        template_sub_dir='character_avatar',
#                                                        ignore_template_mask=True)
#         match_result: MatchResult = match_result_list.max
#
#         if match_result is None:
#             return None
#
#         cv2_utils.show_image(part, match_result_list, win_name='_get_character_pos', wait=0)
#
#         lt = CHARACTER_RECT.left_top
#         match_result.x += lt.x
#         match_result.y += lt.y
#
#         return match_result


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