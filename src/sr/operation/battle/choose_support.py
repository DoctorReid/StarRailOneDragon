from typing import Optional, ClassVar, List

from cv2.typing import MatLike

from basic import Rect, Point
from basic.i18_utils import gt
from basic.img import cv2_utils, MatchResult
from basic.log_utils import log
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult, StateOperation, StateOperationEdge, StateOperationNode
from sr.screen_area.screen_team import ScreenTeam


class ChooseSupport(StateOperation):

    STATUS_SUPPORT_NOT_FOUND: ClassVar[str] = '未找到支援角色'
    STATUS_SUPPORT_NEEDED: ClassVar[str] = '需要支援角色'

    def __init__(self, ctx: Context, character_id: Optional[str]):
        """
        需要在管理配队页面使用 选择对应支援角色
        如果不传入支援角色 则直接返回成功
        :param ctx:
        :param character_id:
        """
        edges: List[StateOperationEdge] = []

        wait = StateOperationNode('等待画面加载', self._wait)

        click_support = StateOperationNode('点击支援', self._click_support)
        edges.append(StateOperationEdge(wait, click_support, status=ChooseSupport.STATUS_SUPPORT_NEEDED))

        click_avatar = StateOperationNode('点击头像', self._click_avatar)
        edges.append(StateOperationEdge(click_support, click_avatar))

        click_join = StateOperationNode('点击入队', self._click_join)
        edges.append(StateOperationEdge(click_avatar, click_join))

        wait2 = StateOperationNode('选择后等待画面加载', self._wait)
        edges.append(StateOperationEdge(click_join, wait2))
        edges.append(StateOperationEdge(click_avatar, wait2, success=False))

        super().__init__(ctx, try_times=10,
                         op_name=gt('选择支援', 'ui'),
                         edges=edges
                         )

        self.character_id: Optional[str] = character_id
        self.no_find_character_times: int = 0

    def _init_before_execute(self):
        super()._init_before_execute()
        self.no_find_character_times: int = 0

    def _wait(self) -> OperationOneRoundResult:
        """
        等待加载 左上角有【队伍】
        :return:
        """
        area = ScreenTeam.TEAM_TITLE.value
        if self.find_area(area):
            if self.character_id is None:
                return self.round_success()
            else:
                return self.round_success(ChooseSupport.STATUS_SUPPORT_NEEDED)
        else:
            return self.round_retry('未在%s画面' % area.status, wait=1)

    def _click_support(self) -> OperationOneRoundResult:
        """
        点击支援按钮
        :return:
        """
        area = ScreenTeam.SUPPORT_BTN.value
        click = self.find_and_click_area(area)
        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(wait=1)
        else:
            return self.round_retry('点击%s失败' % area.status, wait=1)

    def _click_avatar(self) -> OperationOneRoundResult:
        """
        点击头像
        :return:
        """
        screen = self.screenshot()
        pos = self._get_character_pos(screen)

        if pos is None:
            self.no_find_character_times += 1
            if self.no_find_character_times >= 5:
                # 找不到支援角色 点击右边返回 按特殊状态返回成功
                self.ctx.controller.click(ScreenTeam.SUPPORT_CLOSE.value.rect.center)
                return self.round_fail(ChooseSupport.STATUS_SUPPORT_NOT_FOUND, wait=1.5)

            drag_from = ScreenTeam.SUPPORT_CHARACTER_LIST.value.rect.center
            drag_to = drag_from + Point(0, -400)
            self.ctx.controller.drag_to(drag_to, drag_from)
            return self.round_retry(ChooseSupport.STATUS_SUPPORT_NOT_FOUND, wait=2)
        else:
            click = self.ctx.controller.click(pos.center)
            if click:
                return self.round_success(wait=0.5)
            else:
                return self.round_retry('点击头像失败', wait=0.5)

    def _click_join(self) -> OperationOneRoundResult:
        """
        点击入队
        :return:
        """
        area = ScreenTeam.SUPPORT_JOIN.value
        click = self.find_and_click_area(area)
        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(wait=1)
        else:
            return self.round_retry('点击%s失败' % area.status, wait=1)

    def _get_character_pos(self, screen: Optional[MatLike] = None) -> Optional[MatchResult]:
        """
        找到角色头像的位置
        :return:
        """
        if screen is None:
            screen: MatLike = self.screenshot()

        area = ScreenTeam.SUPPORT_CHARACTER_LIST.value
        part = cv2_utils.crop_image_only(screen, area.rect)

        # 先找到UID的位置
        ocr_result_map = self.ctx.ocr.match_words(part, words=['等级'], lcs_percent=0.1)
        if len(ocr_result_map) == 0:
            log.error('找不到等级')
            return None

        template = self.ctx.ih.get_character_avatar_template(self.character_id)
        if template is None:
            log.error('找不到角色头像模板 %s', self.character_id)
            return None

        for k, v in ocr_result_map.items():
            for pos in v:
                center = area.rect.left_top + pos.center
                avatar_rect = Rect(center.x - 42, center.y - 100, center.x + 55, center.y - 10)
                avatar_part = cv2_utils.crop_image_only(screen, avatar_rect)
                # cv2_utils.show_image(avatar_part, wait=0)
                source_kps, source_desc = cv2_utils.feature_detect_and_compute(avatar_part)

                character_pos = cv2_utils.feature_match_for_one(
                    source_kps, source_desc,
                    template.kps, template.desc,
                    template.origin.shape[1], template.origin.shape[0],
                    knn_distance_percent=0.5
                )

                if character_pos is not None:
                    character_pos.x += avatar_rect.left_top.x
                    character_pos.y += avatar_rect.left_top.y
                    return character_pos

        return None
