from cv2.typing import MatLike
from typing import ClassVar, Optional, Tuple

from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils import cv2_utils, str_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from sr_od.app.sr_application import SrApplication
from sr_od.app.trailblaze_power.trailblaze_power_config import TrailblazePowerPlanItem
from sr_od.challenge_mission.use_trailblaze_power import UseTrailblazePower
from sr_od.context.sr_context import SrContext
from sr_od.interastral_peace_guide.guid_choose_tab import GuideChooseTab
from sr_od.interastral_peace_guide.guide_def import GuideMission
from sr_od.operations.back_to_normal_world_plus import BackToNormalWorldPlus
from sr_od.operations.menu import phone_menu_const
from sr_od.operations.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr_od.operations.menu.open_phone_menu import OpenPhoneMenu


class TrailblazePower(SrApplication):

    STATUS_NORMAL_TASK: ClassVar[str] = '普通副本'
    STATUS_SIM_UNI_TASK: ClassVar[str] = '模拟宇宙'
    STATUS_OE_TASK: ClassVar[str] = '饰品提取'
    STATUS_NO_ENOUGH_POWER: ClassVar[str] = '体力不足'
    STATUS_NO_PLAN: ClassVar[str] = '没有开拓力计划'
    STATUS_WITH_PLAN: ClassVar[str] = '有开拓力计划'
    STATUS_PLAN_FINISHED: ClassVar[str] = '完成计划'

    def __init__(self, ctx: SrContext):
        SrApplication.__init__(self, ctx, 'trailblaze_power',
                               op_name=gt('开拓力', 'ui'),
                               run_record=ctx.power_record)
        
        self.last_mission: Optional[GuideMission] = None  # 上一个挑战副本
        self.power: int = 0  # 剩余开拓力
        self.qty: int = 0  # 沉浸器数量

    @operation_node(name='返回大世界', is_start_node=True)
    def back_at_first(self) -> OperationRoundResult:
        op = BackToNormalWorldPlus(self.ctx)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='返回大世界')
    @operation_node(name='检查当前需要挑战的关卡')
    def check_task(self) -> OperationRoundResult:
        """
        判断下一个是什么副本
        :return:
        """
        self.ctx.power_config.check_plan_finished()
        plan: Optional[TrailblazePowerPlanItem] = self.ctx.power_config.next_plan_item

        if plan is None:
            return self.round_success(status=TrailblazePower.STATUS_NO_PLAN)

        return self.round_success(status=TrailblazePower.STATUS_WITH_PLAN)

    @node_from(from_name='检查当前需要挑战的关卡', status=STATUS_WITH_PLAN)
    @operation_node(name='打开菜单')
    def open_menu(self) -> OperationRoundResult:
        op = OpenPhoneMenu(self.ctx)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='打开菜单')
    @operation_node(name='选择指南')
    def choose_guide(self) -> OperationRoundResult:
        op = ClickPhoneMenuItem(self.ctx, phone_menu_const.INTERASTRAL_GUIDE)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='选择指南')
    @operation_node(name='选择生存索引')
    def choose_guide_tab(self) -> OperationRoundResult:
        tab = self.ctx.guide_data.best_match_tab_by_name(gt('生存索引'))
        op = GuideChooseTab(self.ctx, tab)
        return self.round_by_op_result(op.execute())

    @node_from(from_name='选择生存索引')
    @operation_node(name='识别开拓力和沉浸器数量')
    def check_power(self) -> OperationRoundResult:
        screen = self.screenshot()
        x, y = self._get_power_and_qty(screen)

        if x is None or y is None:
            return self.round_retry('检测开拓力和沉浸器数量失败', wait=1)

        log.info('检测当前体力 %d 沉浸器数量 %d', x, y)
        self.power = x
        self.qty = y

        return self.round_success()

    def _get_power_and_qty(self, screen: MatLike) -> Tuple[int, int]:
        """
        获取开拓力和沉浸器数量
        :param screen: 屏幕截图
        :return:
        """
        area1 = self.ctx.screen_loader.get_area('星际和平指南', '生存索引-体力')
        part = cv2_utils.crop_image_only(screen, area1.rect)
        ocr_result = self.ctx.ocr.run_ocr_single_line(part)
        power = str_utils.get_positive_digits(ocr_result, err=None)

        area2 = self.ctx.screen_loader.get_area('星际和平指南', '生存索引-沉浸器数量')
        part = cv2_utils.crop_image_only(screen, area2.rect)
        ocr_result = self.ctx.ocr.run_ocr_single_line(part)
        qty = str_utils.get_positive_digits(ocr_result, err=None)

        return power, qty

    @node_from(from_name='识别开拓力和沉浸器数量')
    @node_from(from_name='执行开拓力计划')
    @operation_node(name='执行开拓力计划')
    def execute_plan(self) -> OperationRoundResult:
        plan: Optional[TrailblazePowerPlanItem] = self.ctx.power_config.next_plan_item
        if plan is None:
            return self.round_success(TrailblazePower.STATUS_NO_PLAN)

        mission: Optional[GuideMission] = self.ctx.guide_data.get_mission_by_unique_id(plan.mission_id)
        if mission is None:
            return self.round_success(TrailblazePower.STATUS_NO_PLAN)

        can_run_times: int = self.power // mission.power
        if mission.cate.cn in ['模拟宇宙', '饰品提取']:  # 模拟宇宙相关的增加沉浸器数量
            can_run_times += self.qty

        if can_run_times == 0:
            return self.round_success(TrailblazePower.STATUS_NO_ENOUGH_POWER)

        if can_run_times + plan.run_times > plan.plan_times:
            run_times = plan.plan_times - plan.run_times
        else:
            run_times = can_run_times

        log.info(f'准备挑战 {mission.mission_name} 次数 {run_times}')
        if run_times == 0:
            return self.round_success(TrailblazePower.STATUS_PLAN_FINISHED)

        # TODO 刷之前需要更新模拟宇宙的记录
        # self.ctx.sim_uni_run_record.check_and_update_status()

        if mission.cate.cn not in ['模拟宇宙', '饰品提取']:
            op = UseTrailblazePower(self.ctx, mission, plan.team_num, run_times,
                                    support=plan.support if plan.support != 'none' else None,
                                    on_battle_success=self._on_normal_task_success)
        elif mission.cate.cn == '模拟宇宙':
            # op = SimUniApp(self.ctx,
            #                specified_uni_num=mission.sim_world.idx,
            #                max_reward_to_get=run_times,
            #                get_reward_callback=self._on_sim_uni_get_reward
            #                )
            # op.init_context_before_start = False
            # op.stop_context_after_stop = False
            return self.round_fail('未支持模拟宇宙')
        elif mission.cate.cn == '饰品提取':
            # op = ChallengeOrnamentExtraction(self.ctx, mission.ornament_extraction,
            #                                  run_times=run_times,
            #                                  diff=0,
            #                                  file_num=plan['team_num'],
            #                                  support_character=plan['support'] if plan['support'] != 'none' else None,
            #                                  get_reward_callback=self.on_oe_get_reward)
            return self.round_fail('未支持饰品提取')
        else:
            return self.round_fail('未知副本类型')

        self.last_mission = mission
        return self.round_by_op_result(op.execute())

    def _on_normal_task_success(self, finished_times: int, use_power: int):
        """
        普通副本获取一次奖励时候的回调
        :param finished_times: 完成次数
        :param use_power: 使用的体力
        :return:
        """
        log.info('挑战成功 完成次数 %d 使用体力 %d', finished_times, use_power)
        self.power -= use_power
        self.ctx.power_config.add_run_times(self.last_mission.unique_id, finished_times)

    def _on_sim_uni_get_reward(self, use_power: int, user_qty: int):
        """
        模拟宇宙 获取沉浸奖励后的回调
        :return:
        """
        log.info('获取沉浸奖励 使用体力 %d 使用沉浸器 %d', use_power, user_qty)
        self.ctx.power_config.add_run_times(self.last_mission.unique_id, 1)

        self.power -= use_power
        self.qty -= user_qty

    def on_oe_get_reward(self, qty: int):
        """
        饰品提取 获取奖励后的回调
        :return:
        """
        log.info('饰品提取获取奖励 次数 %d', qty)
        for _ in range(qty):
            if self.qty > 0:  # 优先使用沉浸器
                self.qty -= 1
            elif self.power >= self.last_mission.power:
                self.power -= self.last_mission.power

            self.ctx.power_config.add_run_times(self.last_mission.unique_id, 1)

    @node_from(from_name='检查当前需要挑战的关卡')
    @node_from(from_name='执行开拓力计划', status=STATUS_NO_PLAN)
    @node_from(from_name='执行开拓力计划', status=STATUS_NO_ENOUGH_POWER)
    @node_from(from_name='执行开拓力计划', status=STATUS_PLAN_FINISHED)
    @operation_node(name='完成后返回')
    def back_at_last(self) -> OperationRoundResult:
        op = BackToNormalWorldPlus(self.ctx)
        return self.round_by_op_result(op.execute())