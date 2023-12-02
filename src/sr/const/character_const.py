from typing import List, Optional

from pydantic import BaseModel

from basic import str_utils
from basic.i18_utils import gt


class Destiny(BaseModel):

    id: str
    """命途唯一标识"""
    cn: str
    """命途中文名称"""


DESTRUCTION = Destiny(id='destruction', cn='毁灭')
PRESERVATION = Destiny(id='preservation', cn='存护')
HUNT = Destiny(id='hunt', cn='巡猎')
ABUNDANCE = Destiny(id='abundance', cn='丰饶')
NIHILITY = Destiny(id='nihility', cn='虚无')
ERUDITION = Destiny(id='erudition', cn='智识')
HARMONY = Destiny(id='harmony', cn='同谐')

DESTINY_LIST: List[Destiny] = [
    DESTRUCTION,
    PRESERVATION,
    HUNT,
    ABUNDANCE,
    NIHILITY,
    ERUDITION,
    HARMONY,
]


class Attack(BaseModel):

    id: str
    """属性唯一标识"""
    cn: str
    """属性中文名称"""


LIANGZI = Attack(id='LIANGZI', cn='量子')
WULI = Attack(id='WULI', cn='物理')
XUSHU = Attack(id='XUSHU', cn='虚数')
HUO = Attack(id='HUO', cn='火')
LEI = Attack(id='LEI', cn='雷')
BING = Attack(id='BING', cn='冰')
FENG = Attack(id='FENG', cn='风')

ATTACK_LIST = [
    LIANGZI,
    WULI,
    XUSHU,
    HUO,
    LEI,
    BING,
    FENG,
]


class Character(BaseModel):

    id: str
    """角色唯一标识"""
    cn: str
    """角色中文名称"""
    destiny: Destiny
    """命途"""
    attack: Attack
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


ARLAN = Character(id='arlan', cn='阿兰', destiny=DESTRUCTION, attack=LEI, level=4)
ASTA = Character(id='asta', cn='艾丝妲', destiny=HARMONY, attack=HUO, level=4)
BAILU = Character(id='bailu', cn='白露', destiny=ABUNDANCE, attack=LEI, level=5)
BLADE = Character(id='blade', cn='刃', destiny=DESTRUCTION, attack=FENG, level=5)
BRONYA = Character(id='bronya', cn='布洛妮娅', destiny=HARMONY, attack=FENG, level=5)
CAELUMDESTRUCTION = Character(id='caelumdestruction', cn='男开拓者毁灭', destiny=DESTRUCTION, attack=WULI, level=4)
CAELUMPRESERVATION = Character(id='caelumpreservation', cn='男开拓者存护', destiny=PRESERVATION, attack=HUO, level=4)
CLARA = Character(id='clara', cn='卡拉拉', destiny=DESTRUCTION, attack=WULI, level=5)
DANHENG = Character(id='danheng', cn='丹恒', destiny=HUNT, attack=FENG, level=4)
DANHENGIMBIBITORLUNAE = Character(id='danhengimbibitorlunae', cn='丹恒·饮月', destiny=DESTRUCTION, attack=XUSHU, level=5)
FUXUAN = Character(id='fuxuan', cn='符玄', destiny=PRESERVATION, attack=LIANGZI, level=5)
GEPARD = Character(id='gepard', cn='杰帕德', destiny=PRESERVATION, attack=BING, level=5)
GUINAIFEN = Character(id='guinaifen', cn='桂乃芬', destiny=NIHILITY, attack=HUO, level=4)
HERTA = Character(id='herta', cn='黑塔', destiny=ERUDITION, attack=BING, level=4)
HIMEKO = Character(id='himeko', cn='姬子', destiny=ERUDITION, attack=HUO, level=5)
HOOK = Character(id='hook', cn='虎克', destiny=DESTRUCTION, attack=HUO, level=4)
HUOHUO = Character(id='huohuo', cn='霍霍', destiny=ABUNDANCE, attack=FENG, level=4)
JINGLIU = Character(id='jingliu', cn='镜流', destiny=DESTRUCTION, attack=BING, level=5)
JINGYUAN = Character(id='jingyuan', cn='景元', destiny=ERUDITION, attack=LEI, level=5)
KAFKA = Character(id='kafka', cn='卡芙卡', destiny=NIHILITY, attack=LEI, level=5)
LUKA = Character(id='luka', cn='卢卡', destiny=NIHILITY, attack=WULI, level=4)
LUOCHA = Character(id='luocha', cn='罗刹', destiny=ABUNDANCE, attack=XUSHU, level=5)
LYNX = Character(id='lynx', cn='玲可', destiny=ABUNDANCE, attack=LIANGZI, level=4)
MARCH7TH = Character(id='march7th', cn='三月七', destiny=PRESERVATION, attack=BING, level=4)
NATASHA = Character(id='natasha', cn='娜塔莎', destiny=ABUNDANCE, attack=WULI, level=4)
PELA = Character(id='pela', cn='佩拉', destiny=NIHILITY, attack=BING, level=4)
QINGQUE = Character(id='qingque', cn='青雀', destiny=ERUDITION, attack=LIANGZI, level=4)
SAMPO = Character(id='sampo', cn='桑博', destiny=NIHILITY, attack=FENG, level=4)
SEELE = Character(id='seele', cn='希儿', destiny=HUNT, attack=LIANGZI, level=5)
SERVAL = Character(id='serval', cn='希露瓦', destiny=ERUDITION, attack=LEI, level=4)
SILVERWOLF = Character(id='silverwolf', cn='银狼', destiny=NIHILITY, attack=LIANGZI, level=5)
STELLEDESTRUCTION = Character(id='stelledestruction', cn='女开拓者毁灭', destiny=DESTRUCTION, attack=WULI, level=4)
STELLEPRESERVATION = Character(id='stellepreservation', cn='女开拓者存护', destiny=PRESERVATION, attack=HUO, level=4)
SUSHANG = Character(id='sushang', cn='素裳', destiny=HUNT, attack=WULI, level=4)
TINGYUN = Character(id='tingyun', cn='停云', destiny=HARMONY, attack=LEI, level=4)
TOPAZNUMBY = Character(id='topaznumby', cn='托帕&账账', destiny=HUNT, attack=HUO, level=5)
WELT = Character(id='welt', cn='瓦尔特', destiny=NIHILITY, attack=XUSHU, level=5)
YANQING = Character(id='yanqing', cn='彦卿', destiny=HUNT, attack=BING, level=5)
YUKONG = Character(id='yukong', cn='驭空', destiny=HARMONY, attack=XUSHU, level=4)

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
                          attack_id: Optional[str] = None,
                          level: Optional[int] = None,
                          character_name: Optional[str] = None) -> List[Character]:
    filter_list = []

    for c in CHARACTER_LIST:
        if destiny_id is not None and c.destiny.id != destiny_id:
            continue
        if attack_id is not None and c.attack.id != attack_id:
            continue
        if level is not None and c.level != level:
            continue
        if character_name is not None and not str_utils.find_by_lcs(character_name, gt(c.cn, 'ui'), percent=1):
            continue

        filter_list.append(c)

    filter_list.sort()

    return filter_list
