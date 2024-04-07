from typing import ClassVar, Optional, Tuple

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.app.application_base import Application
from sr.app.sim_uni.sim_uni_app import SimUniApp
from sr.app.trailblaze_power.trailblaze_power_config import TrailblazePowerPlanItem
from sr.const import phone_menu_const
from sr.context import Context
from sr.image.sceenshot import large_map
from sr.operation import StateOperationNode, StateOperationEdge, OperationOneRoundResult, Operation
from sr.operation.combine.use_trailblaze_power import UseTrailblazePower
from sr.operation.common.back_to_normal_world_plus import BackToNormalWorldPlus
from sr.operation.unit.guide import GuideTabEnum
from sr.operation.unit.guide.choose_guide_tab import ChooseGuideTab
from sr.interastral_peace_guide.survival_index_mission import SurvivalIndexCategoryEnum, SurvivalIndexMission, \
    SurvivalIndexMissionEnum
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.operation.unit.open_map import OpenMap


class TrailblazePower(Application):

    SIM_UNI_POWER_RECT: ClassVar[Rect] = Rect(1474, 56, 1518, 78)  # 模拟宇宙 体力
    SIM_UNI_QTY_RECT: ClassVar[Rect] = Rect(1672, 56, 1707, 78)  # 模拟宇宙 沉浸器数量

    STATUS_NORMAL_TASK: ClassVar[str] = '普通副本'
    STATUS_SIM_UNI_TASK: ClassVar[str] = '模拟宇宙'
    STATUS_NO_ENOUGH_POWER: ClassVar[str] = '体力不足'
    STATUS_PLAN_FINISHED: ClassVar[str] = '完成计划'

    def __init__(self, ctx: Context):
        edges = []

        world = StateOperationNode('返回大世界', op=BackToNormalWorldPlus(ctx))
        check_task = StateOperationNode('检查当前需要挑战的关卡', self._check_task)
        edges.append(StateOperationEdge(world, check_task))

        check_normal_power = StateOperationNode('检查剩余开拓力', self._check_power_for_normal)
        edges.append(StateOperationEdge(check_task, check_normal_power, status=TrailblazePower.STATUS_NORMAL_TASK))

        challenge_normal = StateOperationNode('挑战普通副本', self._challenge_normal_task)
        edges.append(StateOperationEdge(check_normal_power, challenge_normal))
        edges.append(StateOperationEdge(challenge_normal, check_task))  # 循环挑战

        check_sim_uni_power = StateOperationNode('检查剩余沉浸器', self._check_power_for_sim_uni)
        edges.append(StateOperationEdge(check_task, check_sim_uni_power, status=TrailblazePower.STATUS_SIM_UNI_TASK))

        challenge_sim_uni = StateOperationNode('挑战模拟宇宙', self._challenge_sim_uni)
        edges.append(StateOperationEdge(check_sim_uni_power, challenge_sim_uni))
        edges.append(StateOperationEdge(challenge_sim_uni, check_task))

        back = StateOperationNode('完成后返回大世界', op=BackToNormalWorldPlus(ctx))
        edges.append(StateOperationEdge(challenge_normal, back, status=TrailblazePower.STATUS_NO_ENOUGH_POWER))
        edges.append(StateOperationEdge(challenge_normal, back, status=TrailblazePower.STATUS_PLAN_FINISHED))
        edges.append(StateOperationEdge(challenge_sim_uni, back, status=TrailblazePower.STATUS_NO_ENOUGH_POWER))
        edges.append(StateOperationEdge(challenge_sim_uni, back, status=TrailblazePower.STATUS_PLAN_FINISHED))

        super().__init__(ctx, try_times=5,
                         op_name=gt('开拓力', 'ui'),
                         edges=edges,
                         run_record=ctx.tp_run_record)
        self.power: Optional[int] = None  # 剩余开拓力
        self.qty: Optional[int] = None  # 沉浸器数量
        self.last_challenge_point: Optional[SurvivalIndexMission] = None

    def _init_before_execute(self):
        super()._init_before_execute()
        self.last_challenge_point = None
        self.power = None

    def _check_task(self) -> OperationOneRoundResult:
        """
        判断下一个是什么副本
        :return:
        """
        self.ctx.tp_config.check_plan_finished()
        plan: Optional[TrailblazePowerPlanItem] = self.ctx.tp_config.next_plan_item

        if plan is None:
            return Operation.round_success()

        point: Optional[SurvivalIndexMission] = SurvivalIndexMissionEnum.get_by_unique_id(plan['mission_id'])
        if point.cate == SurvivalIndexCategoryEnum.SIM_UNI.value:
            return Operation.round_success(TrailblazePower.STATUS_SIM_UNI_TASK)
        else:
            return Operation.round_success(TrailblazePower.STATUS_NORMAL_TASK)

    def _check_power_for_normal(self) -> OperationOneRoundResult:
        """
        普通副本 在大地图上看剩余体力
        :return:
        """
        if self.power is not None:  # 之前已经检测过了
            return Operation.round_success()

        op = OpenMap(self.ctx)
        op_result = op.execute()
        if not op_result.success:
            return Operation.round_retry('打开大地图失败')

        screen: MatLike = self.screenshot()
        part = cv2_utils.crop_image_only(screen, large_map.LARGE_MAP_POWER_RECT)
        ocr_result = self.ctx.ocr.ocr_for_single_line(part, strict_one_line=True)
        self.power = str_utils.get_positive_digits(ocr_result, err=None)
        if self.power is None:
            return Operation.round_retry('检测剩余开拓力失败', wait=1)
        else:
            log.info('识别当前开拓力 %d', self.power)
            return Operation.round_success()

    def _challenge_normal_task(self) -> OperationOneRoundResult:
        """
        挑战普通副本
        :return:
        """
        plan: Optional[TrailblazePowerPlanItem] = self.ctx.tp_config.next_plan_item
        point: Optional[SurvivalIndexMission] = SurvivalIndexMissionEnum.get_by_unique_id(plan['mission_id'])
        run_times: int = self.power // point.power
        if run_times == 0:
            return Operation.round_success(TrailblazePower.STATUS_NO_ENOUGH_POWER)
        if run_times + plan['run_times'] > plan['plan_times']:
            run_times = plan['plan_times'] - plan['run_times']
        if run_times == 0:
            return Operation.round_success(TrailblazePower.STATUS_PLAN_FINISHED)

        op = UseTrailblazePower(self.ctx, point, plan['team_num'], run_times,
                                support=plan['support'] if plan['support'] != 'none' else None,
                                on_battle_success=self._on_normal_task_success,
                                need_transport=point != self.last_challenge_point)

        op_result = op.execute()
        if op_result.success:
            self.last_challenge_point = point
        return Operation.round_by_op(op_result)

    def _on_normal_task_success(self, finished_times: int, use_power: int):
        """
        普通副本获取一次奖励时候的回调
        :param finished_times: 完成次数
        :param use_power: 使用的体力
        :return:
        """
        log.info('挑战成功 完成次数 %d 使用体力 %d', finished_times, use_power)
        self.power -= use_power
        plan: Optional[TrailblazePowerPlanItem] = self.ctx.tp_config.next_plan_item
        plan['run_times'] += finished_times
        self.ctx.tp_config.save()

    def _check_power_for_sim_uni(self) -> OperationOneRoundResult:
        if self.qty is not None:
            return Operation.round_success()

        ops = [
            OpenPhoneMenu(self.ctx),
            ClickPhoneMenuItem(self.ctx, phone_menu_const.INTERASTRAL_GUIDE),
            ChooseGuideTab(self.ctx, GuideTabEnum.TAB_3.value)
        ]

        for op in ops:
            op_result = op.execute()
            if not op_result.success:
                return Operation.round_by_op(op_result)

        screen = self.screenshot()
        x, y = self._get_sim_uni_power_and_qty(screen)

        if x is None or y is None:
            return Operation.round_retry('检测开拓力和沉浸器数量失败', wait=1)

        log.info('检测当前体力 %d 沉浸器数量 %d', x, y)
        self.power = x
        self.qty = y
        return Operation.round_success()

    def _get_sim_uni_power_and_qty(self, screen: MatLike) -> Tuple[int, int]:
        """
        获取开拓力和沉浸器数量
        :param screen: 屏幕截图
        :return:
        """
        part = cv2_utils.crop_image_only(screen, TrailblazePower.SIM_UNI_POWER_RECT)
        ocr_result = self.ctx.ocr.ocr_for_single_line(part)
        power = str_utils.get_positive_digits(ocr_result, err=None)

        part = cv2_utils.crop_image_only(screen, TrailblazePower.SIM_UNI_QTY_RECT)
        ocr_result = self.ctx.ocr.ocr_for_single_line(part)
        qty = str_utils.get_positive_digits(ocr_result, err=None)

        return power, qty

    def _challenge_sim_uni(self) -> OperationOneRoundResult:
        plan: Optional[TrailblazePowerPlanItem] = self.ctx.tp_config.next_plan_item
        point: Optional[SurvivalIndexMission] = SurvivalIndexMissionEnum.get_by_unique_id(plan['mission_id'])
        run_times: int = self.power // point.power + self.qty
        if run_times == 0:
            return Operation.round_success(TrailblazePower.STATUS_NO_ENOUGH_POWER)
        if run_times + plan['run_times'] > plan['plan_times']:
            run_times = plan['plan_times'] - plan['run_times']
        if run_times == 0:
            return Operation.round_success(TrailblazePower.STATUS_PLAN_FINISHED)

        self.ctx.sim_uni_run_record.check_and_update_status()
        op = SimUniApp(self.ctx,
                       specified_uni_num=point.tp.idx,
                       max_reward_to_get=run_times,
                       get_reward_callback=self._on_sim_uni_get_reward
                       )
        op.init_context_before_start = False
        op.stop_context_after_stop = False
        return Operation.round_by_op(op.execute())

    def _on_sim_uni_get_reward(self, use_power: int, user_qty: int):
        """
        模拟宇宙 获取沉浸奖励后的回调
        :return:
        """
        log.info('获取沉浸奖励 使用体力 %d 使用沉浸器 %d', use_power, user_qty)
        plan: Optional[TrailblazePowerPlanItem] = self.ctx.tp_config.next_plan_item
        plan['run_times'] += 1
        self.ctx.tp_config.save()

        self.power -= use_power
        self.qty -= user_qty
