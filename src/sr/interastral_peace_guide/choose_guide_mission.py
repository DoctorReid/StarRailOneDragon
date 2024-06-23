import time
from typing import Optional

from cv2.typing import MatLike

from basic import Point
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.context.context import Context
from sr.image.sceenshot.screen_state import in_secondary_ui
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.interastral_peace_guide.guide_const import GuideMission
from sr.operation import Operation, OperationOneRoundResult
from sr.screen_area.interastral_peace_guide import ScreenGuide


class ChooseGuideMission(Operation):
    """
    需要先在【星际和平指引】-【生存索引】位置 且左侧类目已经选好了
    在右边选择对应副本进行传送
    """
    def __init__(self, ctx: Context, mission: GuideMission):
        super().__init__(ctx, try_times=5,
                         op_name='%s %s %s' % (
                             gt('指南', 'ui'),
                             gt(mission.cate.tab.cn, 'ui'),
                             gt(mission.name_in_guide, 'ui')
                         ))
        self.mission: GuideMission = mission

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        if not in_secondary_ui(screen, self.ctx.ocr, ScreenState.GUIDE.value):
            time.sleep(1)
            return self.round_retry('未在' + ScreenState.GUIDE.value)

        if not in_secondary_ui(screen, self.ctx.ocr, self.mission.cate.tab.cn):
            time.sleep(1)
            return self.round_retry('未在' + self.mission.cate.tab.cn)

        area = ScreenGuide.MISSION_LIST_RECT.value
        tp_point = self._find_transport_btn(screen)

        if tp_point is None:  # 由于这里每次打开都是在最顶端 所以应该只需往下滑就好了
            log.info('未找到 %s 尝试滑动', self.mission.name_in_guide)
            point_from = area.center
            point_to = point_from + Point(0, -200)
            self.ctx.controller.drag_to(point_to, point_from)
            time.sleep(0.5)
            return self.round_retry('未找到 ' + self.mission.name_in_guide)
        else:
            log.info('找到 %s 尝试传送', self.mission.name_in_guide)
            if self.ctx.controller.click(tp_point):
                return self.round_success()
            else:
                return self.round_fail('点击失败')

    def _find_transport_btn(self, screen: MatLike) -> Optional[Point]:
        """
        在右侧栏中找到传送按钮的位置
        找在目标副本名称下方 最近的一个传送按钮
        :param screen: 屏幕截图
        :return: 传送按钮的点击位置
        """
        area = ScreenGuide.MISSION_LIST_RECT.value
        part, _ = cv2_utils.crop_image(screen, area.rect)

        mission_name = gt(self.mission.name_in_guide, 'ocr')
        mission_ocr_map = self.ctx.ocr.match_words(part, words=[mission_name])  # 副本和传送分开匹配 这样好设置阈值

        mission_point: Optional[Point] = None
        for v in mission_ocr_map.values():
            if v.max is not None:
                mission_point = v.max.center
                break

        if mission_point is None:
            return None

        tp_ocr_map = self.ctx.ocr.match_words(part, words=[gt('传送', 'ocr')], lcs_percent=0.3)  # 副本和传送分开匹配 这样好设置阈值
        tp_point: Optional[Point] = None
        for v in tp_ocr_map.values():
            for result in v:
                if result.center.y < mission_point.y:  # 传送按钮需要在副本名称下方
                    continue
                if tp_point is None or tp_point.y > result.center.y:  # 找出在副本名称下方最近的一个传送按钮
                    tp_point = result.center

        if tp_point is not None:
            tp_point = tp_point + area.rect.left_top

        return tp_point
