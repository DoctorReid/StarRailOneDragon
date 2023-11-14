import time
from typing import Optional

from basic.i18_utils import gt
from sr.app import Application, AppRunRecord, app_const
from sr.const import map_const
from sr.const.map_const import TransportPoint
from sr.context import Context
from sr.operation import Operation
from sr.operation.combine.transport import Transport
from sr.operation.unit.battle.choose_team import ChooseTeam
from sr.operation.unit.battle.click_challenge import ClickChallenge
from sr.operation.unit.battle.click_start_challenge import ClickStartChallenge
from sr.operation.unit.interact import Interact


class TrailblazePowerPoint:

    def __init__(self, tp: TransportPoint, remark: str):
        self.tp: TransportPoint = tp
        self.remark: str = remark


BUD_OF_MEMORIES = TrailblazePowerPoint(map_const.P02_R02_SP04, '角色经验')
BUD_OF_AETHER = TrailblazePowerPoint(map_const.P02_R03_SP06, '光锥经验')
BUD_OF_TREASURES = TrailblazePowerPoint(map_const.P02_R10_SP08, '信用点')

BUD_OF_DESTRUCTION = TrailblazePowerPoint(map_const.P01_R03_SP05, '毁灭光锥技能材料')
BUD_OF_PRESERVATION = TrailblazePowerPoint(map_const.P01_R04_SP04, '存护光锥技能材料')
BUD_OF_THE_HUNT = TrailblazePowerPoint(map_const.P02_R02_SP03, '巡猎光锥技能材料')
BUD_OF_ABUNDANCE = TrailblazePowerPoint(map_const.P02_R03_SP05, '丰饶光锥技能材料')
BUD_OF_HARMONY = TrailblazePowerPoint(map_const.P02_R12_SP04, '同谐光锥技能材料')
BUD_OF_NIHILITY = TrailblazePowerPoint(map_const.P02_R10_SP07, '虚无光锥技能材料')

SHAPE_OF_QUANTA = TrailblazePowerPoint(map_const.P01_R02_SP03, '量子属性角色晋升')
SHAPE_OF_GUST = TrailblazePowerPoint(map_const.P02_R11_SP04, '风属性角色晋升')
SHAPE_OF_FULMINATION = TrailblazePowerPoint(map_const.P02_R05_SP05, '雷属性角色晋升')
SHAPE_OF_BLAZE = TrailblazePowerPoint(map_const.P02_R04_SP04, '火属性角色晋升')
SHAPE_OF_SPIKE = TrailblazePowerPoint(map_const.P02_R10_SP05, '物理属性角色晋升')
SHAPE_OF_RIME = TrailblazePowerPoint(map_const.P02_R05_SP06, '冰属性角色晋升')
SHAPE_OF_MIRAGE = TrailblazePowerPoint(map_const.P02_R03_SP04, '虚数属性角色晋升')
SHAPE_OF_ICICLE = TrailblazePowerPoint(map_const.P03_R02_SP05, '冰属性角色晋升')
SHAPE_OF_DOOM = TrailblazePowerPoint(map_const.P03_R03_SP05, '雷属性角色晋升')
SHAPE_OF_PUPPETRY = TrailblazePowerPoint(map_const.P03_R07_SP05, '虚数属性角色晋升')
SHAPE_OF_ABOMINATION = TrailblazePowerPoint(map_const.P03_R09_SP04, '量子属性角色晋升')
SHAPE_OF_SCORCH = TrailblazePowerPoint(map_const.P02_R10_SP06, '火属性角色晋升')
SHAPE_OF_CELESTIAL = TrailblazePowerPoint(map_const.P03_R08_SP05, '风属性角色晋升')

PATH_OF_GELID_WIND = TrailblazePowerPoint(map_const.P01_R03_SP06, '遗器 猎人 翔鹰')
PATH_OF_JABBING_PUNCH = TrailblazePowerPoint(map_const.P02_R04_SP05, '遗器 拳王 怪盗')
PATH_OF_DRIFTING = TrailblazePowerPoint(map_const.P02_R05_SP07, '遗器 过客 快枪手')
PATH_OF_PROVIDENCE = TrailblazePowerPoint(map_const.P02_R06_SP03, '遗器 铁卫 天才')
PATH_OF_HOLY_HYMN = TrailblazePowerPoint(map_const.P03_R02_SP06, '遗器 圣骑士 乐队')
PATH_OF_CONFLAGRATION = TrailblazePowerPoint(map_const.P03_R03_SP06, '遗器 火匠 废土客')
PATH_OF_ELIXIR_SEEKERS = TrailblazePowerPoint(map_const.P03_R08_SP06, '遗器 莳者 信使')


class TrailblazePowerRecord(AppRunRecord):

    def __init__(self):
        super().__init__(app_const.TRAILBLAZE_POWER.id)


trailblaze_power_record: Optional[TrailblazePowerRecord] = None


def get_record() -> TrailblazePowerRecord:
    global trailblaze_power_record
    if trailblaze_power_record is None:
        trailblaze_power_record = TrailblazePowerRecord()
    return trailblaze_power_record


class TrailblazePower(Application):

    def __init__(self, ctx: Context):
        super().__init__(ctx, op_name=gt('开拓力', 'ui'))
        self.phase: int = 0

    def _execute_one_round(self) -> int:
        if self.phase == 0:  # 传送到对应位置
            op = Transport(self.ctx, PATH_OF_GELID_WIND.tp)
            if not op.execute():
                return Operation.FAIL
            else:
                self.phase += 1
                return Operation.WAIT
        elif self.phase == 1:  # 交互
            op = Interact(self.ctx, PATH_OF_GELID_WIND.tp.cn)
            if not op.execute():
                return Operation.FAIL
            else:
                self.phase += 1
                time.sleep(3)
                return Operation.WAIT
        elif self.phase == 2:  # 挑战
            op = ClickChallenge(self.ctx)
            if not op.execute():
                return Operation.FAIL
            else:
                self.phase += 1
                time.sleep(1)
                return Operation.WAIT
        elif self.phase == 3:  # 配队
            op = ChooseTeam(self.ctx, 2) # TODO
            if not op.execute():
                return Operation.FAIL
            else:
                self.phase += 1
                time.sleep(1)
                return Operation.WAIT
        elif self.phase == 4:  # 开始挑战
            op = ClickStartChallenge(self.ctx)
            if not op.execute():
                return Operation.FAIL
            else:
                self.phase += 1
                time.sleep(1)
                return Operation.WAIT


