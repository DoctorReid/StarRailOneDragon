import time
from typing import ClassVar, Optional, List

from cv2.typing import MatLike

from basic import Rect, str_utils, Point
from basic.i18_utils import gt
from basic.img import cv2_utils, MatchResult
from basic.log_utils import log
from sr.const.traing_mission_const import DailyTrainingMission, ALL_MISSION_LIST
from sr.context import Context
from sr.operation import Operation, OperationOneRoundResult


class GetTrainingUnfinishedMission(Operation):

    GO_RECT: ClassVar[Rect] = Rect(280, 780, 1660, 880)

    def __init__(self, ctx: Context, ignore_missions: Optional[List[str]] = None):
        """
        需要在【指南】-【每日实训】页面中使用
        获取任意一个未完成且可执行的的实训任务
        返回状态为任务ID
        :param ctx: 上下文
        :param ignore_missions: 需要忽略的部分 用于过滤掉失败的任务 DailyTrainingMission.id_cn的列表
        """
        super().__init__(ctx, try_times=5, op_name=gt('获取实训任务', 'ui'))
        self.ignore_missions: Optional[List[DailyTrainingMission]] = ignore_missions

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        go_pos_list = self._get_go_pos(screen)
        for go_pos in go_pos_list:
            mission = self._get_mission(screen, go_pos)

            if mission is None:
                continue

            log.info('识别到未执行的实训任务 %s', mission.id_cn)

            if not mission.able:  # 目前不支持的类型
                log.info('实训任务 %s 未支持执行', mission.id_cn)
                continue

            if self.ignore_missions is not None and mission.id_cn in self.ignore_missions:  # 需要过滤的
                log.info('实训任务 %s 已失败跳过', mission.id_cn)
                continue

            return Operation.round_success(mission.id_cn)

        # 没找到目标 往右滑动
        drag_from = GetTrainingUnfinishedMission.GO_RECT.center
        drag_to = drag_from + Point(-200, 0)
        self.ctx.controller.drag_to(drag_to, drag_from)
        time.sleep(1)

        return Operation.round_retry('未找到可执行任务')

    def _get_mission(self, screen: MatLike, go_pos: MatchResult) -> Optional[DailyTrainingMission]:
        """
        获取任务
        :param screen: 屏幕截图
        :param go_pos: 【前往】按钮的位置
        :return:
        """
        c = go_pos.center
        rect = Rect(c.x - 155, c.y - 360, c.x + 155, c.y - 170)
        part, _ = cv2_utils.crop_image(screen, rect)
        ocr_result_map = self.ctx.ocr.run_ocr(part, merge_line_distance=40)
        # cv2_utils.show_image(part, win_name='_get_mission', wait=0)
        for key in ocr_result_map.keys():
            target_mission = None  # 找一个匹配度最高的结果
            target_lcs_percent = None
            for mission in ALL_MISSION_LIST:
                target_word = gt(mission.desc_cn, 'ocr')
                lcs = str_utils.longest_common_subsequence_length(target_word, key)
                lcs_percent = lcs / len(target_word)
                if lcs_percent < 0.5:  # 最低要求
                    continue
                if target_mission is None or lcs_percent > target_lcs_percent:
                    target_mission = mission
                    target_lcs_percent = lcs_percent

            if target_mission is not None:
                return target_mission
        return None

    def _get_go_pos(self, screen: Optional[MatLike] = None) -> List[MatchResult]:
        """
        获取【前往】或【进行中】按钮的位置
        :param screen: 屏幕截图
        :return: 位置
        """
        if screen is None:
            screen = self.screenshot()

        part, _ = cv2_utils.crop_image(screen, GetTrainingUnfinishedMission.GO_RECT)
        # cv2_utils.show_image(part, win_name='_get_go_pos', wait=0)

        ocr_map = self.ctx.ocr.match_words(part, words=['前往', '进行中'], lcs_percent=0.1)

        go_pos_list: List[MatchResult] = []

        lt = GetTrainingUnfinishedMission.GO_RECT.left_top
        for mrl in ocr_map.values():
            for mr in mrl:
                mr.x += lt.x
                mr.y += lt.y
                go_pos_list.append(mr)

        return go_pos_list
