from typing import List, Optional

from basic.i18_utils import gt
from basic.log_utils import log
from sr.const import map_const
from sr.const.map_const import TransportPoint
from sr.context import Context
from sr.operation import Operation
from sr.operation.combine import CombineOperation
from sr.operation.combine.transport import Transport
from sr.operation.unit.battle.choose_challenge_times import ChooseChallengeTimes
from sr.operation.unit.battle.choose_support import ChooseSupport
from sr.operation.unit.battle.choose_team import ChooseTeam
from sr.operation.unit.battle.click_challenge import ClickChallenge
from sr.operation.unit.battle.click_start_challenge import ClickStartChallenge
from sr.operation.unit.battle.get_reward_and_retry import GetRewardAndRetry
from sr.operation.unit.battle.start_fight import StartFight
from sr.operation.unit.interact import Interact
from sr.operation.unit.wait_in_seconds import WaitInSeconds
from sr.operation.unit.wait_in_world import WaitInWorld

CATEGORY_1 = '经验信用'
CATEGORY_2 = '光锥行迹'
CATEGORY_3 = '角色突破'
CATEGORY_4 = '遗器'
CATEGORY_LIST = [CATEGORY_1, CATEGORY_2, CATEGORY_3, CATEGORY_4]


class TrailblazePowerPoint:

    def __init__(self, category: str, tp: TransportPoint, remark: str, power: int):
        self.category: str = category
        self.tp: TransportPoint = tp
        self.remark: str = remark
        self.power: int = power

    @property
    def unique_id(self) -> str:
        return self.tp.unique_id

    @property
    def display_name(self) -> str:
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

CATEGORY_POINT_MAP: dict[str, List[TrailblazePowerPoint]] = {
    CATEGORY_1: [BUD_OF_MEMORIES, BUD_OF_AETHER, BUD_OF_TREASURES],
    CATEGORY_2: [BUD_OF_DESTRUCTION, BUD_OF_PRESERVATION, BUD_OF_THE_HUNT, BUD_OF_ABUNDANCE, BUD_OF_HARMONY, BUD_OF_NIHILITY, BUD_OF_ERUDITION],
    CATEGORY_3: [SHAPE_OF_QUANTA, SHAPE_OF_GUST, SHAPE_OF_FULMINATION, SHAPE_OF_BLAZE, SHAPE_OF_SPIKE, SHAPE_OF_RIME, SHAPE_OF_MIRAGE,
                 SHAPE_OF_ICICLE, SHAPE_OF_DOOM, SHAPE_OF_PUPPETRY, SHAPE_OF_ABOMINATION, SHAPE_OF_SCORCH, SHAPE_OF_CELESTIAL, SHAPE_OF_PERDITION],
    CATEGORY_4: [PATH_OF_GELID_WIND, PATH_OF_JABBING_PUNCH, PATH_OF_DRIFTING, PATH_OF_PROVIDENCE, PATH_OF_HOLY_HYMN, PATH_OF_CONFLAGRATION, PATH_OF_ELIXIR_SEEKERS, PATH_OF_DARKNESS]
}


def get_point_by_unique_id(unique_id: str) -> Optional[TrailblazePowerPoint]:
    for category_list in CATEGORY_POINT_MAP.values():
        for point in category_list:
            if point.unique_id == unique_id:
                return point
    return None


class UseTrailblazePower(CombineOperation):
    """
    使用开拓里刷本
    """

    def __init__(self, ctx: Context, tpp: TrailblazePowerPoint,
                 team_num: int, run_times: int, support: Optional[str] = None,
                 on_battle_success=None, need_transport: bool = True):
        """

        :param ctx: 上下文
        :param tpp: 挑战关卡
        :param team_num: 使用配队编号
        :param support: 使用支援 传入角色ID
        :param run_times: 执行次数
        :param on_battle_success: 战斗成功的回调 用于记录、扣体力等
        :param need_transport: 是否需要传送 如果出现连续两次都要挑战同一个副本 可以不传送
        """
        self.ctx: Context = ctx
        self.tpp: TrailblazePowerPoint = tpp
        self.team_num: int = team_num
        self.support: Optional[str] = support
        self.run_times: int = run_times
        self.on_battle_success = on_battle_success

        self.current_success_round: int = 0  # 第几轮战斗胜利
        self.trigger_success_times_arr = []  # 每轮战斗胜利触发多少次回调

        ops: List[Operation] = []
        if need_transport:  # 传送到对应位置
            ops.append(Transport(ctx, tpp.tp))

        if tpp.category in (CATEGORY_1, CATEGORY_2):
            times_6 = run_times // 6
            times_left = run_times % 6
            if times_6 > 0:
                for i in self._ops_for_cate_12(6, times_6):
                    ops.append(i)
                for _ in range(times_6):
                    self.trigger_success_times_arr.append(6)
            if times_left > 0:
                for i in self._ops_for_cate_12(times_left, 1):
                    ops.append(i)
                self.trigger_success_times_arr.append(times_left)
        elif tpp.category == CATEGORY_3:
            for i in self._ops_for_cate_3(run_times):
                ops.append(i)
            for _ in range(run_times):
                self.trigger_success_times_arr.append(1)
        elif tpp.category == CATEGORY_4:
            for i in self._ops_for_cate_4(run_times):
                ops.append(i)
            for _ in range(run_times):
                self.trigger_success_times_arr.append(1)

        super().__init__(ctx, ops, op_name='%s %s %d' % (gt(tpp.tp.cn, 'ui'), gt('次数', 'ui'), run_times))

    def _ops_for_cate_12(self, times_per_round: int, round_num: int) -> List[Operation]:
        """
        拟造花萼金的挑战指令 - 经验、信用、光锥技能材料
        :param times_per_round: 每轮挑战次数
        :param round_num: 挑战多少轮
        :return:
        """
        return [
            Interact(self.ctx, self.tpp.tp.cn, 0.5),  # 交互进入副本
            WaitInSeconds(self.ctx, 1.5),  # 等待副本加载
            ChooseChallengeTimes(self.ctx, times_per_round),  # 挑战次数
            ClickChallenge(self.ctx),  # 点击挑战
            ChooseTeam(self.ctx, self.team_num),  # 选择配队
            ChooseSupport(self.ctx, self.support),  # 选择支援
            ClickStartChallenge(self.ctx),  # 开始挑战
            GetRewardAndRetry(self.ctx, round_num, need_confirm=False, success_callback=self._on_battle_success),  # 领奖 重复挑战
            WaitInWorld(self.ctx),  # 等待主界面
        ]

    def _ops_for_cate_3(self, round_num: int) -> List[Operation]:
        """
        凝滞虚影的挑战指令 - 角色突破材料
        :param round_num: 挑战多少轮
        :return:
        """
        return [
            Interact(self.ctx, self.tpp.tp.cn, 0.5),  # 交互进入副本
            WaitInSeconds(self.ctx, 1.5),  # 等待副本加载
            ClickChallenge(self.ctx),  # 点击挑战
            ChooseTeam(self.ctx, self.team_num),  # 选择配队
            ChooseSupport(self.ctx, self.support),  # 选择支援
            ClickStartChallenge(self.ctx),  # 开始挑战
            WaitInWorld(self.ctx),  # 等待界面
            StartFight(self.ctx),  # 主动攻击
            GetRewardAndRetry(self.ctx, round_num, need_confirm=False, success_callback=self._on_battle_success),  # 领奖 重复挑战
            WaitInWorld(self.ctx),  # 等待主界面
        ]

    def _ops_for_cate_4(self, round_num: int) -> List[Operation]:
        """
        侵蚀隧洞的挑战指令 - 遗器
        :param round_num: 挑战多少轮
        :return:
        """
        return [
            Interact(self.ctx, self.tpp.tp.cn, 0.5),  # 交互进入副本
            WaitInSeconds(self.ctx, 1.5),  # 等待副本加载
            ClickChallenge(self.ctx),  # 点击挑战
            ChooseTeam(self.ctx, self.team_num),  # 选择配队
            ChooseSupport(self.ctx, self.support),  # 选择支援
            ClickStartChallenge(self.ctx),  # 开始挑战
            GetRewardAndRetry(self.ctx, round_num, need_confirm=False, success_callback=self._on_battle_success),  # 领奖 重复挑战
            WaitInWorld(self.ctx),  # 等待主界面
        ]

    def _on_battle_success(self):
        if self.on_battle_success is None:
            return
        if self.current_success_round < len(self.trigger_success_times_arr):
            for _ in range(self.trigger_success_times_arr[self.current_success_round]):
                self.on_battle_success()
            self.current_success_round += 1
        else:
            log.error('胜利次数多余预期 %s %s', self.current_success_round, self.trigger_success_times_arr)