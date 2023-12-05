from typing import List, Optional

from pydantic import BaseModel

from basic import str_utils
from basic.i18_utils import gt


class CharacterPath(BaseModel):

    id: str
    """命途唯一标识"""
    cn: str
    """命途中文名称"""


CHARACTER_PATH_DESTRUCTION = CharacterPath(id='destruction', cn='毁灭')
CHARACTER_PATH_PRESERVATION = CharacterPath(id='preservation', cn='存护')
CHARACTER_PATH_HUNT = CharacterPath(id='hunt', cn='巡猎')
CHARACTER_PATH_ABUNDANCE = CharacterPath(id='abundance', cn='丰饶')
CHARACTER_PATH_NIHILITY = CharacterPath(id='nihility', cn='虚无')
CHARACTER_PATH_ERUDITION = CharacterPath(id='erudition', cn='智识')
CHARACTER_PATH_HARMONY = CharacterPath(id='harmony', cn='同谐')

DESTINY_LIST: List[CharacterPath] = [
    CHARACTER_PATH_DESTRUCTION,
    CHARACTER_PATH_PRESERVATION,
    CHARACTER_PATH_HUNT,
    CHARACTER_PATH_ABUNDANCE,
    CHARACTER_PATH_NIHILITY,
    CHARACTER_PATH_ERUDITION,
    CHARACTER_PATH_HARMONY,
]


class CharacterCombatType(BaseModel):

    id: str
    """属性唯一标识"""
    cn: str
    """属性中文名称"""

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        return self.id == other.id


QUANTUM = CharacterCombatType(id='quantum', cn='量子')
PHYSICAL = CharacterCombatType(id='physical', cn='物理')
IMAGINARY = CharacterCombatType(id='imaginary', cn='虚数')
FIRE = CharacterCombatType(id='fire', cn='火')
LIGHTNING = CharacterCombatType(id='lightning', cn='雷')
ICE = CharacterCombatType(id='ice', cn='冰')
WIND = CharacterCombatType(id='wind', cn='风')

CHARACTER_COMBAT_TYPE_LIST = [
    QUANTUM,
    PHYSICAL,
    IMAGINARY,
    FIRE,
    LIGHTNING,
    ICE,
    WIND,
]


class Character(BaseModel):

    id: str
    """角色唯一标识"""
    cn: str
    """角色中文名称"""
    path: CharacterPath
    """命途"""
    combat_type: CharacterCombatType
    """属性"""
    level: int
    """星级"""

    def __lt__(self, other):
        return self.level > other.level \
            or (self.level == other.level and self.id < other.id)

    def __eq__(self, other):
        return self.level == other.level and self.id == other.id

    def __gt__(self, other):
        return self.level > other.level or (self.level == other.level and self.id < other.id)


ARLAN = Character(id='arlan', cn='阿兰', path=CHARACTER_PATH_DESTRUCTION, combat_type=LIGHTNING, level=4)
ASTA = Character(id='asta', cn='艾丝妲', path=CHARACTER_PATH_HARMONY, combat_type=FIRE, level=4)
BAILU = Character(id='bailu', cn='白露', path=CHARACTER_PATH_ABUNDANCE, combat_type=LIGHTNING, level=5)
BLADE = Character(id='blade', cn='刃', path=CHARACTER_PATH_DESTRUCTION, combat_type=WIND, level=5)
BRONYA = Character(id='bronya', cn='布洛妮娅', path=CHARACTER_PATH_HARMONY, combat_type=WIND, level=5)
CAELUMDESTRUCTION = Character(id='caelumdestruction', cn='男主毁灭', path=CHARACTER_PATH_DESTRUCTION, combat_type=PHYSICAL, level=4)
CAELUMPRESERVATION = Character(id='caelumpreservation', cn='男主存护', path=CHARACTER_PATH_PRESERVATION, combat_type=FIRE, level=4)
CLARA = Character(id='clara', cn='卡拉拉', path=CHARACTER_PATH_DESTRUCTION, combat_type=PHYSICAL, level=5)
DANHENG = Character(id='danheng', cn='丹恒', path=CHARACTER_PATH_HUNT, combat_type=WIND, level=4)
DANHENGIMBIBITORLUNAE = Character(id='danhengimbibitorlunae', cn='丹恒·饮月', path=CHARACTER_PATH_DESTRUCTION, combat_type=IMAGINARY, level=5)
FUXUAN = Character(id='fuxuan', cn='符玄', path=CHARACTER_PATH_PRESERVATION, combat_type=QUANTUM, level=5)
GEPARD = Character(id='gepard', cn='杰帕德', path=CHARACTER_PATH_PRESERVATION, combat_type=ICE, level=5)
GUINAIFEN = Character(id='guinaifen', cn='桂乃芬', path=CHARACTER_PATH_NIHILITY, combat_type=FIRE, level=4)
HERTA = Character(id='herta', cn='黑塔', path=CHARACTER_PATH_ERUDITION, combat_type=ICE, level=4)
HIMEKO = Character(id='himeko', cn='姬子', path=CHARACTER_PATH_ERUDITION, combat_type=FIRE, level=5)
HOOK = Character(id='hook', cn='虎克', path=CHARACTER_PATH_DESTRUCTION, combat_type=FIRE, level=4)
HUOHUO = Character(id='huohuo', cn='霍霍', path=CHARACTER_PATH_ABUNDANCE, combat_type=WIND, level=4)
JINGLIU = Character(id='jingliu', cn='镜流', path=CHARACTER_PATH_DESTRUCTION, combat_type=ICE, level=5)
JINGYUAN = Character(id='jingyuan', cn='景元', path=CHARACTER_PATH_ERUDITION, combat_type=LIGHTNING, level=5)
KAFKA = Character(id='kafka', cn='卡芙卡', path=CHARACTER_PATH_NIHILITY, combat_type=LIGHTNING, level=5)
LUKA = Character(id='luka', cn='卢卡', path=CHARACTER_PATH_NIHILITY, combat_type=PHYSICAL, level=4)
LUOCHA = Character(id='luocha', cn='罗刹', path=CHARACTER_PATH_ABUNDANCE, combat_type=IMAGINARY, level=5)
LYNX = Character(id='lynx', cn='玲可', path=CHARACTER_PATH_ABUNDANCE, combat_type=QUANTUM, level=4)
MARCH7TH = Character(id='march7th', cn='三月七', path=CHARACTER_PATH_PRESERVATION, combat_type=ICE, level=4)
NATASHA = Character(id='natasha', cn='娜塔莎', path=CHARACTER_PATH_ABUNDANCE, combat_type=PHYSICAL, level=4)
PELA = Character(id='pela', cn='佩拉', path=CHARACTER_PATH_NIHILITY, combat_type=ICE, level=4)
QINGQUE = Character(id='qingque', cn='青雀', path=CHARACTER_PATH_ERUDITION, combat_type=QUANTUM, level=4)
SAMPO = Character(id='sampo', cn='桑博', path=CHARACTER_PATH_NIHILITY, combat_type=WIND, level=4)
SEELE = Character(id='seele', cn='希儿', path=CHARACTER_PATH_HUNT, combat_type=QUANTUM, level=5)
SERVAL = Character(id='serval', cn='希露瓦', path=CHARACTER_PATH_ERUDITION, combat_type=LIGHTNING, level=4)
SILVERWOLF = Character(id='silverwolf', cn='银狼', path=CHARACTER_PATH_NIHILITY, combat_type=QUANTUM, level=5)
STELLEDESTRUCTION = Character(id='stelledestruction', cn='女主毁灭', path=CHARACTER_PATH_DESTRUCTION, combat_type=PHYSICAL, level=4)
STELLEPRESERVATION = Character(id='stellepreservation', cn='女主存护', path=CHARACTER_PATH_PRESERVATION, combat_type=FIRE, level=4)
SUSHANG = Character(id='sushang', cn='素裳', path=CHARACTER_PATH_HUNT, combat_type=PHYSICAL, level=4)
TINGYUN = Character(id='tingyun', cn='停云', path=CHARACTER_PATH_HARMONY, combat_type=LIGHTNING, level=4)
TOPAZNUMBY = Character(id='topaznumby', cn='托帕&账账', path=CHARACTER_PATH_HUNT, combat_type=FIRE, level=5)
WELT = Character(id='welt', cn='瓦尔特', path=CHARACTER_PATH_NIHILITY, combat_type=IMAGINARY, level=5)
YANQING = Character(id='yanqing', cn='彦卿', path=CHARACTER_PATH_HUNT, combat_type=ICE, level=5)
YUKONG = Character(id='yukong', cn='驭空', path=CHARACTER_PATH_HARMONY, combat_type=IMAGINARY, level=4)

CHARACTER_LIST: List[Character] = [
    ARLAN,
    ASTA,
    BAILU,
    BLADE,
    BRONYA,
    CAELUMDESTRUCTION,
    CAELUMPRESERVATION,
    CLARA,
    DANHENG,
    DANHENGIMBIBITORLUNAE,
    FUXUAN,
    GEPARD,
    GUINAIFEN,
    HERTA,
    HIMEKO,
    HOOK,
    HUOHUO,
    JINGLIU,
    JINGYUAN,
    KAFKA,
    LUKA,
    LUOCHA,
    LYNX,
    MARCH7TH,
    NATASHA,
    PELA,
    QINGQUE,
    SAMPO,
    SEELE,
    SERVAL,
    SILVERWOLF,
    STELLEDESTRUCTION,
    STELLEPRESERVATION,
    SUSHANG,
    TINGYUN,
    TOPAZNUMBY,
    WELT,
    YANQING,
    YUKONG,
]


def filter_character_list(destiny_id: Optional[str] = None,
                          combat_type_id: Optional[str] = None,
                          level: Optional[int] = None,
                          character_name: Optional[str] = None) -> List[Character]:
    filter_list = []

    for c in CHARACTER_LIST:
        if destiny_id is not None and c.path.id != destiny_id:
            continue
        if combat_type_id is not None and c.combatType.id != combat_type_id:
            continue
        if level is not None and c.level != level:
            continue
        if character_name is not None and not str_utils.find_by_lcs(character_name, gt(c.cn, 'ui'), percent=1):
            continue

        filter_list.append(c)

    filter_list.sort()

    return filter_list


def get_character_by_id(c_id: str) -> Optional[Character]:
    for c in CHARACTER_LIST:
        if c.id == c_id:
            return c
    return None
