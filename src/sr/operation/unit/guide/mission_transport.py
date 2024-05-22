import time
from typing import Optional

from cv2.typing import MatLike

from basic import Rect, str_utils, Point
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot.screen_state import in_secondary_ui, ScreenState
from sr.operation import Operation, OperationOneRoundResult
from sr.interastral_peace_guide.survival_index_mission import SurvivalIndexCategory, SurvivalIndexCategoryEnum

CATEGORY_LIST_RECT = Rect(270, 300, 680, 910)


class ChooseGuideMissionCategory(Operation):
    """
    需要先在【星际和平指引】和对应TAB的位置

    选择左侧对应类目
    """

    def __init__(self, ctx: Context, category: SurvivalIndexCategory):
        super().__init__(ctx, try_times=5, op_name='%s %s' % (gt(category.tab.value, 'ui'), gt(category.cn, 'ui')))
        self.category: SurvivalIndexCategory = category

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        if not in_secondary_ui(screen, self.ctx.ocr, ScreenState.GUIDE.value):
            time.sleep(1)
            return self.round_retry('未在' + ScreenState.GUIDE.value)

        if not in_secondary_ui(screen, self.ctx.ocr, self.category.tab.value):
            time.sleep(1)
            return self.round_retry('未在' + self.category.tab.value)

        part, _ = cv2_utils.crop_image(screen, CATEGORY_LIST_RECT)
        ocr_result_map = self.ctx.ocr.run_ocr(part)

        for k, v in ocr_result_map.items():
            # 看有没有目标
            if str_utils.find_by_lcs(gt(self.category.cn, 'ocr'), k, 0.3):
                to_click = v.max.center + CATEGORY_LIST_RECT.left_top
                log.info('生存索引中找到 %s 尝试点击', self.category.cn)
                if self.ctx.controller.click(to_click):
                    return self.round_success()

        log.info('生存索引中未找到 %s 尝试滑动', self.category.cn)
        # 没有目标时候看要往哪个方向滚动
        other_before_target: bool = True  # 由于这里每次打开都是在最顶端 所以应该只需往下滑就好了
        # for item in CATEGORY_LIST:
        #     if item == self.item:
        #         break
        #     for k in ocr_result_map.keys():
        #         if str_utils.find_by_lcs(gt(item.cn, 'ocr'), k, 0.3):
        #             other_before_target = True
        #             break

        point_from = CATEGORY_LIST_RECT.center
        point_to = point_from + (Point(0, -200) if other_before_target else Point(0, 200))
        self.ctx.controller.drag_to(point_to, point_from)
        time.sleep(0.5)
        return self.round_retry('未找到目标')


class GuideMission:

    def __init__(self, category: SurvivalIndexCategory, cn: str):
        """
        生存索引右侧的副本
        """
        self.category: SurvivalIndexCategory = category
        """分类"""
        self.cn: str = cn
        """中文"""


MISSION_FORGOTTEN_HALL = GuideMission(category=None, cn='混沌回忆')
MISSION_SIM_UNIVERSE = GuideMission(category=SurvivalIndexCategoryEnum.SIM_UNI.value, cn='本周积分')  # 模拟宇宙最上方总分的传送


MISSION_LIST_RECT = Rect(695, 295, 1655, 930)  # 副本列表的位置


class ChooseGuideMission(Operation):
    """
    需要先在【星际和平指引】-【生存索引】位置 且左侧类目已经选好了
    在右边选择对应副本进行传送
    """
    def __init__(self, ctx: Context, mission: GuideMission):
        super().__init__(ctx, try_times=5, op_name='%s %s' % (gt(mission.category.tab.value, 'ui'), gt(mission.cn, 'ui')))
        self.mission: GuideMission = mission

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen: MatLike = self.screenshot()

        if not in_secondary_ui(screen, self.ctx.ocr, ScreenState.GUIDE.value):
            log.info('等待生存索引加载')
            time.sleep(1)
            return self.round_retry('未在' + ScreenState.GUIDE.value)

        if not in_secondary_ui(screen, self.ctx.ocr, self.mission.category.tab.value):
            log.info('等待生存索引加载')
            time.sleep(1)
            return self.round_retry('未在' + self.mission.category.tab.value)

        tp_point = self._find_transport_btn(screen)

        if tp_point is None:  # 由于这里每次打开都是在最顶端 所以应该只需往下滑就好了
            log.info('生存索引中未找到 %s 尝试滑动', self.mission.cn)
            point_from = MISSION_LIST_RECT.center
            point_to = point_from + Point(0, -200)
            self.ctx.controller.drag_to(point_to, point_from)
            time.sleep(0.5)
            return self.round_retry('未找到 ' + self.mission.cn)
        else:
            log.info('生存索引中找到 %s 尝试传送', self.mission.cn)
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
        part, _ = cv2_utils.crop_image(screen, MISSION_LIST_RECT)

        mission_name = gt(self.mission.cn, 'ocr')
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
            tp_point = tp_point + MISSION_LIST_RECT.left_top

        return tp_point
