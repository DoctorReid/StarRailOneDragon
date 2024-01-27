from typing import List, Optional, Union, Callable, ClassVar

from basic import Rect
from basic.i18_utils import gt
from basic.log_utils import log
from sr.const import map_const
from sr.const.map_const import TransportPoint
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import Operation, StateOperation, OperationOneRoundResult, StateOperationNode, StateOperationEdge
from sr.operation.battle.wait_battle_reward import WaitBattleReward
from sr.operation.combine import CombineOperation
from sr.operation.combine.transport import Transport
from sr.operation.battle.choose_challenge_times import ChooseChallengeTimes
from sr.operation.battle.choose_support import ChooseSupport
from sr.operation.battle.choose_team import ChooseTeam
from sr.operation.battle.click_challenge import ClickChallenge
from sr.operation.battle.click_start_challenge import ClickStartChallenge
from sr.operation.battle.get_reward_and_retry import GetRewardAndRetry
from sr.operation.battle.start_fight import StartFight
from sr.operation.unit.interact import Interact
from sr.operation.unit.wait import WaitInWorld, WaitInSeconds
from sr.sim_uni.sim_uni_const import SimUniWorld, SimUniWorldEnum

CATEGORY_1 = '经验信用'
CATEGORY_2 = '光锥行迹'
CATEGORY_3 = '角色突破'
CATEGORY_4 = '遗器'
CATEGORY_5 = '模拟宇宙'
CATEGORY_LIST = [CATEGORY_1, CATEGORY_2, CATEGORY_3, CATEGORY_4, CATEGORY_5]


class TrailblazePowerPoint:

    def __init__(self, category: str, tp: Union[TransportPoint, SimUniWorld], remark: str, power: int
                 ):
        self.category: str = category
        self.tp: Union[TransportPoint, SimUniWorld] = tp
        self.remark: str = remark
        self.power: int = power

    @property
    def unique_id(self) -> str:
        return self.tp.unique_id

    @property
    def display_name(self) -> str:
        if self.category == CATEGORY_5:
            return gt(self.remark, 'ui')
        else:
            return '%s %s' % (gt(self.tp.cn[:4], 'ui'), gt(self.remark, 'ui'))


BUD_OF_MEMORIES = TrailblazePowerPoint(CATEGORY_1, map_const.P02_R02_SP04, '角色经验', 10)
BUD_OF_AETHER = TrailblazePowerPoint(CATEGORY_1, map_const.P02_R03_SP06, '光锥经验', 10)
BUD_OF_TREASURES = TrailblazePowerPoint(CATEGORY_1, map_const.P02_R10_SP08, '信用点', 10)

BUD_OF_DESTRUCTION = TrailblazePowerPoint(CATEGORY_2, map_const.P01_R03_SP05, '毁灭', 10)
BUD_OF_PRESERVATION = TrailblazePowerPoint(CATEGORY_2, map_const.P01_R04_SP04, '存护', 10)
BUD_OF_THE_HUNT = TrailblazePowerPoint(CATEGORY_2, map_const.P02_R02_SP03, '巡猎', 10)
BUD_OF_ABUNDANCE = TrailblazePowerPoint(CATEGORY_2, map_const.P02_R03_SP05, '丰饶', 10)
BUD_OF_HARMONY = TrailblazePowerPoint(CATEGORY_2, map_const.P02_R12_SP04, '同谐', 10)
BUD_OF_NIHILITY = TrailblazePowerPoint(CATEGORY_2, map_const.P02_R10_SP07, '虚无', 10)
BUD_OF_ERUDITION = TrailblazePowerPoint(CATEGORY_2, map_const.P02_R11_SP05, '智识', 10)

SHAPE_OF_QUANTA = TrailblazePowerPoint(CATEGORY_3, map_const.P01_R02_SP03, '量子', 10)
SHAPE_OF_GUST = TrailblazePowerPoint(CATEGORY_3, map_const.P02_R11_SP04, '风', 30)
SHAPE_OF_FULMINATION = TrailblazePowerPoint(CATEGORY_3, map_const.P02_R05_SP05, '雷', 30)
SHAPE_OF_BLAZE = TrailblazePowerPoint(CATEGORY_3, map_const.P02_R04_SP04, '火', 30)
SHAPE_OF_SPIKE = TrailblazePowerPoint(CATEGORY_3, map_const.P02_R10_SP05, '物理', 30)
SHAPE_OF_RIME = TrailblazePowerPoint(CATEGORY_3, map_const.P02_R05_SP06, '冰', 30)
SHAPE_OF_MIRAGE = TrailblazePowerPoint(CATEGORY_3, map_const.P02_R03_SP04, '虚数', 30)
SHAPE_OF_ICICLE = TrailblazePowerPoint(CATEGORY_3, map_const.P03_R02_SP05, '冰', 30)
SHAPE_OF_DOOM = TrailblazePowerPoint(CATEGORY_3, map_const.P03_R03_SP05, '雷', 30)
SHAPE_OF_PUPPETRY = TrailblazePowerPoint(CATEGORY_3, map_const.P03_R07_SP05, '虚数', 30)
SHAPE_OF_ABOMINATION = TrailblazePowerPoint(CATEGORY_3, map_const.P03_R09_SP04, '量子', 30)
SHAPE_OF_SCORCH = TrailblazePowerPoint(CATEGORY_3, map_const.P02_R10_SP06, '火', 30)
SHAPE_OF_CELESTIAL = TrailblazePowerPoint(CATEGORY_3, map_const.P03_R08_SP05, '风', 30)
SHAPE_OF_PERDITION = TrailblazePowerPoint(CATEGORY_3, map_const.P03_R10_SP05, '物理', 30)

PATH_OF_GELID_WIND = TrailblazePowerPoint(CATEGORY_4, map_const.P01_R03_SP06, '猎人 翔鹰', 40)
PATH_OF_JABBING_PUNCH = TrailblazePowerPoint(CATEGORY_4, map_const.P02_R04_SP05, '拳王 怪盗', 40)
PATH_OF_DRIFTING = TrailblazePowerPoint(CATEGORY_4, map_const.P02_R05_SP07, '过客 快枪手', 40)
PATH_OF_PROVIDENCE = TrailblazePowerPoint(CATEGORY_4, map_const.P02_R06_SP03, '铁卫 天才', 40)
PATH_OF_HOLY_HYMN = TrailblazePowerPoint(CATEGORY_4, map_const.P03_R02_SP06, '圣骑士 乐队', 40)
PATH_OF_CONFLAGRATION = TrailblazePowerPoint(CATEGORY_4, map_const.P03_R03_SP06, '火匠 废土客', 40)
PATH_OF_ELIXIR_SEEKERS = TrailblazePowerPoint(CATEGORY_4, map_const.P03_R08_SP06, '莳者 信使', 40)
PATH_OF_DARKNESS = TrailblazePowerPoint(CATEGORY_4, map_const.P03_R10_SP06, '大公 系囚', 40)

SIM_UNI_NORMAL_3 = TrailblazePowerPoint(CATEGORY_5, SimUniWorldEnum.WORLD_03.value, '第三世界', 40)
SIM_UNI_NORMAL_4 = TrailblazePowerPoint(CATEGORY_5, SimUniWorldEnum.WORLD_04.value, '第四世界', 40)
SIM_UNI_NORMAL_5 = TrailblazePowerPoint(CATEGORY_5, SimUniWorldEnum.WORLD_05.value, '第五世界', 40)
SIM_UNI_NORMAL_6 = TrailblazePowerPoint(CATEGORY_5, SimUniWorldEnum.WORLD_06.value, '第六世界', 40)
SIM_UNI_NORMAL_7 = TrailblazePowerPoint(CATEGORY_5, SimUniWorldEnum.WORLD_07.value, '第七世界', 40)
SIM_UNI_NORMAL_8 = TrailblazePowerPoint(CATEGORY_5, SimUniWorldEnum.WORLD_08.value, '第八世界', 40)

CATEGORY_POINT_MAP: dict[str, List[TrailblazePowerPoint]] = {
    CATEGORY_1: [BUD_OF_MEMORIES, BUD_OF_AETHER, BUD_OF_TREASURES],
    CATEGORY_2: [BUD_OF_DESTRUCTION, BUD_OF_PRESERVATION, BUD_OF_THE_HUNT, BUD_OF_ABUNDANCE, BUD_OF_HARMONY, BUD_OF_NIHILITY, BUD_OF_ERUDITION],
    CATEGORY_3: [SHAPE_OF_QUANTA, SHAPE_OF_GUST, SHAPE_OF_FULMINATION, SHAPE_OF_BLAZE, SHAPE_OF_SPIKE, SHAPE_OF_RIME, SHAPE_OF_MIRAGE,
                 SHAPE_OF_ICICLE, SHAPE_OF_DOOM, SHAPE_OF_PUPPETRY, SHAPE_OF_ABOMINATION, SHAPE_OF_SCORCH, SHAPE_OF_CELESTIAL, SHAPE_OF_PERDITION],
    CATEGORY_4: [PATH_OF_GELID_WIND, PATH_OF_JABBING_PUNCH, PATH_OF_DRIFTING, PATH_OF_PROVIDENCE, PATH_OF_HOLY_HYMN, PATH_OF_CONFLAGRATION, PATH_OF_ELIXIR_SEEKERS, PATH_OF_DARKNESS],
    CATEGORY_5: [SIM_UNI_NORMAL_3, SIM_UNI_NORMAL_4, SIM_UNI_NORMAL_5, SIM_UNI_NORMAL_6, SIM_UNI_NORMAL_7, SIM_UNI_NORMAL_8]
}


def get_point_by_unique_id(unique_id: str) -> Optional[TrailblazePowerPoint]:
    for category_list in CATEGORY_POINT_MAP.values():
        for point in category_list:
            if point.unique_id == unique_id:
                return point
    return None


class UseTrailblazePower(StateOperation):

    AFTER_BATTLE_CHALLENGE_AGAIN_BTN: ClassVar[Rect] = Rect(1180, 930, 1330, 960)  # 战斗结束后领奖励页面 【再来一次】按钮
    AFTER_BATTLE_EXIT_BTN_RECT = Rect(640, 930, 780, 960)  # 战斗结束后领奖励页面 【退出关卡】按钮

    STATUS_BATTLE_FAIL: ClassVar[str] = '挑战失败'
    STATUS_CHALLENGE_AGAIN: ClassVar[str] = '再来一次'
    STATUS_CHALLENGE_EXIT_AGAIN: ClassVar[str] = '退出关卡后再来一次'
    STATUS_FINISH_EXIT: ClassVar[str] = '挑战完成'

    def __init__(self, ctx: Context, tpp: TrailblazePowerPoint,
                 team_num: int, plan_times: int, support: Optional[str] = None,
                 on_battle_success: Optional[Callable[[int, int], None]] = None,
                 need_transport: bool = True):
        """
        使用开拓力刷本
        :param ctx: 上下文
        :param tpp: 挑战关卡
        :param team_num: 使用配队编号
        :param support: 使用支援 传入角色ID
        :param plan_times: 计划挑战次数
        :param on_battle_success: 战斗成功的回调 用于记录、扣体力等
        :param need_transport: 是否需要传送 如果出现连续两次都要挑战同一个副本 可以不传送
        """
        edges = []

        transport = StateOperationNode('传送', self._transport)
        interact = StateOperationNode('交互', self._interact)
        edges.append(StateOperationEdge(transport, interact))

        before_challenge = StateOperationNode('挑战前', self._before_click_challenge)
        edges.append(StateOperationEdge(interact, before_challenge))

        click_challenge = StateOperationNode('点击挑战', self._click_challenge)
        edges.append(StateOperationEdge(before_challenge, click_challenge))

        choose_team = StateOperationNode('选择配队', self._choose_team)
        edges.append(StateOperationEdge(click_challenge, choose_team))

        choose_support = StateOperationNode('选择支援', self._choose_support)
        edges.append(StateOperationEdge(choose_team, choose_support))

        click_start = StateOperationNode('开始挑战', self._start_challenge)
        edges.append(StateOperationEdge(choose_support, click_start))



        battle = StateOperationNode('战斗', self._battle)
        edges.append(StateOperationEdge(click_start, battle))

        edges.append(StateOperationEdge(battle, battle, status=UseTrailblazePower.STATUS_CHALLENGE_AGAIN))
        edges.append(StateOperationEdge(battle, interact, status=UseTrailblazePower.STATUS_CHALLENGE_EXIT_AGAIN))

        super().__init__(ctx, try_times=5,
                         op_name='%s %s %d' % (gt(tpp.tp.cn, 'ui'), gt('次数', 'ui'), plan_times),
                         edges=edges
                         )

        self.tpp: TrailblazePowerPoint = tpp
        self.team_num: int = team_num
        self.support: Optional[str] = support
        self.plan_times: int = plan_times  # 计划挑战次数
        self.finish_times: int = 0  # 已经完成的次数
        self.current_challenge_times: int = 1  # 当前挑战的次数
        self.need_transport: bool = True
        self.on_battle_success: Optional[Callable[[int, int], None]] = on_battle_success
        self.battle_fail_times: int = 0  # 战斗失败次数

    def _init_before_execute(self):
        super()._init_before_execute()
        self.finish_times = 0
        self.battle_fail_times = 0

    def _transport(self) -> OperationOneRoundResult:
        """
        传送
        :return:
        """
        if not self.need_transport:
            return Operation.round_success()
        op = Transport(self.ctx, self.tpp.tp)
        return Operation.round_by_op(op.execute())

    def _interact(self) -> OperationOneRoundResult:
        """
        交互进入副本
        :return:
        """
        op = Interact(self.ctx, self.tpp.tp.cn, 0.5, single_line=True, no_move=True)  # 交互进入副本
        # 等待一定时间 副本加载
        return Operation.round_by_op(op.execute(), wait=1.5)

    def _get_current_challenge_times(self) -> int:
        """
        获取当前的挑战次数
        :return:
        """
        if self.tpp.category == CATEGORY_1 or self.tpp.category == CATEGORY_2:
            current_challenge_times = self.plan_times - self.finish_times
            if current_challenge_times > 6:
                current_challenge_times = 6
            return current_challenge_times
        else:
            return 1

    def _before_click_challenge(self) -> OperationOneRoundResult:
        """
        点击挑战之前的初始化 由不同副本自行实现
        :return:
        """
        self.current_challenge_times = self._get_current_challenge_times()
        if self.tpp.category == CATEGORY_1 or self.tpp.category == CATEGORY_2:
            op = ChooseChallengeTimes(self.ctx, self.current_challenge_times)
            op_result = op.execute()
            return Operation.round_by_op(op_result)
        else:
            return Operation.round_success()

    def _click_challenge(self) -> OperationOneRoundResult:
        """
        点击挑战
        :return:
        """
        op = ClickChallenge(self.ctx)
        return Operation.round_by_op(op.execute())

    def _choose_team(self) -> OperationOneRoundResult:
        """
        选择配队
        :return:
        """
        op = ChooseTeam(self.ctx, self.team_num)
        return Operation.round_by_op(op.execute())

    def _choose_support(self):
        """
        选择支援
        :return:
        """
        if self.support is None:
            return Operation.round_success()
        op = ChooseSupport(self.ctx, self.support)
        return Operation.round_by_op(op.execute())

    def _start_challenge(self) -> OperationOneRoundResult:
        """
        开始挑战
        :return:
        """
        op = ClickStartChallenge(self.ctx)
        return Operation.round_by_op(op.execute())

    def _after_start_challenge(self) -> OperationOneRoundResult:
        """
        点击开始挑战后 进入战斗前
        :return:
        """
        if self.tpp.category == CATEGORY_3:
            op = WaitInWorld(self.ctx, wait_after_success=1)  # 等待界面
            op_result = op.execute()
            if not op_result.success:
                return Operation.round_fail('未在大世界画面')
            self.ctx.controller.initiate_attack()
            return Operation.round_success()
        else:
            return Operation.round_success()

    def _battle(self) -> OperationOneRoundResult:
        """
        战斗
        :return:
        """
        op = WaitBattleReward(self.ctx)
        op_result = op.execute()
        if not op_result.success:
            return Operation.round_by_op(op_result)

        if op_result.status == screen_state.ScreenState.TP_BATTLE_FAIL.value:
            self.battle_fail_times += 1
            if self.battle_fail_times >= 5:  # 失败次数过多 退出
                return Operation.round_fail(UseTrailblazePower.STATUS_BATTLE_FAIL)

            click = self.ocr_and_click_one_line('再来一次', UseTrailblazePower.AFTER_BATTLE_CHALLENGE_AGAIN_BTN, lcs_percent=0.1)
            if click == Operation.OCR_CLICK_SUCCESS:
                return Operation.round_success(UseTrailblazePower.STATUS_CHALLENGE_AGAIN)
            else:
                return Operation.round_retry('点击再来一次失败')
        else:
            self.finish_times += self.current_challenge_times
            if self.on_battle_success is not None:
                self.on_battle_success(self.current_challenge_times, self.tpp.power * self.current_challenge_times)

            if self.finish_times >= self.plan_times:
                click = self.ocr_and_click_one_line('退出关卡', UseTrailblazePower.AFTER_BATTLE_EXIT_BTN_RECT,
                                                    lcs_percent=0.1)
                if click == Operation.OCR_CLICK_SUCCESS:
                    return Operation.round_success(UseTrailblazePower.STATUS_FINISH_EXIT)
                else:
                    return Operation.round_retry('点击退出关卡失败')

            next_challenge_times = self._get_current_challenge_times()
            if next_challenge_times != self.current_challenge_times:
                click = self.ocr_and_click_one_line('退出关卡', UseTrailblazePower.AFTER_BATTLE_EXIT_BTN_RECT, lcs_percent=0.1)
                if click == Operation.OCR_CLICK_SUCCESS:
                    return Operation.round_success(UseTrailblazePower.STATUS_CHALLENGE_EXIT_AGAIN)
                else:
                    return Operation.round_retry('点击退出关卡失败')
            else:
                click = self.ocr_and_click_one_line('再来一次', UseTrailblazePower.AFTER_BATTLE_CHALLENGE_AGAIN_BTN, lcs_percent=0.1)
                if click == Operation.OCR_CLICK_SUCCESS:
                    return Operation.round_success(UseTrailblazePower.STATUS_CHALLENGE_AGAIN)
                else:
                    return Operation.round_retry('点击再来一次失败')
