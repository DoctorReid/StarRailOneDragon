from typing import List, Optional

from cv2.typing import MatLike

from basic import str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.const.character_const import Character, CHARACTER_LIST
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult
from sr.screen_area import ScreenArea
from sr.screen_area.screen_normal_world import ScreenNormalWorld


class CheckTeamMembersInWorld(Operation):

    def __init__(self, ctx: Context):
        """
        需要在大世界 右侧显示4名角色头像时使用
        获取组队角色
        :param ctx: 上下文
        """
        super().__init__(ctx, try_times=5,
                         op_name=gt('组队角色判断', 'ui'))

        self.character_list: List[Character] = []

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        self.character_list = [None, None, None, None]

        return None

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        if not screen_state.is_normal_in_world(screen, self.ctx.im):
            return self.round_retry('未在大世界画面', wait=1)

        self._check_by_name(screen)
        self._check_by_avatar(screen)

        self.ctx.team_info.update_character_list(self.character_list)
        log.info('当前配队 %s', [i.cn if i is not None else None for i in self.character_list])
        return self.round_success(data=self.character_list)

    def _check_by_name(self, screen: MatLike):
        """
        用名字匹配
        :param screen:
        :return:
        """
        area_list = [
            ScreenNormalWorld.TEAM_MEMBER_NAME_1.value,
            ScreenNormalWorld.TEAM_MEMBER_NAME_2.value,
            ScreenNormalWorld.TEAM_MEMBER_NAME_3.value,
            ScreenNormalWorld.TEAM_MEMBER_NAME_4.value,
        ]
        for i in range(4):
            if self.character_list[i] is not None:
                continue
            area: ScreenArea = area_list[i]

            part = cv2_utils.crop_image_only(screen, area.rect)

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

            self.character_list[i] = best_character

    def _check_by_avatar(self, screen: MatLike):
        """
        用头像匹配
        :param screen:
        :return:
        """
        area_list = [
            ScreenNormalWorld.TEAM_MEMBER_AVATAR_1.value,
            ScreenNormalWorld.TEAM_MEMBER_AVATAR_2.value,
            ScreenNormalWorld.TEAM_MEMBER_AVATAR_3.value,
            ScreenNormalWorld.TEAM_MEMBER_AVATAR_4.value,
        ]

        for i in range(4):
            if self.character_list[i] is not None:
                continue
            area: ScreenArea = area_list[i]

            part = cv2_utils.crop_image_only(screen, area.rect)
            source_kps, source_desc = cv2_utils.feature_detect_and_compute(part)

            for character in CHARACTER_LIST:
                template = self.ctx.ih.get_character_avatar_template(character.id)

                if template is None:
                    log.error('%s 角色头像文件缺失 请下载最新的images.zip 更新', character.cn)
                    continue

                mr = cv2_utils.feature_match_for_one(source_kps, source_desc,
                                                     template.kps, template.desc,
                                                     template.origin.shape[1], template.origin.shape[0])

                if mr is not None:
                    self.character_list[i] = character
                    break
