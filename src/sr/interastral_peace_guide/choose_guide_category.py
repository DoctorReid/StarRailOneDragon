from basic import Point, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.context.context import Context
from sr.interastral_peace_guide.guide_const import GuideCategory
from sr.operation import StateOperation, StateOperationNode, OperationOneRoundResult
from sr.screen_area.interastral_peace_guide import ScreenGuide


class ChooseGuideCategory(StateOperation):

    def __init__(self, ctx: Context, target: GuideCategory,
                 skip_wait: bool = True):
        """
        在 星际和平指南 画面中使用
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
                         op_name='%s %s' % (gt('指南', 'ui'), gt(target.cn, 'ui')),
                         nodes=nodes
                         )

        self.target: GuideCategory = target

    def _wait(self) -> OperationOneRoundResult:
        """
        等待画面加载 左上角出现对应tab的
        :return:
        """
        screen = self.screenshot()

        area = ScreenGuide.SURVIVAL_INDEX_TITLE.value
        part = cv2_utils.crop_image_only(screen, area.rect)

        target_tab = self.target.tab.cn
        ocr_result = self.ctx.ocr.ocr_for_single_line(part)
        if str_utils.find_by_lcs(ocr_result, gt(target_tab, 'ocr'), percent=0.55):
            return self.round_success()
        else:
            return self.round_retry('未在%s画面' % target_tab)

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
                    return self.round_success(wait=0.5)

        log.info('生存索引中未找到 %s 尝试滑动', self.target.cn)
        # 没有目标时候看要往哪个方向滚动
        other_before_target: bool = True  # 由于这里每次打开都是在最顶端 所以应该只需往下滑就好了

        point_from = area.rect.center
        point_to = point_from + (Point(0, -200) if other_before_target else Point(0, 200))
        self.ctx.controller.drag_to(point_to, point_from)
        return self.round_retry('未找到%s' % self.target.cn, wait=0.5)
