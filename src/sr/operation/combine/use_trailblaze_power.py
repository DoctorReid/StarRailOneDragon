from typing import List, Optional

from basic.i18_utils import gt
from sr.const import map_const
from sr.const.map_const import TransportPoint
from sr.context import Context
from sr.operation import Operation
from sr.operation.combine import CombineOperation
from sr.operation.combine.transport import Transport
from sr.operation.unit.battle.choose_team import ChooseTeam
from sr.operation.unit.battle.click_challenge import ClickChallenge
from sr.operation.unit.battle.click_start_challenge import ClickStartChallenge
from sr.operation.unit.battle.get_reward_and_retry import GetRewardAndRetry
from sr.operation.unit.interact import Interact

CATEGORY_1 = '经验信用'
CATEGORY_2 = '光锥技能'
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
        return '%s %s' % (gt(self.tp.cn, 'ui'), gt(self.remark, 'ui'))


BUD_OF_MEMORIES = TrailblazePowerPoint(CATEGORY_1, map_const.P02_R02_SP04, '角色经验', 10)
BUD_OF_AETHER = TrailblazePowerPoint(CATEGORY_1, map_const.P02_R03_SP06, '光锥经验', 10)
BUD_OF_TREASURES = TrailblazePowerPoint(CATEGORY_1, map_const.P02_R10_SP08, '信用点', 10)

BUD_OF_DESTRUCTION = TrailblazePowerPoint(CATEGORY_2, map_const.P01_R03_SP05, '毁灭', 10)
BUD_OF_PRESERVATION = TrailblazePowerPoint(CATEGORY_2, map_const.P01_R04_SP04, '存护', 10)
BUD_OF_THE_HUNT = TrailblazePowerPoint(CATEGORY_2, map_const.P02_R02_SP03, '巡猎', 10)
BUD_OF_ABUNDANCE = TrailblazePowerPoint(CATEGORY_2, map_const.P02_R03_SP05, '丰饶', 10)
BUD_OF_HARMONY = TrailblazePowerPoint(CATEGORY_2, map_const.P02_R12_SP04, '同谐', 10)
BUD_OF_NIHILITY = TrailblazePowerPoint(CATEGORY_2, map_const.P02_R10_SP07, '虚无', 10)
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
    CATEGORY_2: [BUD_OF_DESTRUCTION, BUD_OF_PRESERVATION, BUD_OF_THE_HUNT, BUD_OF_ABUNDANCE, BUD_OF_HARMONY, BUD_OF_NIHILITY],
    CATEGORY_3: [SHAPE_OF_QUANTA, SHAPE_OF_GUST, SHAPE_OF_FULMINATION, SHAPE_OF_BLAZE, SHAPE_OF_SPIKE, SHAPE_OF_RIME, SHAPE_OF_MIRAGE,
                 SHAPE_OF_ICICLE, SHAPE_OF_DOOM, SHAPE_OF_PUPPETRY, SHAPE_OF_ABOMINATION, SHAPE_OF_SCORCH, SHAPE_OF_CELESTIAL],
    CATEGORY_4: [PATH_OF_GELID_WIND, PATH_OF_JABBING_PUNCH, PATH_OF_DRIFTING, PATH_OF_PROVIDENCE, PATH_OF_HOLY_HYMN, PATH_OF_CONFLAGRATION, PATH_OF_ELIXIR_SEEKERS]
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

    def __init__(self, ctx: Context, tpp: TrailblazePowerPoint, team_num: int, run_times: int,
                 on_battle_success=None):
        ops: List[Operation] = [
            Transport(ctx, tpp.tp),  # 传送到对应位置
            Interact(ctx, tpp.tp.cn, 0.5),  # 交互进入副本
            ClickChallenge(ctx),  # 点击挑战
            ChooseTeam(ctx, team_num),  # 选择配队
            ClickStartChallenge(ctx),  # 开始挑战
            GetRewardAndRetry(ctx, run_times, ),  # 领奖 重复挑战
        ]

        super().__init__(ctx, ops, op_name='%s %s %d' % (gt(tpp.tp.cn, 'ui'), gt('次数', 'ui'), run_times))
        self.on_battle_success = on_battle_success

    def _on_battle_success(self):
        self.on_battle_success(self.tpp)