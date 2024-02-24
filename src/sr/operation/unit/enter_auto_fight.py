import time
from typing import ClassVar, List

from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.log_utils import log
from sr.config import game_config
from sr.context import Context
from sr.image.sceenshot import mini_map, screen_state
from sr.operation import Operation, OperationOneRoundResult
from sr.operation.unit.check_technique_point import CheckTechniquePoint
from sr.operation.unit.technique import pc_can_use_technique
from sr.screen_area.dialog import ScreenDialog


class EnterAutoFight(Operation):
    ATTACK_INTERVAL: ClassVar[float] = 0.2  # 发起攻击的间隔
    EXIT_AFTER_NO_ALTER_TIME: ClassVar[int] = 2  # 多久没警报退出
    EXIT_AFTER_NO_BATTLE_TIME: ClassVar[int] = 20  # 持续多久没有进入战斗画面就退出 这时候大概率是小地图判断被怪物锁定有问题
    ATTACK_DIRECTION_ARR: ClassVar[List] = ['w', 's', 'a', 'd']

    STATUS_ENEMY_NOT_FOUND: ClassVar[str] = '未发现敌人'
    STATUS_BATTLE_FAIL: ClassVar[str] = '战斗失败'

    def __init__(self, ctx: Context, use_technique: bool = False):
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
        self.attack_direction: int = 0  # 攻击方向
        self.use_technique: bool = use_technique  # 使用秘技开怪

    def _init_before_execute(self):
        super()._init_before_execute()
        self.last_attack_time = time.time()
        self.last_alert_time = time.time()  # 上次警报时间
        self.last_not_in_world_time = time.time() - 1.5  # 上次不在移动画面的时间
        self.attack_direction: int = 0  # 攻击方向

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        self.last_state = self.current_state
        self.current_state = screen_state.get_world_patrol_screen_state(
            screen, self.ctx.im, self.ctx.ocr,
            in_world=True, battle=True, battle_fail=True,
            fast_recover=self.use_technique)
        if self.current_state == screen_state.ScreenState.NORMAL_IN_WORLD.value:
            self._update_in_world()
            return self._try_attack(screen)
        elif self.current_state == screen_state.ScreenState.BATTLE_FAIL.value:
            self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)
            return Operation.round_fail(EnterAutoFight.STATUS_BATTLE_FAIL, wait=5)
        elif self.current_state == ScreenDialog.FAST_RECOVER_TITLE.value.text:
            result = self._recover_technique_point()
            self._update_not_in_world_time()  # 恢复秘技点的时间不应该在计算内
            return result
        elif self.current_state == screen_state.ScreenState.BATTLE.value:
            return self._in_battle()
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
        if not mini_map.is_under_attack(mm, self.ctx.game_config.mini_map_pos, strict=True):
            if now_time - self.last_alert_time > EnterAutoFight.EXIT_AFTER_NO_ALTER_TIME:
                return Operation.round_success(None if self.with_battle else EnterAutoFight.STATUS_ENEMY_NOT_FOUND)
        else:
            self.last_alert_time = now_time

        if now_time - self.last_not_in_world_time > EnterAutoFight.EXIT_AFTER_NO_BATTLE_TIME:
            return Operation.round_success(None if self.with_battle else EnterAutoFight.STATUS_ENEMY_NOT_FOUND)

        if self.use_technique and not self.ctx.is_buff_technique:  # 攻击类每次都需要使用
            self.ctx.technique_used = False

        if self.use_technique and not self.ctx.technique_used and \
                (not self.ctx.is_pc or pc_can_use_technique(screen, self.ctx.ocr, self.gc.key_technique)):  # 普通锄大地战斗后 会有一段时间才能进行操作 可以操作时 操作按键会显示出来
            technique_point = CheckTechniquePoint.get_technique_point(screen, self.ctx.ocr)
            if technique_point is None:  # 部分机器运行速度快 右上角图标出来了当下面秘技点还没出来 这时候还不能使用秘技
                pass
            elif self.ctx.is_buff_technique:
                self.ctx.controller.use_technique()
                self.ctx.technique_used = True  # 无论有没有秘技点 先设置已经使用了
                self._update_not_in_world_time()  # 使用秘技的时间不应该在计算内
            elif mini_map.with_enemy_nearby(self.ctx.im, mm):  # 攻击类只有附近有敌人时候才使用
                self.ctx.controller.use_technique()
                self.ctx.technique_used = True  # 无论有没有秘技点 先设置已经使用了

            if self.ctx.technique_used and technique_point == 0:
                self.last_alert_time += 0.5
                return Operation.round_wait(wait=0.5)

        self._attack(now_time)

        return Operation.round_wait()

    def _attack(self, now_time: float):
        if now_time - self.last_attack_time <= EnterAutoFight.ATTACK_INTERVAL:
            return
        self.last_attack_time = now_time
        if self.attack_direction > 0:
            self.ctx.controller.move(EnterAutoFight.ATTACK_DIRECTION_ARR[self.attack_direction % 4])
            time.sleep(0.2)
        self.attack_direction += 1
        self.ctx.controller.initiate_attack()
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

    def on_resume(self):
        super().on_resume()
        self._update_not_in_world_time()

    def _recover_technique_point(self) -> OperationOneRoundResult:
        """
        恢复秘技点
        :return:
        """
        self.ctx.technique_used = False  # 重置使用情况
        click = self.find_and_click_area(ScreenDialog.FAST_RECOVER_CONFIRM.value)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_wait(wait=0.5)
        else:
            return Operation.round_retry('点击确认失败', wait=1)

    def _in_battle(self) -> OperationOneRoundResult:
        """
        战斗
        :return:
        """
        self._update_not_in_world_time()
        self.with_battle = True
        self.ctx.technique_used = False
        return Operation.round_wait(wait=1)
