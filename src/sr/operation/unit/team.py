from typing import ClassVar, List, Optional, Union

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from sr.const.character_const import Character, CHARACTER_LIST
from sr.context import Context
from sr.image.sceenshot import screen_state
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
        screen = self.screenshot()  # _1702052217230
        character_id = self._get_character_id(screen)
        if character_id is not None:
            return Operation.round_success(character_id)

        return Operation.round_retry('无法匹配角色名称')

    def _get_character_id(self, screen: MatLike) -> Optional[str]:
        """
        获取对应的角色ID
        :param screen: 屏幕截图
        :return:
        """
        rect = GetTeamMemberInWorld.CHARACTER_NAME_RECT_LIST[self.character_num - 1]
        part, _ = cv2_utils.crop_image(screen, rect)

        character_name = self.ctx.ocr.ocr_for_single_line(part)
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


class SwitchMember(Operation):

    def __init__(self, ctx: Context, num: int,
                 skip_first_screen_check: bool = False):
        """
        切换角色 需要在大世界页面
        :param ctx:
        :param num: 第几个队友
        :param skip_first_screen_check: 是否跳过第一次画面状态检查
        """
        super().__init__(ctx, try_times=5, op_name='%s %d' % (gt('切换角色', 'ui'), num))
        self.num: int = num
        self.skip_first_screen_check: bool = skip_first_screen_check  # 是否跳过第一次的画面状态检查 用于提速
        self.first_screen_check: bool = True  # 是否第一次检查画面状态

    def _init_before_execute(self):
        super()._init_before_execute()
        self.first_screen_check = True

    def _execute_one_round(self) -> OperationOneRoundResult:
        first = self.first_screen_check
        self.first_screen_check = False
        if first and self.skip_first_screen_check:
            pass
        else:
            screen = self.screenshot()
            if not screen_state.is_normal_in_world(screen, self.ctx.im):
                return Operation.round_retry('未在大世界页面', wait=1)

        # TODO 未判断角色阵亡
        self.ctx.controller.switch_character(self.num)
        return Operation.round_success(wait=1)
