from typing import Optional, List, ClassVar, Callable

from basic import str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.app.app_description import AppDescriptionEnum
from sr.app.app_run_record import AppRunRecord
from sr.app.application_base import Application
from sr.app.sim_uni.sim_uni_run_record import SimUniRunRecord
from sr.app.sim_uni.sim_uni_run_world import SimUniRunWorld
from sr.const import phone_menu_const
from sr.context import Context
from sr.image.sceenshot import screen_state, mini_map
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.interastral_peace_guide.choose_guide_mission import ChooseGuideMission
from sr.interastral_peace_guide.choose_guide_tab import ChooseGuideTab
from sr.interastral_peace_guide.guide_const import GuideTabEnum, GuideCategoryEnum, GuideMissionEnum
from sr.operation import OperationResult, Operation, StateOperationEdge, StateOperationNode, \
    OperationOneRoundResult
from sr.operation.unit.back_to_world import BackToWorld
from sr.operation.unit.interact import Interact
from sr.operation.unit.menu.click_phone_menu_item import ClickPhoneMenuItem
from sr.operation.unit.menu.open_phone_menu import OpenPhoneMenu
from sr.screen_area.interastral_peace_guide import ScreenGuide
from sr.screen_area.screen_normal_world import ScreenNormalWorld
from sr.screen_area.screen_sim_uni import ScreenSimUni
from sr.sim_uni.op.choose_sim_uni_category import ChooseSimUniCategory
from sr.sim_uni.op.choose_sim_uni_diff import ChooseSimUniDiff
from sr.sim_uni.op.choose_sim_uni_num import ChooseSimUniNum
from sr.sim_uni.op.choose_sim_uni_path import ChooseSimUniPath
from sr.sim_uni.op.sim_uni_battle import SimUniEnterFight
from sr.sim_uni.op.sim_uni_claim_weekly_reward import SimUniClaimWeeklyReward
from sr.sim_uni.op.sim_uni_exit import SimUniExit
from sr.sim_uni.op.sim_uni_start import SimUniStart
from sr.sim_uni.sim_uni_const import SimUniTypeEnum, SimUniPath, SimUniWorldEnum


class SimUniApp(Application):

    STATUS_NOT_FOUND_IN_SI: ClassVar[str] = '生存索引中未找到模拟宇宙'
    STATUS_ALL_FINISHED: ClassVar[str] = '已完成通关次数'
    STATUS_EXCEPTION: ClassVar[str] = '异常次数过多'

    def __init__(self, ctx: Context,
                 specified_uni_num: Optional[int] = None,
                 max_reward_to_get: int = 0,
                 get_reward_callback: Optional[Callable[[int, int], None]] = None):
        """
        模拟宇宙应用 需要在大世界中非战斗、非特殊关卡界面中开启
        :param ctx:
        """
        edges: List[StateOperationEdge] = []

        check_times = StateOperationNode('检查运行次数', self._check_times)
        check_initial_screen = StateOperationNode('检查初始画面', self._check_initial_screen)
        edges.append(StateOperationEdge(check_times, check_initial_screen))

        check_reward_before_exit = StateOperationNode('领取每周奖励', op=SimUniClaimWeeklyReward(ctx))
        edges.append(StateOperationEdge(check_times, check_reward_before_exit, status=SimUniApp.STATUS_ALL_FINISHED))

        back_to_world = StateOperationNode('退出', op=BackToWorld(ctx))  # 无论是否领取成功都退出
        edges.append(StateOperationEdge(check_reward_before_exit, back_to_world, ignore_status=True))
        edges.append(StateOperationEdge(check_reward_before_exit, back_to_world, success=False, ignore_status=True))

        open_menu = StateOperationNode('菜单', op=OpenPhoneMenu(ctx))
        edges.append(StateOperationEdge(check_initial_screen, open_menu, ignore_status=True))

        choose_guide = StateOperationNode('指南', op=ClickPhoneMenuItem(ctx, phone_menu_const.INTERASTRAL_GUIDE))
        edges.append(StateOperationEdge(open_menu, choose_guide))
        edges.append(StateOperationEdge(check_initial_screen, choose_guide,
                                        status=ScreenState.PHONE_MENU.value))  # 在菜单的时候 打开指南

        choose_survival_index = StateOperationNode('指南中选择生存索引', op=ChooseGuideTab(ctx, GuideTabEnum.TAB_2.value))
        edges.append(StateOperationEdge(choose_guide, choose_survival_index))
        edges.append(StateOperationEdge(check_initial_screen, choose_survival_index,
                                        status=ScreenState.GUIDE.value))  # 在指南里 选择生存索引

        choose_in_si = StateOperationNode('生存索引中选择模拟宇宙', self.choose_in_survival_index)
        edges.append(StateOperationEdge(choose_survival_index, choose_in_si))
        edges.append(StateOperationEdge(check_initial_screen, choose_in_si,
                                        status=ScreenState.GUIDE_SURVIVAL_INDEX.value))  # 在生存索引 选择模拟宇宙

        choose_sim_category = StateOperationNode('指南中选择模拟宇宙', op=ChooseGuideTab(ctx, GuideTabEnum.TAB_3.value))
        edges.append(StateOperationEdge(choose_in_si, choose_sim_category, status=self.STATUS_NOT_FOUND_IN_SI))

        choose_in_su = StateOperationNode('模拟宇宙中选择模拟宇宙', self.choose_in_sim_uni)
        edges.append(StateOperationEdge(choose_sim_category, choose_in_su))

        si_transport = StateOperationNode('生存索引中传送', op=ChooseGuideMission(ctx, GuideMissionEnum.SIM_UNI_00.value))
        edges.append(StateOperationEdge(choose_in_si, si_transport))

        su_transport = StateOperationNode('模拟宇宙中传送', op=ChooseGuideMission(ctx, GuideMissionEnum.SIM_UNI_00.value))
        edges.append(StateOperationEdge(choose_in_su, su_transport))

        choose_normal_universe = StateOperationNode('普通宇宙', op=ChooseSimUniCategory(ctx, SimUniTypeEnum.NORMAL))
        edges.append(StateOperationEdge(si_transport, choose_normal_universe))
        edges.append(StateOperationEdge(su_transport, choose_normal_universe))
        edges.append(StateOperationEdge(check_initial_screen, choose_normal_universe,
                                        status=ScreenState.SIM_TYPE_EXTEND.value))  # 拓展装置 选择模拟宇宙

        choose_universe_num = StateOperationNode('选择世界', self._choose_sim_uni_num)
        edges.append(StateOperationEdge(choose_normal_universe, choose_universe_num))
        edges.append(StateOperationEdge(check_initial_screen, choose_universe_num,
                                        status=ScreenState.SIM_TYPE_NORMAL.value))  # 模拟宇宙 选择世界

        choose_universe_diff = StateOperationNode('选择难度', self._choose_sim_uni_diff)
        edges.append(StateOperationEdge(choose_universe_num, choose_universe_diff,
                                        status=ChooseSimUniNum.STATUS_RESTART))

        start_sim = StateOperationNode('开始挑战', op=SimUniStart(ctx))
        edges.append(StateOperationEdge(choose_universe_diff, start_sim))
        edges.append(StateOperationEdge(choose_universe_num, start_sim,
                                        status=ChooseSimUniNum.STATUS_CONTINUE))

        choose_path = StateOperationNode('选择命途', self._choose_path)
        edges.append(StateOperationEdge(start_sim, choose_path, status=SimUniStart.STATUS_RESTART))

        run_world = StateOperationNode('通关', self._run_world)
        edges.append(StateOperationEdge(choose_path, run_world))
        edges.append(StateOperationEdge(start_sim, run_world, status=ChooseSimUniNum.STATUS_CONTINUE))

        # 战斗成功
        check_times_to_continue = StateOperationNode('继续检查运行次数', self._check_times)
        edges.append(StateOperationEdge(run_world, check_times_to_continue))
        edges.append(StateOperationEdge(check_times_to_continue, choose_universe_num))
        edges.append(StateOperationEdge(check_times_to_continue, check_reward_before_exit, status=SimUniApp.STATUS_ALL_FINISHED))
        edges.append(StateOperationEdge(check_times_to_continue, check_reward_before_exit, status=SimUniApp.STATUS_EXCEPTION))

        # 战斗失败
        fail_click_empty = StateOperationNode('战斗失败结算', self._fail_click_empty)
        edges.append(StateOperationEdge(run_world, fail_click_empty,
                                        success=False, status=SimUniEnterFight.STATUS_BATTLE_FAIL))
        edges.append(StateOperationEdge(fail_click_empty, check_times_to_continue))

        if not ctx.one_dragon_config.is_debug:  # 任何异常错误都退出当前宇宙 调试模式下不退出 直接失败等待处理
            exception_exit = StateOperationNode('异常退出', self._exception_exit)
            edges.append(StateOperationEdge(run_world, exception_exit,
                                            success=False, ignore_status=True))
            edges.append(StateOperationEdge(exception_exit, check_times_to_continue))

        self.run_record: SimUniRunRecord = ctx.sim_uni_run_record
        super().__init__(ctx, try_times=5,
                         op_name=gt(AppDescriptionEnum.SIM_UNIVERSE.value.cn, 'ui'),
                         edges=edges, specified_start_node=check_times,
                         run_record=self.run_record)

        self.current_uni_num: int = 0  # 当前运行的第几宇宙 启动时会先完成运行中的宇宙

        self.specified_uni_num: Optional[int] = specified_uni_num  # 指定宇宙 用于沉浸奖励
        self.max_reward_to_get: int = max_reward_to_get  # 最多获取多少次奖励
        self.get_reward_cnt: int = 0  # 当前获取的奖励次数
        self.get_reward_callback: Optional[Callable[[int, int], None]] = get_reward_callback  # 获取奖励后的回调

        self.exception_times: int = 0  # 异常出现次数

    def _init_before_execute(self):
        super()._init_before_execute()
        self.get_reward_cnt = 0
        self.exception_times: int = 0
        self.not_found_in_survival_times: int = 0  # 在生存索引中找不到模拟宇宙的次数

        Application.get_preheat_executor().submit(self.preheat)

    def preheat(self):
        """
        预热
        - 提前加载需要的模板
        - 角度匹配用的矩阵
        :return:
        """
        self.ctx.ih.preheat_for_world_patrol()
        mini_map.preheat()

    def _check_times(self) -> OperationOneRoundResult:
        if self.specified_uni_num is not None:
            if self.get_reward_cnt < self.max_reward_to_get:
                return self.round_success()
            else:
                return self.round_success(SimUniApp.STATUS_ALL_FINISHED)

        if self.exception_times >= 10:
            return self.round_success(SimUniApp.STATUS_EXCEPTION)

        log.info('本日通关次数 %d 本周通关次数 %d', self.run_record.daily_times, self.run_record.weekly_times)
        if self.run_record.run_status_under_now == AppRunRecord.STATUS_SUCCESS:
            return self.round_success(SimUniApp.STATUS_ALL_FINISHED)
        else:
            return self.round_success()

    def _fail_click_empty(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        area = ScreenSimUni.EXIT_EMPTY_TO_CONTINUE.value

        click = self.find_and_click_area(area, screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return self.round_success(wait=2)
        else:
            return self.round_retry('未在结算画面', wait=1)

    def _interact_in_herta(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        if not self.find_area(ScreenNormalWorld.CHARACTER_ICON.value, screen):
            return self.round_retry('等待大世界画面', wait=1)

        op = Interact(self.ctx, '模拟宇宙', lcs_percent=0.1, single_line=True, no_move=True)
        op_result = op.execute()
        if op_result.success:
            return self.round_success(wait=2)
        else:
            return self.round_fail('加载失败')

    def _check_initial_screen(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        return self.round_success(screen_state.get_sim_uni_initial_screen_state(screen, self.ctx.im, self.ctx.ocr))

    def _transport(self) -> OperationOneRoundResult:
        """
        点击传送
        :return:
        """
        area_list = [
            ScreenSimUni.GUIDE_TRANSPORT_1.value,
            ScreenSimUni.GUIDE_TRANSPORT_2.value
        ]
        screen = self.screenshot()
        for area in area_list:
            click = self.find_and_click_area(area, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                return self.round_success(wait=3)

        return self.round_retry('点击传送失败', wait=1)

    def _choose_sim_uni_num(self) -> OperationOneRoundResult:
        if self.specified_uni_num is None:
            world = SimUniWorldEnum[self.ctx.sim_uni_config.weekly_uni_num]
        else:
            world = SimUniWorldEnum['WORLD_%02d' % self.specified_uni_num]
        op = ChooseSimUniNum(self.ctx, world.value.idx)
        op_result = op.execute()
        if op_result.success:
            self.current_uni_num = op_result.data  # 使用OP的结果 可能选的并不是原来要求的
            self.ctx.sim_uni_info.world_num = self.current_uni_num
        else:
            self.ctx.sim_uni_info.world_num = 0
        return self.round_by_op(op_result)

    def _choose_sim_uni_diff(self) -> OperationOneRoundResult:
        op = ChooseSimUniDiff(self.ctx, self.ctx.sim_uni_config.weekly_uni_diff)
        return self.round_by_op(op.execute())

    def _choose_path(self) -> OperationOneRoundResult:
        """
        选择命途
        :return:
        """
        cfg = self.ctx.sim_uni_config.get_challenge_config(self.current_uni_num)
        op = ChooseSimUniPath(self.ctx, SimUniPath[cfg.path])
        return self.round_by_op(op.execute())

    def _run_world(self) -> OperationOneRoundResult:
        uni_challenge_config = self.ctx.sim_uni_config.get_challenge_config(self.current_uni_num)
        get_reward = self.current_uni_num == self.specified_uni_num  # 只有当前宇宙和开拓力需要的宇宙是同一个 才能拿奖励

        op = SimUniRunWorld(self.ctx, self.current_uni_num,
                            config=uni_challenge_config,
                            op_callback=self.on_world_finished,
                            max_reward_to_get=self.max_reward_to_get - self.get_reward_cnt if get_reward else 0,
                            get_reward_callback=self._on_sim_uni_get_reward if get_reward else None
                            )
        return self.round_by_op(op.execute())

    def _on_sim_uni_get_reward(self, use_power: int, user_qty: int):
        self.get_reward_cnt += 1
        if self.get_reward_callback is not None:
            self.get_reward_callback(use_power, user_qty)

    def on_world_finished(self, op_result: OperationResult):
        if op_result.success and op_result.status == SimUniRunWorld.STATUS_SUCCESS:
            log.info('成功通过 记录次数+1')
            self.run_record.add_times()

    def _exception_exit(self) -> OperationOneRoundResult:
        self.exception_times += 1
        op = SimUniExit(self.ctx)
        return self.round_by_op(op.execute())

    def choose_in_survival_index(self) -> OperationOneRoundResult:
        """
        在生存索引中 选择模拟宇宙
        开启差分宇宙后 就没有这个选项了
        :return:
        """
        screen = self.screenshot()

        area = ScreenGuide.SURVIVAL_INDEX_CATE.value
        part = cv2_utils.crop_image_only(screen, area.rect)

        target = GuideCategoryEnum.SI_SIM_UNI.value
        ocr_result_map = self.ctx.ocr.run_ocr(part)

        for k, v in ocr_result_map.items():
            # 看有没有目标
            if str_utils.find_by_lcs(gt(target.cn, 'ocr'), k, 0.55):
                to_click = v.max.center + area.rect.left_top
                log.info('生存索引中找到 %s 尝试点击', target.cn)
                if self.ctx.controller.click(to_click):
                    return self.round_success(wait=0.5)

        self.not_found_in_survival_times += 1
        if self.not_found_in_survival_times > 1:
            return self.round_success(status=self.STATUS_NOT_FOUND_IN_SI)
        else:
            return self.round_retry(wait=0.5)

    def choose_in_sim_uni(self) -> OperationOneRoundResult:
        """
        在指南-模拟宇宙中 选择模拟宇宙
        开启差分宇宙后 就有这个选项了
        :return:
        """
        screen = self.screenshot()

        area = ScreenGuide.SURVIVAL_INDEX_CATE.value
        part = cv2_utils.crop_image_only(screen, area.rect)

        target = GuideCategoryEnum.SI_SIM_UNI.value
        ocr_result_map = self.ctx.ocr.run_ocr(part)

        for k, v in ocr_result_map.items():
            # 看有没有目标
            if str_utils.find_by_lcs(gt(target.cn, 'ocr'), k, 0.55):
                to_click = v.max.center + area.rect.left_top
                log.info('生存索引中找到 %s 尝试点击', target.cn)
                if self.ctx.controller.click(to_click):
                    return self.round_success(wait=0.5)

        self.not_found_in_survival_times += 1
        if self.not_found_in_survival_times > 1:
            return self.round_fail(status='找不到模拟宇宙')
        else:
            return self.round_retry(wait=0.5)
