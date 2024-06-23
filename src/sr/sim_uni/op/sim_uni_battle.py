import time
from typing import ClassVar, Optional

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.log_utils import log
from sr.const import STANDARD_CENTER_POS, OPPOSITE_DIRECTION
from sr.context.context import Context
from sr.image.sceenshot import screen_state
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.operation import Operation, OperationOneRoundResult, StateOperation, StateOperationNode, StateOperationEdge, \
    OperationResult
from sr.operation.battle.start_fight import StartFightForElite
from sr.operation.unit.team.switch_member import SwitchMember
from sr.operation.unit.technique import UseTechnique, UseTechniqueResult, FastRecover
from sr.screen_area.dialog import ScreenDialog
from sr.screen_area.screen_normal_world import ScreenNormalWorld
from sr.screen_area.screen_sim_uni import ScreenSimUni
from sr.sim_uni.op.sim_uni_choose_bless import SimUniChooseBless
from sr.sim_uni.op.sim_uni_choose_curio import SimUniChooseCurio
from sr.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig


class SimUniEnterFight(Operation):

    ATTACK_INTERVAL: ClassVar[float] = 0.2  # 发起攻击的间隔
    EXIT_AFTER_NO_ALTER_TIME: ClassVar[int] = 2  # 多久没警报退出
    EXIT_AFTER_NO_BATTLE_TIME: ClassVar[int] = 20  # 持续多久没有进入战斗画面就退出 这时候大概率是小地图判断被怪物锁定有问题

    STATUS_ENEMY_NOT_FOUND: ClassVar[str] = '未发现敌人'
    STATUS_BATTLE_FAIL: ClassVar[str] = '战斗失败'
    STATUS_STATE_UNKNOWN: ClassVar[str] = '未知状态'
    STATUS_ATTACK_FAIL: ClassVar[str] = '攻击失败'

    def __init__(self, ctx: Context,
                 config: Optional[SimUniChallengeConfig] = None,
                 disposable: bool = False,
                 no_attack: bool = False,
                 first_state: Optional[str] = None):
        """
        模拟宇宙中 主动进入战斗
        根据小地图的红圈 判断是否被敌人锁定
        """
        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('进入战斗', 'ui')))

        self.config: Optional[SimUniChallengeConfig] = ctx.sim_uni_challenge_config if config is None else config  # 挑战配置
        self.disposable: bool = disposable  # 攻击可破坏物
        self.no_attack: bool = no_attack  # 不主动攻击
        self.technique_fight: bool = False if self.config is None else self.config.technique_fight  # 是否使用秘技开怪
        self.technique_only: bool = False if self.config is None else self.config.technique_only  # 是否仅用秘技开怪
        self.first_state: Optional[str] = first_state  # 初始画面状态 传入后会跳过第一次画面状态判断

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        now = time.time()
        self.last_attack_time: float = now - SimUniEnterFight.ATTACK_INTERVAL
        self.last_alert_time: float = now  # 上次警报时间
        self.last_no_alert_time: float = now  # 上次没有警报时间
        self.last_not_in_world_time: float = now  # 上次在战斗的时间
        self.attack_times: int = 0  # 攻击次数
        self.last_attack_direction: Optional[str] = None  # 上一次攻击方向
        self.with_battle: bool = False  # 是否有进入战斗

        self.first_screen_check: bool = True  # 是否第一次检查画面状态
        self.last_state: str = ''  # 上一次的画面状态
        self.current_state: str = ''  # 这一次的画面状态

        self.ctx.pos_first_cal_pos_after_fight = True
        self.had_last_move: bool = False  # 退出这个指令前 是否已经进行过最后的移动了

        return None

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        self.last_state = self.current_state

        if self.first_screen_check and self.first_state is not None:
            self.current_state = self.first_state
        else:
            # 为了保证及时攻击 外层仅判断是否在大世界画面 非大世界画面时再细分处理
            self.current_state = screen_state.get_sim_uni_screen_state(
                screen, self.ctx.im, self.ctx.ocr,
                in_world=True, battle=True)
        self.first_screen_check = False

        log.debug('当前画面 %s', self.current_state)
        if self.current_state == ScreenState.NORMAL_IN_WORLD.value:
            if self.no_attack:
                # 适用于OP前就已经知道进入了战斗 这里只是等待战斗结束 因此只要是在大世界画面就认为完成了
                return self.round_success()

            round_result = self._try_attack(screen)
            return round_result
        elif self.current_state == ScreenState.BATTLE.value:
            round_result = self._handle_not_in_world(screen)
            self._update_not_in_world_time()
            return round_result
        else:
            return self.round_retry(SimUniEnterFight.STATUS_STATE_UNKNOWN, wait=1)

    def _update_not_in_world_time(self):
        """
        不在移动画面的情况
        更新一些统计时间
        :return:
        """
        if self.had_last_move:
            # 不是结束前移动触发的选择祝福 才能重置时间
            return
        now = time.time()
        log.debug(f'更新不在大世界的时间 {now:.4f}')
        self.last_not_in_world_time = now
        self.last_alert_time = now

    def _in_battle(self) -> Optional[OperationOneRoundResult]:
        """
        战斗
        :return:
        """
        self.with_battle = True
        self.ctx.technique_used = False
        return self.round_wait(wait=1)

    def _choose_bless(self) -> Optional[OperationOneRoundResult]:
        """
        选择祝福
        :return:
        """
        op = SimUniChooseBless(self.ctx, self.config)
        op_result = op.execute()
        if not self.disposable:
            # 黄泉秘技不会真的进入战斗 出现过祝福 就可以认为是进行过战斗了
            self.with_battle = True

        if op_result.success:
            # 成功后 必定不在选择祝福画面 应该尽快返回 继续指令 避免被怪袭击
            return self.round_wait()
        else:
            return self.round_retry(op_result.status, wait=1)

    def _choose_curio(self) -> Optional[OperationOneRoundResult]:
        """
        选择奇物
        :return:
        """
        op = SimUniChooseCurio(self.ctx, self.config)
        op_result = op.execute()

        if op_result.success:
            # 成功后 应该尽快返回 继续指令 避免被怪袭击
            return self.round_wait(wait=1)
        else:
            return self.round_retry(op_result.status, wait=1)

    def _try_attack(self, screen: MatLike) -> OperationOneRoundResult:
        """
        尝试主动攻击
        :param screen: 屏幕截图
        :return:
        """
        now_time = time.time()

        if self.disposable:
            result = self._attack(now_time)
            time.sleep(0.5)  # 攻击可破坏时 多等一会 防止刮刮乐出奖
            return result
        else:
            with_alert, attack_direction = self.ctx.yolo_detector.get_attack_direction(screen, self.last_attack_direction, now_time)
            if with_alert:
                log.debug('有告警 上一次攻击方向 %s 本次攻击方向 %s', self.last_attack_direction, attack_direction)
                self.last_alert_time = now_time
                if now_time - self.last_no_alert_time > 20:
                    # 已经在原地攻击了很久了 可能是被地形卡住了 不再尝试攻击 退出后尝试继续移动
                    return self.round_fail(SimUniEnterFight.STATUS_ATTACK_FAIL)
                if now_time - self.last_no_alert_time > 10:
                    # 已经在原地攻击了很久了 可能是被地形卡住了 尝试往告警方向移动
                    self._move_to_attack()
            else:
                log.debug('无告警')
                self.last_no_alert_time = now_time
                if now_time - self.last_alert_time > SimUniEnterFight.EXIT_AFTER_NO_ALTER_TIME:
                    # 长时间没有告警 攻击可以结束了
                    return self._exit_with_last_move()

            if now_time - self.last_not_in_world_time > SimUniEnterFight.EXIT_AFTER_NO_BATTLE_TIME:
                # 长时间没有离开大世界画面 可能是小地图背景色污染
                return self._exit_with_last_move()

            self.ctx.controller.move(direction=attack_direction)
            self.last_attack_direction = attack_direction

            current_use_tech = False  # 当前这轮使用了秘技 ctx中的状态会在攻击秘技使用后重置
            if (self.technique_fight and not self.ctx.technique_used
                    and not self.ctx.no_technique_recover_consumables  # 之前已经用完药了
                    and (self.ctx.team_info.is_buff_technique or self.ctx.team_info.is_attack_technique)):  # 识别到秘技类型才能使用
                op = UseTechnique(self.ctx,
                                  max_consumable_cnt=0 if self.config is None else self.config.max_consumable_cnt,
                                  trick_snack=self.ctx.game_config.use_quirky_snacks
                                  )
                op_result = op.execute()
                if op_result.success:
                    result_data: UseTechniqueResult = op_result.data
                    current_use_tech = result_data.use_tech
                    if (
                            (current_use_tech and self.ctx.team_info.is_buff_technique)  # 使用BUFF类秘技的时间不应该在计算内
                            or result_data.with_dialog  # 使用消耗品的时间不应该在计算内
                    ):
                        self._update_not_in_world_time()

            if self.technique_fight and self.technique_only and current_use_tech:
                # 仅秘技开怪情况下 用了秘技就不进行攻击了 用不了秘技只可能是没秘技点了 这时候可以攻击
                self.attack_times += 1
                return self.round_wait(wait_round_time=0.05)
            else:
                return self._attack(now_time)

    def _move_to_attack(self):
        """
        往之前识别的可攻击方向移动
        :return:
        """
        frame_result = self.ctx.yolo_detector.sim_uni_yolo.last_detect_result
        direction_cnt: int = 0   # 负数往左 正数往右
        if frame_result is not None:
            for result in frame_result.results:
                if result.detect_class.class_cate in ['界面提示被锁定', '界面提示可攻击']:
                    if result.x1 < STANDARD_CENTER_POS.x:
                        direction_cnt -= 1
                    else:
                        direction_cnt += 1

        if direction_cnt < 0:
            self.ctx.controller.move('a', 1)
        else:
            self.ctx.controller.move('d', 1)

    def _attack(self, now_time: float) -> OperationOneRoundResult:
        if now_time - self.last_attack_time < SimUniEnterFight.ATTACK_INTERVAL:
            return self.round_wait()
        if self.disposable and self.attack_times > 0:  # 可破坏物只攻击一次
            return self.round_success()
        self.last_attack_time = now_time
        self.ctx.controller.initiate_attack()
        self.attack_times += 1
        self.ctx.controller.stop_moving_forward()  # 攻击之后再停止移动 避免停止移动的后摇
        return self.round_wait(wait_round_time=0.5)

    def _handle_not_in_world(self, screen: MatLike) -> OperationOneRoundResult:
        """
        统一处理不在大世界画面的情况
        :param screen:
        :return:
        """
        self.ctx.detect_info.view_down = False  # 进入了非大世界画面 就将视角重置
        state = screen_state.get_sim_uni_screen_state(
            screen, self.ctx.im, self.ctx.ocr,
            in_world=False,
            battle=True,
            battle_fail=True,
            bless=True,
            curio=True,
            empty_to_close=True,
            fast_recover=True,  # 目前黄泉连续使用秘技时 弹出快速恢复的话 会触发祝福 因此处理完祝福 还需要处理快速恢复
            express_supply=True
        )
        if state == ScreenState.SIM_BLESS.value:
            return self._choose_bless()
        elif state == ScreenState.SIM_CURIOS.value:
            return self._choose_curio()
        elif state == ScreenState.EMPTY_TO_CLOSE.value:
            self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)
            return self.round_wait(wait=1)
        elif state == ScreenState.BATTLE_FAIL.value:
            self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)
            return self.round_fail(SimUniEnterFight.STATUS_BATTLE_FAIL, wait=5)
        elif state == ScreenNormalWorld.EXPRESS_SUPPLY.value.status:
            return self._claim_express_supply()
        elif state == ScreenDialog.FAST_RECOVER_TITLE.value.status:
            return self._fast_recover()
        elif state == ScreenState.BATTLE.value:
            return self._in_battle()
        else:
            return self.round_retry(SimUniEnterFight.STATUS_STATE_UNKNOWN, wait=1)

    def _claim_express_supply(self) -> OperationOneRoundResult:
        """
        领取小月卡
        :return:
        """
        get_area = ScreenNormalWorld.EXPRESS_SUPPLY_GET.value
        self.ctx.controller.click(get_area.center)
        time.sleep(3)  # 暂停一段时间再操作
        self.ctx.controller.click(get_area.center)  # 领取需要分两个阶段 点击两次
        time.sleep(1)  # 暂停一段时间再操作
        return self.round_wait()

    def _fast_recover(self) -> OperationOneRoundResult:
        """
        两种情况会出现在"快速恢复"画面
        - 由于追求连续攻击 使用秘技后仅在较短时间内判断"快速恢复"对话框是否出现 部分机器运行慢的话 对话框较久才会出现 但已经被脚本判断为无需使用消耗品
        - 模拟宇宙 黄泉连续使用秘技时 弹出快速恢复的话 会触发前一次还没出现的祝福 因此处理完祝福 还需要处理快速恢复
        因此 在这里做一个兜底判断
        :return:
        """
        op = FastRecover(self.ctx,
                         max_consumable_cnt=0 if self.config is None else self.config.max_consumable_cnt,
                         quirky_snacks=self.ctx.game_config.use_quirky_snacks)
        op_result = op.execute()
        if op_result.success:
            return self.round_wait()
        else:
            return self.round_retry(op_result.status, wait=1)

    def _exit_with_last_move(self) -> OperationOneRoundResult:
        """
        结束前再移动一次 方便触发可能出现的选择祝福
        :return:
        """
        log.debug('结束前移动')
        if self.had_last_move:
            # 已经进行过最后的移动了
            return self.round_success(None if self.with_battle else SimUniEnterFight.STATUS_ENEMY_NOT_FOUND)
        else:
            direction = self.last_attack_direction
            for i in range(2):  # 多按几次 防止被后摇吞了
                direction = 's' if direction is None else OPPOSITE_DIRECTION[direction]
                self.ctx.controller.move(direction=direction)
                time.sleep(0.25)
            self.had_last_move = True
            return self.round_wait()

    def handle_resume(self) -> None:
        """
        恢复运行后的处理 由子类实现
        :return:
        """
        self._update_not_in_world_time()

    def handle_pause(self) -> None:
        """
        暂停后的处理 由子类实现
        :return:
        """
        self.ctx.controller.stop_moving_forward()

    def _after_operation_done(self, result: OperationResult):
        super()._after_operation_done(result)
        self.ctx.controller.stop_moving_forward()


class SimUniFightElite(StateOperation):

    STATUS_ENEMY_NOT_FOUND: ClassVar[str] = '没有敌人'

    def __init__(self, ctx: Context, config: Optional[SimUniChallengeConfig] = None):
        """
        模拟宇宙 - 挑战精英、首领
        """
        edges = []

        check = StateOperationNode('检测敌人', self._check_enemy)
        technique_fight = StateOperationNode('秘技进入战斗', self._technique_fight)
        edges.append(StateOperationEdge(check, technique_fight, ignore_status=True))

        fight = StateOperationNode('战斗', self._fight)
        edges.append(StateOperationEdge(technique_fight, fight))

        switch = StateOperationNode('切换1号位', self._switch_1)
        edges.append(StateOperationEdge(fight, switch))
        edges.append(StateOperationEdge(check, switch, status=SimUniFightElite.STATUS_ENEMY_NOT_FOUND))

        super().__init__(ctx,
                         try_times=5,
                         op_name='%s %s' % (
                             gt('模拟宇宙', 'ui'),
                             gt('挑战精英首领', 'ui'),
                         ),
                         edges=edges
                         )
        self.config: Optional[SimUniChallengeConfig] = ctx.sim_uni_challenge_config if config is None else config

    def _check_enemy(self) -> OperationOneRoundResult:
        """
        判断当前是否有敌人
        :return:
        """
        area = ScreenSimUni.ENEMY_LEVEL.value
        screen = self.screenshot()

        if self.find_area(area, screen):
            return self.round_success()
        else:
            return self.round_success(SimUniFightElite.STATUS_ENEMY_NOT_FOUND)

    def _technique_fight(self) -> OperationOneRoundResult:
        op = StartFightForElite(self.ctx)
        return self.round_by_op(op.execute(), wait=1)

    def _fight(self) -> OperationOneRoundResult:
        area = ScreenSimUni.ENEMY_LEVEL.value
        screen = self.screenshot()
        if self.find_area(area, screen):  # 还没有进入战斗 可能是使用近战角色没有攻击到
            self.ctx.controller.initiate_attack()
            return self.round_retry('尝试攻击进入战斗画面')
        else:
            op = SimUniEnterFight(self.ctx, config=self.config, no_attack=True)  # 前面已经进行攻击了 这里不需要 且不额外使用秘技
            return self.round_by_op(op.execute())

    def _switch_1(self) -> OperationOneRoundResult:
        op = SwitchMember(self.ctx, 1)
        return self.round_by_op(op.execute())
