from typing import ClassVar, List, Optional

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.const.character_const import Character, CHARACTER_LIST
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, OperationOneRoundResult, StateOperation, StateOperationNode, StateOperationEdge
from sr.screen_area import ScreenArea
from sr.screen_area.dialog import ScreenDialog
from sr.screen_area.screen_normal_world import ScreenNormalWorld


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

    def _init_before_execute(self):
        self.character_list = [None, None, None, None]

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        if not screen_state.is_normal_in_world(screen, self.ctx.im):
            return Operation.round_retry('未在大世界画面', wait=1)

        self._check_by_avatar(screen)
        self._check_by_name(screen)

        self.ctx.current_character_list = self.character_list
        log.info('当前配队 %s', [i.cn if i is not None else None for i in self.character_list])
        return Operation.round_success(data=self.character_list)

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


class SwitchMember(StateOperation):

    STATUS_CONFIRM: ClassVar[str] = '确认'

    def __init__(self, ctx: Context, num: int,
                 skip_first_screen_check: bool = False):
        """
        切换角色 需要在大世界页面
        :param ctx:
        :param num: 第几个队友 从1开始
        :param skip_first_screen_check: 是否跳过第一次画面状态检查
        """
        edges = []

        switch = StateOperationNode('切换', self._switch)
        confirm = StateOperationNode('确认', self._confirm)
        edges.append(StateOperationEdge(switch, confirm))

        wait = StateOperationNode('等待', self._wait_after_confirm)
        edges.append(StateOperationEdge(confirm, wait, status=SwitchMember.STATUS_CONFIRM))

        edges.append(StateOperationEdge(wait, switch))  # 复活后需要再按一次切换

        super().__init__(ctx, try_times=5,
                         op_name='%s %d' % (gt('切换角色', 'ui'), num),
                         edges=edges, specified_start_node=switch)

        self.num: int = num
        self.skip_first_screen_check: bool = skip_first_screen_check  # 是否跳过第一次的画面状态检查 用于提速
        self.first_screen_check: bool = True  # 是否第一次检查画面状态

    def _init_before_execute(self):
        super()._init_before_execute()
        self.first_screen_check = True

    def _switch(self) -> OperationOneRoundResult:
        first = self.first_screen_check
        self.first_screen_check = False
        if first and self.skip_first_screen_check:
            pass
        else:
            screen = self.screenshot()
            if not screen_state.is_normal_in_world(screen, self.ctx.im):
                return Operation.round_retry('未在大世界页面', wait=1)

        self.ctx.controller.switch_character(self.num)
        return Operation.round_success(wait=1)

    def _confirm(self) -> OperationOneRoundResult:
        """
        复活确认
        :return:
        """
        screen = self.screenshot()
        if screen_state.is_normal_in_world(screen, self.ctx.im):  # 无需复活
            return Operation.round_success()

        if self.find_area(ScreenDialog.FAST_RECOVER_NO_CONSUMABLE.value, screen):
            area = ScreenDialog.FAST_RECOVER_CANCEL.value
        else:
            area = ScreenDialog.FAST_RECOVER_CONFIRM.value

        click = self.find_and_click_area(area, screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(area.status, wait=1)
        else:
            return Operation.round_retry('点击%s失败' % area.status, wait=1)

    def _wait_after_confirm(self) -> OperationOneRoundResult:
        """
        等待回到大世界画面
        :return:
        """
        screen = self.screenshot()
        if screen_state.is_normal_in_world(screen, self.ctx.im):
            return Operation.round_success()
        else:
            return Operation.round_retry('未在大世界画面', wait=1)
