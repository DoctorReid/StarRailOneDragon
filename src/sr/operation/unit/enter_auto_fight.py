import time
from typing import ClassVar, List, Optional

from cv2.typing import MatLike

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import mini_map, screen_state
from sr.operation import Operation, OperationOneRoundResult
from sr.operation.unit.technique import UseTechnique
from sr.screen_area.screen_normal_world import ScreenNormalWorld


class WorldPatrolEnterFight(Operation):
    ATTACK_INTERVAL: ClassVar[float] = 0.2  # 发起攻击的间隔
    EXIT_AFTER_NO_ALTER_TIME: ClassVar[int] = 2  # 多久没警报退出
    EXIT_AFTER_NO_BATTLE_TIME: ClassVar[int] = 20  # 持续多久没有进入战斗画面就退出 这时候大概率是小地图判断被怪物锁定有问题
    ATTACK_DIRECTION_ARR: ClassVar[List] = ['w', 's', 'a', 'd']

    STATUS_ENEMY_NOT_FOUND: ClassVar[str] = '未发现敌人'
    STATUS_BATTLE_FAIL: ClassVar[str] = '战斗失败'

    def __init__(self, ctx: Context,
                 technique_fight: bool = False,
                 technique_only: bool = False,
                 first_state: Optional[str] = None,
                 disposable: bool = False):
        """
        根据小地图的红圈 判断是否被敌人锁定 进行主动攻击
        """
        super().__init__(ctx, op_name=gt('进入战斗', 'ui'))
        self.last_attack_time: float = 0
        self.last_alert_time: float = 0  # 上次警报时间
        self.last_not_in_world_time: float = 0  # 上次不在移动画面的时间
        self.last_state: str = ''  # 上一次的画面状态
        self.current_state: str = ''  # 这一次的画面状态
        self.with_battle: bool = False  # 是否有进入战斗
        self.attack_times: int = 0  # 攻击次数
        self.technique_fight: bool = technique_fight  # 使用秘技开怪
        self.technique_only: bool = technique_only  # 仅使用秘技开怪
        self.first_state: Optional[str] = first_state  # 初始画面状态 传入后会跳过第一次画面状态判断
        self.first_screen_check: bool = True  # 是否第一次检查画面状态
        self.first_tech_after_battle: bool = False  # 是否战斗画面后第一次使用秘技
        self.disposable: bool = disposable  # 是否攻击可破坏物 开启时无法使用秘技

    def _init_before_execute(self):
        super()._init_before_execute()
        now = time.time()
        self.last_attack_time: float = now - WorldPatrolEnterFight.ATTACK_INTERVAL
        self.last_alert_time: float = now  # 上次警报时间
        self.last_not_in_world_time: float = now  # 上次不在移动画面的时间
        self.attack_times: int = 0  # 攻击次数
        self.first_screen_check: bool = True  # 是否第一次检查画面状态
        self.first_tech_after_battle: bool = False  # 是否战斗画面后第一次使用秘技
        self.ctx.pos_info.first_cal_pos_after_fight = True

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

        if self.current_state == screen_state.ScreenState.NORMAL_IN_WORLD.value:
            self._update_in_world()
            round_result = self._try_attack(screen)
            self.attack_times += 1
            if not self.disposable:
                self.ctx.controller.move(WorldPatrolEnterFight.ATTACK_DIRECTION_ARR[self.attack_times % 4])
            else:
                return Operation.round_success()  # 攻击破坏物只攻击一下就够了
            return round_result
        elif self.current_state == screen_state.ScreenState.BATTLE.value:
            round_result = self._handle_not_in_world(screen)
            self._update_not_in_world_time()
            return round_result
        else:
            return Operation.round_retry('未知画面', wait=1)

    def _update_in_world(self):
        """
        在大世界画面的更新
        :return:
        """
        if self.last_state != screen_state.ScreenState.NORMAL_IN_WORLD.value:
            self._update_not_in_world_time()

    def _try_attack(self, screen: MatLike) -> OperationOneRoundResult:
        """
        尝试主动攻击
        :param screen: 屏幕截图
        :return:
        """
        now_time = time.time()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        if not mini_map.is_under_attack(mm, strict=True):
            if now_time - self.last_alert_time > WorldPatrolEnterFight.EXIT_AFTER_NO_ALTER_TIME:
                return Operation.round_success(None if self.with_battle else WorldPatrolEnterFight.STATUS_ENEMY_NOT_FOUND)
        else:
            self.last_alert_time = now_time

        if now_time - self.last_not_in_world_time > WorldPatrolEnterFight.EXIT_AFTER_NO_BATTLE_TIME:
            return Operation.round_success(None if self.with_battle else WorldPatrolEnterFight.STATUS_ENEMY_NOT_FOUND)

        current_use_tech = False  # 当前这轮使用了秘技 ctx中的状态会在攻击秘技使用后重置
        if (self.technique_fight and not self.ctx.technique_used
                and not self.ctx.no_technique_recover_consumables  # 之前已经用完药了
                and (self.ctx.team_info.is_buff_technique or self.ctx.team_info.is_attack_technique)):  # 识别到秘技类型才能使用
            op = UseTechnique(self.ctx, max_consumable_cnt=self.ctx.world_patrol_config.max_consumable_cnt,
                              need_check_available=self.ctx.is_pc and self.first_tech_after_battle,  # 只有战斗结束刚出来的时候可能用不了秘技
                              quirky_snacks=self.ctx.game_config.use_quirky_snacks
                              )
            op_result = op.execute()
            current_use_tech = op_result.data
            self.first_tech_after_battle = False
            if current_use_tech and self.ctx.team_info.is_buff_technique:
                self._update_not_in_world_time()  # 使用BUFF类秘技的时间不应该在计算内

        if self.technique_fight and self.technique_only and current_use_tech:
            # 仅秘技开怪情况下 用了秘技就不进行攻击了 用不了秘技只可能是没秘技点了 这时候可以攻击
            pass
        else:
            self._attack(now_time)

        return Operation.round_wait()

    def _attack(self, now_time: float):
        if now_time - self.last_attack_time < WorldPatrolEnterFight.ATTACK_INTERVAL:
            return
        if self.disposable and self.attack_times > 0:
            return
        self.last_attack_time = now_time
        self.ctx.controller.initiate_attack()
        self.ctx.controller.stop_moving_forward()  # 攻击之后再停止移动 避免停止移动的后摇
        time.sleep(0.5)

    def _update_not_in_world_time(self):
        """
        不在移动画面的情况
        更新一些统计时间
        :return:
        """
        now = time.time()
        self.last_not_in_world_time = now
        self.last_alert_time = now

    def on_resume(self, e=None):
        super().on_resume()
        self._update_not_in_world_time()

    def _handle_not_in_world(self, screen: MatLike) -> OperationOneRoundResult:
        """
        统一处理不在大世界的情况
        :return:
        """
        state = screen_state.get_world_patrol_screen_state(
            screen, self.ctx.im, self.ctx.ocr,
            in_world=False, battle=True, battle_fail=True,
            express_supply=True)

        if state == screen_state.ScreenState.BATTLE_FAIL.value:
            self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)
            return Operation.round_fail(WorldPatrolEnterFight.STATUS_BATTLE_FAIL, wait=5)
        elif state == ScreenNormalWorld.EXPRESS_SUPPLY.value.status:
            return self._claim_express_supply()
        elif state == screen_state.ScreenState.BATTLE.value:
            return self._in_battle()
        else:
            return Operation.round_retry('未知画面', wait=1)

    def _in_battle(self) -> OperationOneRoundResult:
        """
        战斗
        :return:
        """
        self.with_battle = True
        self.ctx.technique_used = False
        self.first_tech_after_battle = True
        return Operation.round_wait(wait=1)

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

        return Operation.round_wait()
