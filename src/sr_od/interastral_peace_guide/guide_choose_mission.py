from cv2.typing import MatLike
from typing import Optional

from one_dragon.base.geometry.point import Point
from one_dragon.base.matcher.match_result import MatchResultList
from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from sr_od.context.sr_context import SrContext
from sr_od.interastral_peace_guide.guide_def import GuideMission
from sr_od.operations.sr_operation import SrOperation
from sr_od.screen_state import common_screen_state


class GuideChooseMission(SrOperation):
    """
    需要先在【星际和平指引】-【生存索引】位置 且左侧类目已经选好了
    在右边选择对应副本进行传送
    """
    def __init__(self, ctx: SrContext, mission: GuideMission):
        SrOperation.__init__(self, ctx,
                             op_name='%s %s' % (
                                 gt('指南选择副本', 'ui'),
                                 gt(mission.mission_name, 'ui')
                             ))
        self.mission: GuideMission = mission

    @operation_node(name='等待画面加载', node_max_retry_times=5, is_start_node=True)
    def wait_screen(self) -> OperationRoundResult:
        screen: MatLike = self.screenshot()

        if common_screen_state.in_secondary_ui(self.ctx, screen, self.mission.cate.tab.cn):
            return self.round_success()
        else:
            return self.round_retry('未在画面 %s' % self.mission.cate.tab.cn, wait=1)

    @node_from(from_name='等待画面加载')
    @operation_node(name='选择', node_max_retry_times=10)
    def choose(self) -> OperationRoundResult:
        screen: MatLike = self.screenshot()

        tp_point = self.find_transport_btn(screen)
        if tp_point is None:
            area = self.ctx.screen_loader.get_area('星际和平指南', '副本列表')
            drag_from = area.center
            drag_to = drag_from + Point(0, -200)
            self.ctx.controller.drag_to(drag_to, drag_from)

            return self.round_retry(wait=2)
        else:
            self.ctx.controller.click(tp_point)
            return self.round_success()

    def find_transport_btn(self, screen: MatLike) -> Optional[Point]:
        """
        在右侧栏中找到传送按钮的位置
        找在目标副本名称下方 最近的一个传送按钮
        :param screen: 屏幕截图
        :return: 传送按钮的点击位置
        """
        area = self.ctx.screen_loader.get_area('星际和平指南', '副本列表')
        part = cv2_utils.crop_image_only(screen, area.rect)

        ocr_result_map = self.ctx.ocr.run_ocr(part)

        word_list = []
        mrl_list = []

        for ocr_word, mrl in ocr_result_map.items():
            word_list.append(ocr_word)
            mrl_list.append(mrl)

        if self.mission.region_name is not None:
            region_idx = str_utils.find_best_match_by_difflib(gt(self.mission.region_name), word_list, cutoff=0.5)
            if region_idx is None:
                log.error('匹配失败 %s', self.mission.region_name)
                return None
            log.info('匹配区域名称 %s', word_list[region_idx])

            # 区域通常不会重复 取max即可
            region_pos = mrl_list[region_idx].max.right_bottom

            # 只保留区域上方一定距离的文本
            mission_region_distance = 50
            if self.mission.mission_name == '模拟宇宙':
                mission_region_distance = 350

            word_list = []
            mrl_list = []

            for ocr_word, mrl in ocr_result_map.items():
                mrl2 = MatchResultList(only_best=False)
                for mr in mrl:
                    if 0 < region_pos.y - mr.right_bottom.y < mission_region_distance:
                        mrl2.append(mr)

                if len(mrl2) == 0:
                    continue

                word_list.append(ocr_word)
                mrl_list.append(mrl2)

            log.info('过滤后文本 %s', word_list)

        mission_idx = str_utils.find_best_match_by_difflib(gt(self.mission.mission_name), word_list, cutoff=0.5)
        if mission_idx is None:
            log.error('匹配失败 %s', self.mission.mission_name)
            return None
        log.info('匹配副本名称 %s', word_list[mission_idx])

        tp_idx = str_utils.find_best_match_by_difflib(gt('传送'), word_list, cutoff=0.5)  # 模拟宇宙
        if tp_idx is None:
            tp_idx = str_utils.find_best_match_by_difflib(gt('进入'), word_list, cutoff=0.5)  # 普通副本
        if tp_idx is None:
            log.error('匹配失败 传送/进入')
            return None

        mission_pos = mrl_list[mission_idx].max.center
        tp_mrl = mrl_list[tp_idx]

        # 返回最靠近副本名称的传送
        tp_point = None
        for mr in tp_mrl:
            if self.mission.mission_name == '模拟宇宙':
                if abs(mr.center.y - region_pos.y) > 30:  # 模拟宇宙用下面的首通奖励来匹配 太远的就忽略
                    continue
            elif self.mission.cate.cn == '历战余响':
                if abs(mr.center.y - mission_pos.y) > 150:  # 历战余响距离较远
                    continue
            else:
                if abs(mr.center.y - mission_pos.y) > 30:  # 普通副本
                    continue

            if tp_point is None or abs(mr.center.y - mission_pos.y) < abs(tp_point.y - mission_pos.y):
                tp_point = mr.center

        if tp_point is not None:
            return tp_point + area.left_top
        else:
            return None


def __debug():
    ctx = SrContext()
    ctx.init_by_config()
    ctx.ocr.init_model()
    ctx.start_running()

    tab = ctx.guide_data.best_match_tab_by_name('生存索引')
    category = ctx.guide_data.best_match_category_by_name('拟造花萼（赤）', tab)
    mission = ctx.guide_data.best_match_mission_by_name('同谐之蕾', category, '「白日梦」酒店-梦境')

    op = GuideChooseMission(ctx, mission)
    op.execute()


if __name__ == '__main__':
    __debug()
