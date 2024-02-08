from enum import Enum
from typing import List

from cv2.typing import MatLike

from basic import Point, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.image.sceenshot.screen_state import ScreenState
from sr.operation import Operation, StateOperation, StateOperationNode, OperationOneRoundResult
from sr.screen_area.interastral_peace_guide import ScreenGuide


class SurvivalIndexCategory:

    def __init__(self, tab: ScreenState, cn: str):
        """
        生存索引左侧的类目
        """
        self.tab: ScreenState = tab
        """指南上的TAB"""

        self.cn: str = cn
        """中文"""


class SurvivalIndexCategoryEnum(Enum):

    BUD_1 = SurvivalIndexCategory(tab=ScreenState.GUIDE_SURVIVAL_INDEX, cn='拟造花萼金')
    BUD_2 = SurvivalIndexCategory(tab=ScreenState.GUIDE_SURVIVAL_INDEX, cn='拟造花萼赤')
    SHAPE = SurvivalIndexCategory(tab=ScreenState.GUIDE_SURVIVAL_INDEX, cn='凝滞虚影')
    PATH = SurvivalIndexCategory(tab=ScreenState.GUIDE_SURVIVAL_INDEX, cn='侵蚀虫洞')
    ECHO_OF_WAR = SurvivalIndexCategory(tab=ScreenState.GUIDE_SURVIVAL_INDEX, cn='历战回响')
    FORGOTTEN_HALL = SurvivalIndexCategory(tab=ScreenState.GUIDE_TREASURES_LIGHTWARD, cn='忘却之庭')
    ROGUE = SurvivalIndexCategory(tab=ScreenState.GUIDE_SURVIVAL_INDEX, cn='模拟宇宙')


class SurvivalIndexChooseCategory(StateOperation):

    def __init__(self, ctx: Context, target: SurvivalIndexCategory,
                 skip_wait: bool = True):
        """
        在 星际和平指南-生存索引 画面中使用
        选择左方的一个类目
        :param ctx: 上下文
        :param target: 目标类目
        :param skip_wait: 跳过等待加载
        """
        nodes = []
        if not skip_wait:
            nodes.append(StateOperationNode('等待加载', self._wait))
        nodes.append(StateOperationNode('选择', self._choose))

        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('生存索引', 'ui'), gt(target.cn, 'ui')),
                         nodes=nodes
                         )

        self.target: SurvivalIndexCategory = target

    def _wait(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        area = ScreenGuide.SURVIVAL_INDEX_TITLE.value
        if self.find_area(area, screen):
            return Operation.round_success()
        else:
            return Operation.round_retry('未在%s画面' % area.text)

    def _choose(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        area = ScreenGuide.SURVIVAL_INDEX_CATE.value

        part = cv2_utils.crop_image_only(screen, area.rect)

        ocr_result_map = self.ctx.ocr.run_ocr(part)

        for k, v in ocr_result_map.items():
            # 看有没有目标
            if str_utils.find_by_lcs(gt(self.target.cn, 'ocr'), k, 0.3):
                to_click = v.max.center + area.rect.left_top
                log.info('生存索引中找到 %s 尝试点击', self.target.cn)
                if self.ctx.controller.click(to_click):
                    return Operation.round_success(wait=0.5)

        log.info('生存索引中未找到 %s 尝试滑动', self.target.cn)
        # 没有目标时候看要往哪个方向滚动
        other_before_target: bool = True  # 由于这里每次打开都是在最顶端 所以应该只需往下滑就好了

        point_from = area.rect.center
        point_to = point_from + (Point(0, -200) if other_before_target else Point(0, 200))
        self.ctx.controller.drag_to(point_to, point_from)
        return Operation.round_retry('未找到%s' % self.target.cn, wait=0.5)


class SurvivalIndexMission:

    def __init__(self):
        pass

class SurvivalIndexChooseMission(StateOperation):

    def __init__(self):
        pass