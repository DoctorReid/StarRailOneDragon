import time
from typing import ClassVar, Optional, List

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.log_utils import log
from sr.const import OPPOSITE_DIRECTION
from sr.context.context import Context
from sr.image.sceenshot import screen_state
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.operation import Operation, OperationOneRoundResult
from sr.operation.unit.technique import UseTechnique, UseTechniqueResult, FastRecover
from sr.screen_area.dialog import ScreenDialog
from sr.screen_area.screen_normal_world import ScreenNormalWorld


class WorldPatrolEnterFight(Operation):
    ATTACK_INTERVAL: ClassVar[float] = 0.2  # 发起攻击的间隔
    EXIT_AFTER_NO_ALTER_TIME: ClassVar[int] = 2  # 多久没警报退出
    EXIT_AFTER_NO_BATTLE_TIME: ClassVar[int] = 20  # 持续多久没有进入战斗画面就退出 这时候大概率是小地图判断被怪物锁定有问题

    STATUS_ENEMY_NOT_FOUND: ClassVar[str] = '未发现敌人'
    STATUS_BATTLE_FAIL: ClassVar[str] = '战斗失败'
    STATUS_EXIT_WITH_ALERT: ClassVar[str] = '退出但有告警'

    def __init__(self, ctx: Context,
                 technique_fight: bool = False,
                 technique_only: bool = False,
                 first_state: Optional[str] = None,
                 disposable: bool = False):
        """
        根据小地图的红圈 判断是否被敌人锁定 进行主动攻击
        """
        super().__init__(ctx, op_name=gt('进入战斗', 'ui'))
        self.technique_fight: bool = technique_fight  # 使用秘技开怪
        self.technique_only: bool = technique_only  # 仅使用秘技开怪
        self.first_state: Optional[str] = first_state  # 初始画面状态 传入后会跳过第一次画面状态判断
        self.disposable: bool = disposable  # 是否攻击可破坏物 开启时无法使用秘技

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
        self.last_attack_time: float = now - WorldPatrolEnterFight.ATTACK_INTERVAL
        self.last_alert_time: float = now  # 上次警报时间
        self.last_not_in_world_time: float = now  # 上次不在移动画面的时间
        self.attack_times: int = 0  # 攻击次数
        self.last_attack_direction: str = 's'  # 上一次攻击方向
        self.attack_direction_history: List[str] = []  # 攻击方向的历史记录

        self.with_battle: bool = False  # 是否有进入战斗
        self.first_screen_check: bool = True  # 是否第一次检查画面状态
        self.last_state: str = ''  # 上一次的画面状态
        self.current_state: str = ''  # 这一次的画面状态
        self.first_tech_after_battle: bool = False  # 是否战斗画面后第一次使用秘技
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
            self.current_state = screen_state.get_world_patrol_screen_state(
                screen, self.ctx.im, self.ctx.ocr,
                in_world=True, battle=True)

        self.first_screen_check = False

        if self.current_state == ScreenState.NORMAL_IN_WORLD.value:
            self._update_in_world()

            round_result = self._try_attack(screen)
            return round_result
        elif self.current_state == ScreenState.BATTLE.value:
            round_result = self._handle_not_in_world(screen)
            self._update_not_in_world_time()
            return round_result
        else:
            return self.round_retry('未知画面', wait=1)

    def _update_in_world(self):
        """
        在大世界画面的更新
        :return:
        """
        if self.last_state != ScreenState.NORMAL_IN_WORLD.value:
            self._update_not_in_world_time()

    def _try_attack(self, screen: MatLike) -> OperationOneRoundResult:
        """
        尝试主动攻击
        :param screen: 屏幕截图
        :return:
        """
        now_time = time.time()
        if self.disposable:
            result = self._attack(now_time)
            return result
        else:
            with_alert, attack_direction = self.ctx.yolo_detector.get_attack_direction(screen, self.last_attack_direction, now_time)
            if with_alert:
                log.debug('有告警')
                self.last_alert_time = now_time
            else:
                log.debug('无告警')
                if now_time - self.last_alert_time > WorldPatrolEnterFight.EXIT_AFTER_NO_ALTER_TIME:
                    # 长时间没有告警 攻击可以结束了
                    return self._exit_with_last_move(with_alert)

            if now_time - self.last_not_in_world_time > WorldPatrolEnterFight.EXIT_AFTER_NO_BATTLE_TIME:
                # 长时间没有离开大世界画面 可能是人物卡住了 攻击不到怪
                return self._exit_with_last_move(with_alert)

            fix_attack_direction = self.fix_and_record_direction(attack_direction)
            self.ctx.controller.move(direction=fix_attack_direction)

            current_use_tech = False  # 当前这轮使用了秘技 ctx中的状态会在攻击秘技使用后重置
            if (self.technique_fight and not self.ctx.technique_used
                    and not self.ctx.no_technique_recover_consumables  # 之前已经用完药了
                    and (self.ctx.team_info.is_buff_technique or self.ctx.team_info.is_attack_technique)):  # 识别到秘技类型才能使用
                op = UseTechnique(self.ctx, max_consumable_cnt=self.ctx.world_patrol_config.max_consumable_cnt,
                                  need_check_available=self.ctx.is_pc and self.first_tech_after_battle,  # 只有战斗结束刚出来的时候可能用不了秘技
                                  trick_snack=self.ctx.game_config.use_quirky_snacks
                                  )
                op_result = op.execute()
                if op_result.success:
                    op_result_data: UseTechniqueResult = op_result.data
                    current_use_tech = op_result_data.use_tech
                    self.first_tech_after_battle = False
                    if (
                            (current_use_tech and self.ctx.team_info.is_buff_technique)  # 使用BUFF类秘技的时间不应该在计算内
                            or op_result_data.with_dialog  # 使用消耗品的时间不应该在计算内
                    ):
                        self._update_not_in_world_time()

            if self.technique_fight and self.technique_only and current_use_tech:
                # 仅秘技开怪情况下 用了秘技就不进行攻击了 用不了秘技只可能是没秘技点了 这时候可以攻击
                self.attack_times += 1
                return self.round_wait(wait_round_time=0.05)
            else:
                return self._attack(now_time)

    def _attack(self, now_time: float) -> OperationOneRoundResult:
        if now_time - self.last_attack_time < WorldPatrolEnterFight.ATTACK_INTERVAL:
            return self.round_wait()
        if self.disposable and self.attack_times > 0:  # 可破坏物只攻击一次
            return self.round_success()
        self.last_attack_time = now_time
        self.ctx.controller.initiate_attack()
        self.attack_times += 1
        self.ctx.controller.stop_moving_forward()  # 攻击之后再停止移动 避免停止移动的后摇
        return self.round_wait(wait=0.5)

    def _update_not_in_world_time(self):
        """
        不在移动画面的情况
        更新一些统计时间
        :return:
        """
        now = time.time()
        log.debug(f'更新不在大世界的时间 {now:.4f}')
        self.last_not_in_world_time = now
        self.last_alert_time = now

    def handle_resume(self) -> None:
        """
        恢复运行后的处理 由子类实现
        :return:
        """
        self._update_not_in_world_time()

    def _handle_not_in_world(self, screen: MatLike) -> OperationOneRoundResult:
        """
        统一处理不在大世界的情况
        :return:
        """
        state = screen_state.get_world_patrol_screen_state(
            screen, self.ctx.im, self.ctx.ocr,
            in_world=False, battle=True, battle_fail=True,
            express_supply=True, fast_recover=True)
        log.debug('当前画面 %s', state)

        if state == ScreenState.BATTLE_FAIL.value:
            self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)
            return self.round_fail(WorldPatrolEnterFight.STATUS_BATTLE_FAIL, wait=5)
        elif state == ScreenNormalWorld.EXPRESS_SUPPLY.value.status:
            return self._claim_express_supply()
        elif state == ScreenDialog.FAST_RECOVER_TITLE.value.status:
            return self.handle_fast_recover()
        elif state == ScreenState.BATTLE.value:
            return self._in_battle()
        else:
            return self.round_retry('未知画面', wait=1)

    def _in_battle(self) -> OperationOneRoundResult:
        """
        战斗
        :return:
        """
        self.with_battle = True
        self.ctx.technique_used = False
        self.first_tech_after_battle = True
        return self.round_wait(wait=1)

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

    def handle_fast_recover(self) -> OperationOneRoundResult:
        """
        由于追求连续攻击 使用秘技后仅在较短时间内判断"快速恢复"对话框是否出现
        部分机器运行慢的话 对话框较久才会出现 但已经被脚本判断为无需使用消耗品
        因此 在这里做一个兜底判断
        :return:
        """
        op = FastRecover(self.ctx,
                         max_consumable_cnt=self.ctx.world_patrol_config.max_consumable_cnt,
                         quirky_snacks=self.ctx.game_config.use_quirky_snacks
                         )
        # 可能把战斗中的文字错误识别成【快速恢复】 因此允许失败
        return self.round_by_op(op.execute(), retry_on_fail=True)

    def _exit_with_last_move(self, with_alert: bool = False) -> OperationOneRoundResult:
        """
        结束前再移动一次 取消掉后摇 才能继续后续指令
        :param with_alert: 退出时 是否仍然有告警。有的话说明卡住了
        :return:
        """
        log.debug('结束前移动')
        if self.had_last_move:  # 已经进行过最后的移动了
            if with_alert:  # 仍然有告警 最后进入战斗失败了
                return self.round_success(WorldPatrolEnterFight.STATUS_EXIT_WITH_ALERT)
            else:
                return self.round_success(None if self.with_battle else WorldPatrolEnterFight.STATUS_ENEMY_NOT_FOUND)
        else:
            move_direction = 's' if self.last_attack_direction is None else OPPOSITE_DIRECTION[self.last_attack_direction]
            self.ctx.controller.move(direction=move_direction)
            time.sleep(0.25)
            self.had_last_move = True
            return self.round_wait()

    def fix_and_record_direction(self, attack_direction: str) -> str:
        """
        修正攻击方向 同时记录
        - 目前攻击有左右判定 但远程怪不靠近的情况下 可能会导致角色一直在左右攻击
        :return:
        """
        if self.ctx.controller.is_moving and self.attack_times == 0:
            # 目前是直接攻击再松开w 这样避免停止移动带来的后摇 因此第一下攻击一定是在按着w的情况下进行的 攻击方向会固定为前方
            self.last_attack_direction = 'w'
        else:
            last_idx = len(self.attack_direction_history) - 1
            ad_count = 0  # 左右攻击的计数
            ws_count = 0  # 前后攻击的计数
            last_ws = None  # 上一次前后攻击的方向
            to_count = 8
            for _ in range(to_count):
                if last_idx < 0:
                    break
                if self.attack_direction_history[last_idx] in ['a', 'd']:
                    ad_count += 1
                else:
                    ws_count += 1
                    last_ws = self.attack_direction_history[last_idx]

            if ad_count >= to_count - 1 and ws_count <= 1:
                self.last_attack_direction = OPPOSITE_DIRECTION.get(last_ws, 's')
            else:
                self.last_attack_direction = attack_direction

        self.attack_direction_history.append(self.last_attack_direction)
        return self.last_attack_direction
