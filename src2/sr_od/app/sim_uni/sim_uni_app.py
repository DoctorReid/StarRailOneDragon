from typing import Optional, List, ClassVar, Callable

from one_dragon.base.operation.operation_edge import node_from
from one_dragon.base.operation.operation_node import operation_node
from one_dragon.base.operation.operation_round_result import OperationRoundResult
from one_dragon.utils.log_utils import log
from sr_od.app.sim_uni import sim_uni_screen_state
from sr_od.app.sim_uni.operations.sim_uni_claim_weekly_reward import SimUniClaimWeeklyReward
from sr_od.app.sr_application import SrApplication
from sr_od.context.sr_context import SrContext


class SimUniApp(SrApplication):

    STATUS_NOT_FOUND_IN_SI: ClassVar[str] = '生存索引中未找到模拟宇宙'
    STATUS_ALL_FINISHED: ClassVar[str] = '已完成通关次数'
    STATUS_EXCEPTION: ClassVar[str] = '异常次数过多'
    STATUS_TO_WEEKLY_REWARD: ClassVar[str] = '领取每周奖励'

    def __init__(self, ctx: SrContext,
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

        choose_in_si = StateOperationNode('生存索引中选择模拟宇宙', self.choose_category_in_survival_index)
        edges.append(StateOperationEdge(choose_survival_index, choose_in_si))
        edges.append(StateOperationEdge(check_initial_screen, choose_in_si,
                                        status=ScreenState.GUIDE_SURVIVAL_INDEX.value))  # 在生存索引 选择模拟宇宙

        choose_sim_category = StateOperationNode('指南中选择模拟宇宙', op=ChooseGuideTab(ctx, GuideTabEnum.TAB_3.value))
        edges.append(StateOperationEdge(choose_in_si, choose_sim_category, status=self.STATUS_NOT_FOUND_IN_SI))

        choose_in_su = StateOperationNode('模拟宇宙中选择模拟宇宙', self.choose_category_in_sim_uni)
        edges.append(StateOperationEdge(choose_sim_category, choose_in_su))

        si_transport = StateOperationNode('生存索引中传送', op=ChooseGuideMission(ctx, GuideMissionEnum.SIM_UNI_00.value))
        edges.append(StateOperationEdge(choose_in_si, si_transport))

        su_transport = StateOperationNode('模拟宇宙中传送', op=ChooseGuideMission(ctx, GuideMissionEnum.SIM_UNI_NORMAL.value))
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
        self.not_found_in_survival_times: int = 0  # 在生存索引中找不到模拟宇宙的次数
        self.all_finished: bool = False

    def preheat(self):
        """
        预热
        - 提前加载需要的模板
        - 角度匹配用的矩阵
        :return:
        """
        self.ctx.ih.preheat_for_world_patrol()
        mini_map.preheat()

    @operation_node(name='检查运行次数', is_start_node=True)
    def _check_times(self) -> OperationRoundResult:
        if self.specified_uni_num is not None:
            if self.get_reward_cnt < self.max_reward_to_get:
                return self.round_success()
            else:
                self.all_finished = True
                return self.round_success(SimUniApp.STATUS_ALL_FINISHED)

        if self.exception_times >= 10:
            return self.round_success(SimUniApp.STATUS_EXCEPTION)

        log.info('本日精英次数 %d 本周精英次数 %d', self.run_record.elite_daily_times, self.run_record.elite_weekly_times)
        if (self.run_record.elite_daily_times >= self.ctx.sim_uni_config.elite_daily_times
                or self.run_record.elite_weekly_times >= self.ctx.sim_uni_config.elite_weekly_times):
            self.all_finished = True
            return self.round_success(SimUniApp.STATUS_ALL_FINISHED)
        else:
            return self.round_success()

    @node_from(from_name='检查运行次数')
    @operation_node(name='识别初始画面')
    def _check_initial_screen(self) -> OperationRoundResult:
        screen = self.screenshot()
        state = sim_uni_screen_state.get_sim_uni_initial_screen_state(self.ctx, screen)

        if state == sim_uni_screen_state.ScreenState.SIM_TYPE_NORMAL.value:
            if self.all_finished:
                return self.round_success(SimUniApp.STATUS_TO_WEEKLY_REWARD)
        return self.round_success(state)

    def _transport(self) -> OperationRoundResult:
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

    def _choose_sim_uni_num(self) -> OperationRoundResult:
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

    def _choose_sim_uni_diff(self) -> OperationRoundResult:
        op = ChooseSimUniDiff(self.ctx, self.ctx.sim_uni_config.weekly_uni_diff)
        return self.round_by_op(op.execute())

    def _choose_path(self) -> OperationRoundResult:
        """
        选择命途
        :return:
        """
        cfg = self.ctx.sim_uni_config.get_challenge_config(self.current_uni_num)
        op = ChooseSimUniPath(self.ctx, SimUniPath[cfg.path])
        return self.round_by_op(op.execute())

    def _run_world(self) -> OperationRoundResult:
        uni_challenge_config = self.ctx.sim_uni_config.get_challenge_config(self.current_uni_num)
        get_reward = self.current_uni_num == self.specified_uni_num  # 只有当前宇宙和开拓力需要的宇宙是同一个 才能拿奖励

        op = SimUniRunWorld(self.ctx, self.current_uni_num,
                            config=uni_challenge_config,
                            max_reward_to_get=self.max_reward_to_get - self.get_reward_cnt if get_reward else 0,
                            get_reward_callback=self._on_sim_uni_get_reward if get_reward else None
                            )
        return self.round_by_op(op.execute())

    def _on_sim_uni_get_reward(self, use_power: int, user_qty: int):
        self.get_reward_cnt += 1
        if self.get_reward_callback is not None:
            self.get_reward_callback(use_power, user_qty)

    def _exception_exit(self) -> OperationRoundResult:
        self.exception_times += 1
        op = SimUniExit(self.ctx)
        return self.round_by_op(op.execute())

    def choose_category_in_survival_index(self) -> OperationRoundResult:
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

    def choose_category_in_sim_uni(self) -> OperationRoundResult:
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

    @node_from(from_name='识别初始画面', status=STATUS_TO_WEEKLY_REWARD)
    @operation_node(name='领取每周奖励')
    def check_reward_before_exit(self) -> OperationRoundResult:
        op = SimUniClaimWeeklyReward(self.ctx)
        return self.round_by_op_result(op.execute())
