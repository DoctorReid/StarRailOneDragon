from typing import Optional, List, Dict

from basic import cal_utils, Rect, Point
from basic.i18_utils import gt


class Planet:

    def __init__(self, num: int, i: str, cn: str):
        self.num: int = num  # 编号 用于强迫症给文件排序
        self.id: str = i  # 用在找文件夹之类的
        self.cn: str = cn  # 中文

    def __str__(self):
        return '%02d - %s' % (self.num, self.cn)

    @property
    def n_id(self):
        """
        编号ID
        :return:
        """
        return 'P%02d' % self.num

    @property
    def np_id(self):
        """
        带编号的唯一ID
        :return:
        """
        return '%s_%s' % (self.n_id, self.id)

    @property
    def display_name(self):
        return gt(self.cn, 'ui')


P01 = Planet(1, "KJZHT", "空间站黑塔")
P02 = Planet(2, "YLL6", "雅利洛")
P03 = Planet(3, "XZLF", "仙舟罗浮")

PLANET_LIST = [P01, P02, P03]


def get_planet_by_cn(cn: str) -> Planet:
    """
    根据星球的中文 获取对应常量
    :param cn: 星球中文
    :return: 常量
    """
    for i in PLANET_LIST:
        if i.cn == cn:
            return i
    return None


class Region:

    def __init__(self, num: int, i: str, cn: str, planet: Planet, floor: int = 0):
        self.num: int = num  # 编号 方便列表排序
        self.id: str = i  # id 用在找文件夹之类的
        self.cn: str = cn  # 中文 用在OCR
        self.planet: Planet = planet
        self.floor: int = floor

    def __str__(self):
        return '%s - %s' % (self.cn, self.id)

    @property
    def r_id(self) -> str:
        """
        星球+区域ID 用于不区分楼层的场景
        :return:
        """
        return 'R%02d_%s' % (self.num, self.id)

    @property
    def pr_id(self) -> str:
        """
        星球+区域ID 用于不区分楼层的场景
        :return:
        """
        return '%s_%s' % (self.planet.np_id, self.r_id)

    @property
    def l_str(self) -> str:
        """
        层数 正数用 l1 负数用 b1
        :return:
        """
        if self.floor == 0:
            return ''
        elif self.floor > 0:
            return '_F%d' % self.floor
        elif self.floor < 0:
            return '_B%d' % abs(self.floor)

    @property
    def rl_id(self) -> str:
        """
        区域在星球下的唯一ID 用于文件夹
        :return 区域id + 楼层id
        """
        return '%s%s' % (self.r_id, self.l_str)

    @property
    def prl_id(self) -> str:
        """
        区域唯一ID 用于唯一标识
        :return 星球id + 区域id + 楼层id
        """
        return '%s_%s' % (self.planet.np_id, self.rl_id)

    @property
    def another_floor(self) -> bool:
        return self.floor != 0

    @property
    def display_name(self) -> str:
        return gt(self.cn, 'ui')


# 空间站黑塔
P01_R00 = Region(0, "GJCX", "观景车厢", None)
P01_R01 = Region(1, "ZKCD", "主控舱段", P01)
P01_R02 = Region(2, "JZCD", "基座舱段", P01)
P01_R03_B1 = Region(3, "SRCD", "收容舱段", P01, -1)
P01_R03_L1 = Region(3, "SRCD", "收容舱段", P01, 1)
P01_R03_L2 = Region(3, "SRCD", "收容舱段", P01, 2)
P01_R04_L1 = Region(4, "ZYCD", "支援舱段", P01, 1)
P01_R04_L2 = Region(4, "ZYCD", "支援舱段", P01, 2)
P01_R05_L1 = Region(5, "JBCD", "禁闭舱段", P01, 1)
P01_R05_L2 = Region(5, "JBCD", "禁闭舱段", P01, 2)
P01_R05_L3 = Region(5, "JBCD", "禁闭舱段", P01, 3)

# 雅利洛
P02_R01_L1 = Region(1, "XZQ", "行政区", P02, floor=1)
P02_R01_B1 = Region(1, "XZQ", "行政区", P02, floor=-1)
P02_R02 = Region(2, "CJXY", "城郊雪原", P02)
P02_R03 = Region(3, "BYTL", "边缘通路", P02)
P02_R04 = Region(4, "TWJQ", "铁卫禁区", P02)
P02_R05 = Region(5, "CXHL", "残响回廊", P02)
P02_R06 = Region(6, "YDL", "永冬岭", P02)
P02_R07 = Region(7, "ZWZZ", "造物之柱", P02)
P02_R08_L2 = Region(8, "JWQSYC", "旧武器试验场", P02, floor=2)
P02_R09 = Region(9, "PYZ", "磐岩镇", P02)
P02_R10 = Region(10, "DKQ", "大矿区", P02)
P02_R11_L1 = Region(11, "MDZ", "铆钉镇", P02, floor=1)
P02_R11_L2 = Region(11, "MDZ", "铆钉镇", P02, floor=2)
P02_R12_L1 = Region(12, "JXJL", "机械聚落", P02, floor=1)
P02_R12_L2 = Region(12, "JXJL", "机械聚落", P02, floor=2)

# 仙舟罗浮
P03_R01 = Region(1, "XCHZS", "星槎海中枢", P03)
P03_R02_L1 = Region(2, "LYD", "流云渡", P03, floor=1)
P03_R02_L2 = Region(2, "LYD", "流云渡", P03, floor=2)
P03_R03_L1 = Region(3, "HXG", "廻星港", P03, floor=1)
P03_R03_L2 = Region(3, "HXG", "廻星港", P03, floor=2)
P03_R04 = Region(4, "CLT", "长乐天", P03)
P03_R05 = Region(5, "JRX", "金人巷", P03)
P03_R06_L1 = Region(6, "TBS", "太卜司", P03, floor=1)
P03_R06_L2 = Region(6, "TBS", "太卜司", P03, floor=2)
P03_R07 = Region(7, "GZS", "工造司", P03)
P03_R08_L1 = Region(8, "DDS", "丹鼎司", P03, floor=1)
P03_R08_L2 = Region(8, "DDS", "丹鼎司", P03, floor=2)
P03_R09 = Region(9, "LYJ", "鳞渊境", P03)
P03_R10 = Region(10, "SY", "绥园", P03)

# 这里的顺序需要保持和界面上的区域顺序一致
PLANET_2_REGION: Dict[str, List[Region]] = {
    P01.np_id: [P01_R01, P01_R02, P01_R03_L1, P01_R03_L2, P01_R03_B1, P01_R04_L1, P01_R04_L2, P01_R05_L1, P01_R05_L2, P01_R05_L3],
    P02.np_id: [P02_R01_L1, P02_R01_B1, P02_R02, P02_R03, P02_R04, P02_R05, P02_R06, P02_R07, P02_R08_L2, P02_R09, P02_R10,
                P02_R11_L1, P02_R11_L2, P02_R12_L1, P02_R12_L2],
    P03.np_id: [P03_R01, P03_R02_L1, P03_R02_L2, P03_R03_L1, P03_R03_L2, P03_R04, P03_R05, P03_R06_L1, P03_R06_L2,
                P03_R07, P03_R08_L1, P03_R08_L2, P03_R09, P03_R10]
}


def get_region_by_cn(cn: str, planet: Planet, floor: int = 0) -> Region:
    """
    根据区域的中文 获取对应常量
    :param cn: 区域的中文
    :param planet: 所属星球 传入后会判断 为以后可能重名准备
    :param floor: 层数
    :return: 常量
    """
    for i in PLANET_2_REGION[planet.np_id]:
        if i.cn != cn:
            continue
        if floor is not None and i.floor != floor:
            continue
        return i
    return None


class TransportPoint:

    def __init__(self, id: str, cn: str, region: Region, template_id: str, lm_pos: tuple, tp_pos: Optional[tuple] = None):
        self.id: str = id  # 英文 用在找图
        self.cn: str = cn  # 中文 用在OCR
        self.region: Region = region  # 所属区域
        self.planet: Planet = region.planet  # 所属星球
        self.template_id: str = template_id  # 匹配模板
        self.lm_pos: Point = Point(lm_pos[0], lm_pos[1])  # 在大地图的坐标
        self.tp_pos: Point = Point(tp_pos[0], tp_pos[1]) if tp_pos is not None else self.lm_pos  # 传送落地的坐标

    def __str__(self):
        return '%s - %s' % (self.cn, self.id)

    @property
    def display_name(self):
        return gt(self.cn, 'ui')

    @property
    def unique_id(self):
        return '%s_%s' % (self.region.prl_id, self.id)


# 空间站黑塔 - 主控舱段
P01_R01_SP01 = TransportPoint('JCY', '监察域', P01_R01, 'mm_tp_03', (529, 231), (562, 243))
P01_R01_SP02 = TransportPoint('HXTL', '核心通路', P01_R01, 'mm_tp_03', (592, 691), (563, 678))
P01_R01_SP03 = TransportPoint('HTDBGS', '黑塔的办公室', P01_R01, 'mm_tp_04', (245, 796), (245, 770))  # 这个比较特殊 需要走出办公室才是这个坐标
P01_R01_SP04 = TransportPoint('FSSQ', '封锁扇区', P01_R01, 'mm_sp_01', (228, 744))
P01_R01_SP05 = TransportPoint('TKDT', '太空电梯', P01_R01, 'mm_sp_02', (562, 837))
P01_R01_SP06 = TransportPoint('NGZY', '内购专员', P01_R01, 'mm_sp_04', (535, 628))

# 空间站黑塔 - 基座舱段
P01_R02_SP01 = TransportPoint('JKS', '监控室', P01_R02, 'mm_tp_03', (635, 143), (642, 133))
P01_R02_SP02 = TransportPoint('JDZX', '接待中心', P01_R02, 'mm_tp_03', (493, 500), (503, 496))
P01_R02_SP03 = TransportPoint('KHZX', '空海之形凝滞虚影', P01_R02, 'mm_tp_06', (540, 938), (554, 923))
P01_R02_SP04 = TransportPoint('TKDT', '太空电梯', P01_R02, 'mm_sp_02', (556, 986))

# 空间站黑塔 - 收容舱段
P01_R03_SP01 = TransportPoint('ZT', '中庭', P01_R03_L1, 'mm_tp_03', (626, 346), (618, 330))
P01_R03_SP02 = TransportPoint('KZZXW', '控制中心外', P01_R03_L1, 'mm_tp_03', (372, 375), (385, 368))
P01_R03_SP03 = TransportPoint('TSJXS', '特殊解析室', P01_R03_L2, 'mm_tp_03', (765, 439), (752, 448))
P01_R03_SP04 = TransportPoint('WMZJ', '无明之间', P01_R03_L1, 'mm_tp_03', (1040, 510), (1009, 515))
P01_R03_SP05 = TransportPoint('HMZL', '毁灭之蕾拟造花萼赤', P01_R03_L1, 'mm_tp_07', (316, 325), (319, 335))
P01_R03_SP06 = TransportPoint('SFZJ', '霜风之径侵蚀隧洞', P01_R03_L1, 'mm_tp_09', (847, 367), (841, 368))
P01_R03_SP07 = TransportPoint('LJZZ', '裂界征兆', P01_R03_L1, 'mm_sp_01', (459, 342))
P01_R03_SP08 = TransportPoint('TKDT', '太空电梯', P01_R03_L1, 'mm_sp_02', (607, 364))

# 空间站黑塔 - 支援舱段
P01_R04_SP01 = TransportPoint('BJKF', '备件库房', P01_R04_L2, 'mm_tp_03', (434, 240), (454, 232))
P01_R04_SP02 = TransportPoint('YT', '月台', P01_R04_L2, 'mm_tp_03', (789, 404), (799, 393))
P01_R04_SP03 = TransportPoint('DLS', '电力室', P01_R04_L2, 'mm_tp_03', (165, 414), (137, 380))
P01_R04_SP04 = TransportPoint('CHZL', '存护之蕾拟造花萼赤', P01_R04_L2, 'mm_tp_07', (467, 322), (476, 330))
P01_R04_SP05 = TransportPoint('TKDT', '太空电梯', P01_R04_L2, 'mm_sp_02', (105, 345))
P01_R04_SP06 = TransportPoint('HMDKD', '毁灭的开端历战回响', P01_R04_L2, 'mm_boss_01', (1010, 286), (1015, 295))

# 空间站黑塔 - 禁闭舱段
P01_R05_SP01 = TransportPoint('WC', '温床', P01_R05_L2, 'mm_tp_03', (684, 306), (710, 309))
P01_R05_SP02 = TransportPoint('WC', '集散中心', P01_R05_L3, 'mm_tp_03', (642, 500), (609, 481))
P01_R05_SP03 = TransportPoint('PYM', '培养皿', P01_R05_L1, 'mm_tp_03', (669, 560), (677, 540))
P01_R05_SP04 = TransportPoint('YWZBJ', '药物制备间', P01_R05_L2, 'mm_tp_03', (541, 796), (530, 800))
P01_R05_SP05 = TransportPoint('ZXDJY', '蛀星的旧靥历战回响', P01_R05_L1, 'mm_boss_04', (571, 526), (582, 529))

# 雅利洛 - 行政区
P02_R01_SP01 = TransportPoint('HJGJY', '黄金歌剧院', P02_R01_L1, 'mm_tp_03', (603, 374), (619, 380))
P02_R01_SP02 = TransportPoint('ZYGC', '中央广场', P02_R01_L1, 'mm_tp_03', (487, 806), (501, 801))
P02_R01_SP03 = TransportPoint('GDBG', '歌德宾馆', P02_R01_L1, 'mm_tp_03', (784, 1173), (776, 1183))
P02_R01_SP04 = TransportPoint('LSWHBWG', '历史文化博物馆', P02_R01_L1, 'mm_tp_05', (395, 771))
P02_R01_SP05 = TransportPoint('CJXY', '城郊雪原', P02_R01_L1, 'mm_sp_02', (485, 370))
P02_R01_SP06 = TransportPoint('BYTL', '边缘通路', P02_R01_L1, 'mm_sp_02', (508, 1113))
P02_R01_SP07 = TransportPoint('TWJQ', '铁卫禁区', P02_R01_L1, 'mm_sp_02', (792, 1259))
P02_R01_SP08 = TransportPoint('SHJ1', '售货机1', P02_R01_L1, 'mm_sp_03', (672, 521))
P02_R01_SP09 = TransportPoint('SS', '书商', P02_R01_L1, 'mm_sp_03', (641, 705))
P02_R01_SP10 = TransportPoint('MBR', '卖报人', P02_R01_L1, 'mm_sp_03', (610, 806))
P02_R01_SP11 = TransportPoint('XZQSD', '行政区商店', P02_R01_L1, 'mm_sp_03', (639, 906))
P02_R01_SP12 = TransportPoint('SHJ2', '售货机2', P02_R01_L1, 'mm_sp_03', (697, 1187))
P02_R01_SP13 = TransportPoint('HDCX', '花店长夏', P02_R01_L1, 'mm_sp_05', (602, 588))
P02_R01_SP14 = TransportPoint('KLBB1', '克里珀堡1', P02_R01_L1, 'mm_sp_05', (769, 732))
P02_R01_SP15 = TransportPoint('KLBB2', '克里珀堡2', P02_R01_L1, 'mm_sp_05', (769, 878))
P02_R01_SP16 = TransportPoint('JWXYD', '机械屋永动', P02_R01_L1, 'mm_sp_05', (727, 918))
P02_R01_SP17 = TransportPoint('GDBGRK', '歌德宾馆入口', P02_R01_L1, 'mm_sp_05', (627, 1152))  # 这个跟传送点冲突 区分一下
P02_R01_SP18 = TransportPoint('PYZ', '磐岩镇', P02_R01_B1, 'mm_sp_02', (641, 778))
P02_R01_SP19 = TransportPoint('SHJ3', '售货机3', P02_R01_B1, 'mm_sp_03', (516, 864))

# 雅利洛 - 城郊雪原
P02_R02_SP01 = TransportPoint('CP', '长坡', P02_R02, 'mm_tp_03', (1035, 319), (1023, 321))
P02_R02_SP02 = TransportPoint('ZLD', '着陆点', P02_R02, 'mm_tp_03', (1283, 367), (1271, 384))
P02_R02_SP03 = TransportPoint('XLZL', '巡猎之蕾拟造花萼赤', P02_R02, 'mm_tp_07', (946, 244), (947, 253))
P02_R02_SP04 = TransportPoint('HYZL', '回忆之蕾拟造花萼金', P02_R02, 'mm_tp_08', (1098, 391), (1103, 399))
P02_R02_SP05 = TransportPoint('XZQ', '行政区', P02_R02, 'mm_sp_02', (444, 109))
P02_R02_SP06 = TransportPoint('LK', '玲可', P02_R02, 'mm_sp_03', (1032, 342))

# 雅利洛 - 边缘通路
P02_R03_SP01 = TransportPoint('HCGC', '候车广场', P02_R03, 'mm_tp_03', (598, 832), (580, 833))
P02_R03_SP02 = TransportPoint('XXGC', '休闲广场', P02_R03, 'mm_tp_03', (690, 480), (701, 491))
P02_R03_SP03 = TransportPoint('GDJZ', '歌德旧宅', P02_R03, 'mm_tp_03', (811, 259), (800, 267))
P02_R03_SP04 = TransportPoint('HGZX', '幻光之形凝滞虚影', P02_R03, 'mm_tp_06', (450, 840), (474, 842))
P02_R03_SP05 = TransportPoint('FRZL', '丰饶之蕾拟造花萼赤', P02_R03, 'mm_tp_07', (659, 509), (669, 510))
P02_R03_SP06 = TransportPoint('YTZL', '以太之蕾拟造花萼金', P02_R03, 'mm_tp_08', (596, 194), (606, 195))

# 雅利洛 - 铁卫禁区
P02_R04_SP01 = TransportPoint('JQGS', '禁区岗哨', P02_R04, 'mm_tp_03', (1162, 576), (1158, 586))
P02_R04_SP02 = TransportPoint('JQQX', '禁区前线', P02_R04, 'mm_tp_03', (538, 596), (530, 587))
P02_R04_SP03 = TransportPoint('NYSN', '能源枢纽', P02_R04, 'mm_tp_03', (750, 1102), (767, 1064))
P02_R04_SP04 = TransportPoint('YHZX', '炎华之形凝滞虚影', P02_R04, 'mm_tp_06', (463, 442), (464, 465))
P02_R04_SP05 = TransportPoint('XQZJ', '迅拳之径侵蚀隧洞', P02_R04, 'mm_tp_09', (1143, 624), (1145, 617))
P02_R04_SP06 = TransportPoint('YYHY', '以眼还眼', P02_R04, 'mm_sp_01', (438, 578))
P02_R04_SP07 = TransportPoint('DBJXQ', '冬兵进行曲', P02_R04, 'mm_sp_01', (723, 1073))
P02_R04_SP08 = TransportPoint('CXHL', '残响回廊', P02_R04, 'mm_sp_02', (314, 589))

# 雅利洛 - 残响回廊
P02_R05_SP01 = TransportPoint('ZCLY', '筑城领域', P02_R05, 'mm_tp_03', (770, 442), (781, 426))
P02_R05_SP02 = TransportPoint('WRGC', '污染广场', P02_R05, 'mm_tp_03', (381, 655), (392, 642))
P02_R05_SP03 = TransportPoint('ZZZHS', '作战指挥室', P02_R05, 'mm_tp_03', (495, 856), (511, 849))
P02_R05_SP04 = TransportPoint('GZCQX', '古战场前线', P02_R05, 'mm_tp_03', (570, 1243), (580, 1232))
P02_R05_SP05 = TransportPoint('MLZX', '鸣雷之形凝滞虚影', P02_R05, 'mm_tp_06', (526, 640), (505, 639))
P02_R05_SP06 = TransportPoint('SJZX', '霜晶之形凝滞虚影', P02_R05, 'mm_tp_06', (681, 1231), (657, 1238))
P02_R05_SP07 = TransportPoint('PBZJ', '漂泊之径侵蚀隧洞', P02_R05, 'mm_tp_09', (654, 242), (660, 246))
P02_R05_SP08 = TransportPoint('TWJQ', '铁卫禁区', P02_R05, 'mm_sp02', (389, 626))
P02_R05_SP09 = TransportPoint('YDL', '永冬岭', P02_R05, 'mm_sp02', (733, 1280))  # 这里旁边站着一个传送到造物之柱的士兵

# 雅利洛 - 永冬岭
P02_R06_SP01 = TransportPoint('GZC', '古战场', P02_R06, 'mm_tp_03', (366, 776), (392, 768))
P02_R06_SP02 = TransportPoint('ZWPT', '造物平台', P02_R06, 'mm_tp_03', (784, 571), (791, 586))
P02_R06_SP03 = TransportPoint('RZZJ', '睿治之径侵蚀隧洞', P02_R06, 'mm_tp_09', (585, 663), (581, 661))
P02_R06_SP04 = TransportPoint('CXHL', '残响回廊', P02_R06, 'mm_sp_02', (338, 793))
P02_R06_SP05 = TransportPoint('HCDLM', '寒潮的落幕历战回响', P02_R06, 'mm_boss_02', (814, 701))

# 雅利洛 - 造物之柱
P02_R07_SP01 = TransportPoint('ZWZZRK', '造物之柱入口', P02_R07, 'mm_tp_03', (382, 426), (373, 426))
P02_R07_SP02 = TransportPoint('ZWZZSGC', '造物之柱施工场', P02_R07, 'mm_tp_03', (660, 616), (647, 597))
P02_R07_SP03 = TransportPoint('CXHL', '残响回廊', P02_R07, 'mm_sp_02', (313, 346))

# 雅利洛 - 旧武器试验场
P02_R08_SP01 = TransportPoint('JSQDZX', '决胜庆典中心', P02_R08_L2, 'mm_tp_03', (583, 836), (572, 837))
P02_R08_SP02 = TransportPoint('YTZXZD', '以太战线终端', P02_R08_L2, 'mm_tp_12', (525, 792), (539, 792))
P02_R08_SP03 = TransportPoint('MDZ', '铆钉镇', P02_R08_L2, 'mm_sp_02', (591, 1032))

# 雅利洛 - 磐岩镇
P02_R09_SP01 = TransportPoint('GDDFD', '歌德大饭店', P02_R09, 'mm_tp_03', (614, 236), (632, 236))
P02_R09_SP02 = TransportPoint('BJQLB', '搏击俱乐部', P02_R09, 'mm_tp_03', (419, 251), (409, 238))
P02_R09_SP03 = TransportPoint('NTSDZS', '娜塔莎的诊所', P02_R09, 'mm_tp_03', (416, 417), (418, 434))
P02_R09_SP04 = TransportPoint('PYZCJLS', '磐岩镇超级联赛', P02_R09, 'mm_tp_10', (358, 262))
P02_R09_SP05 = TransportPoint('MDZ', '铆钉镇', P02_R09, 'mm_sp_02', (630, 114))
P02_R09_SP06 = TransportPoint('DKQ', '大矿区', P02_R09, 'mm_sp_02', (453, 595))
P02_R09_SP07 = TransportPoint('DDSD', '地底商店', P02_R09, 'mm_sp_03', (632, 306))
P02_R09_SP08 = TransportPoint('CXT', '小吃摊', P02_R09, 'mm_sp_04', (706, 458))
P02_R09_SP09 = TransportPoint('GDDFD', '歌德大饭店', P02_R09, 'mm_sp_05', (688, 222))
P02_R09_SP10 = TransportPoint('NTSDZSRK', '娜塔莎的诊所入口', P02_R09, 'mm_sp_05', (393, 475))

# 雅利洛 - 大矿区
P02_R10_SP01 = TransportPoint('RK', '入口', P02_R10, 'mm_tp_03', (333, 166))
P02_R10_SP02 = TransportPoint('LLZBNS', '流浪者避难所', P02_R10, 'mm_tp_03', (778, 349))
P02_R10_SP03 = TransportPoint('FKD', '俯瞰点', P02_R10, 'mm_tp_03', (565, 641))
P02_R10_SP04 = TransportPoint('ZKD', '主矿道', P02_R10, 'mm_tp_03', (530, 757))
P02_R10_SP05 = TransportPoint('FMZX', '锋芒之形凝滞虚影', P02_R10, 'mm_tp_06', (561, 536))
P02_R10_SP06 = TransportPoint('FZZX', '燔灼之形凝滞虚影', P02_R10, 'mm_tp_06', (836, 630))
P02_R10_SP07 = TransportPoint('XWZL', '虚无之蕾拟造花萼赤', P02_R10, 'mm_tp_07', (295, 243))
P02_R10_SP08 = TransportPoint('CZZL', '藏珍之蕾拟造花萼金', P02_R10, 'mm_tp_08', (554, 686))
P02_R10_SP09 = TransportPoint('PYZ', '磐岩镇', P02_R10, 'mm_sp_02', (351, 144))

# 雅利洛 - 铆钉镇
P02_R11_SP01 = TransportPoint('GEY', '孤儿院', P02_R11_L1, 'mm_tp_03', (600, 211))
P02_R11_SP02 = TransportPoint('FQSJ', '废弃市集', P02_R11_L1, 'mm_tp_03', (465, 374))
P02_R11_SP03 = TransportPoint('RK', '入口', P02_R11_L1, 'mm_tp_03', (613, 675))
P02_R11_SP04 = TransportPoint('XFZX', '巽风之形凝滞虚影', P02_R11_L1, 'mm_tp_06', (580, 374))
P02_R11_SP05 = TransportPoint('ZSZL', '智识之蕾拟造花萼赤', P02_R11_L1, 'mm_tp_07', (609, 608))
P02_R11_SP06 = TransportPoint('JWQSYC', '旧武器试验场', P02_R11_L1, 'mm_sp_02', (767, 244))  # 与 机械聚落 重合
P02_R11_SP07 = TransportPoint('PYZ', '磐岩镇', P02_R11_L1, 'mm_sp_02', (597, 698))

# 雅利洛 - 机械聚落
P02_R12_SP01 = TransportPoint('LLZYD', '流浪者营地', P02_R12_L2, 'mm_tp_03', (556, 174))
P02_R12_SP02 = TransportPoint('SQLZD', '史瓦罗驻地', P02_R12_L2, 'mm_tp_03', (554, 506))
P02_R12_SP03 = TransportPoint('NYZHSS', '能源转换设施', P02_R12_L1, 'mm_tp_03', (413, 527))
P02_R12_SP04 = TransportPoint('TXZL', '同谐之蕾拟造花萼赤', P02_R12_L1, 'mm_tp_07', (298, 564))

# 仙舟罗浮 - 星槎海中枢
P03_R01_SP01 = TransportPoint('XCMT', '星槎码头', P03_R01, 'mm_tp_03', (443, 341))
P03_R01_SP02 = TransportPoint('KYT', '坤舆台', P03_R01, 'mm_tp_03', (700, 370))
P03_R01_SP03 = TransportPoint('XYDD', '宣夜大道', P03_R01, 'mm_tp_03', (428, 622))
P03_R01_SP04 = TransportPoint('TKZY', '天空之眼', P03_R01, 'mm_sp_01', (616, 409))
P03_R01_SP05 = TransportPoint('LYD', '流云渡', P03_R01, 'mm_sp_02', (849, 168))
P03_R01_SP06 = TransportPoint('CLT', '长乐天', P03_R01, 'mm_sp_02', (539, 231))
P03_R01_SP07 = TransportPoint('HXG', '廻星港', P03_R01, 'mm_sp_02', (337, 748))
P03_R01_SP08 = TransportPoint('SHJ1', '售货机1', P03_R01, 'mm_sp_03', (603, 306))
P03_R01_SP09 = TransportPoint('ZHPLB', '杂货铺老板', P03_R01, 'mm_sp_03', (572, 482))
P03_R01_SP10 = TransportPoint('BYH', '不夜侯', P03_R01, 'mm_sp_03', (348, 508))
P03_R01_SP11 = TransportPoint('SHJ2', '售货机2', P03_R01, 'mm_sp_03', (360, 538))
P03_R01_SP12 = TransportPoint('SHJ3', '售货机3', P03_R01, 'mm_sp_03', (389, 538))
P03_R01_SP13 = TransportPoint('SZG', '赎珠阁', P03_R01, 'mm_sp_04', (375, 595))
P03_R01_SP14 = TransportPoint('SHJ4', '售货机4', P03_R01, 'mm_sp_03', (316, 698))
P03_R01_SP15 = TransportPoint('XCT', '小吃摊', P03_R01, 'mm_sp_03', (436, 702))
P03_R01_SP16 = TransportPoint('SCG', '司辰宫', P03_R01, 'mm_sp_05', (673, 487))

# 仙舟罗浮 - 流云渡
P03_R02_SP01 = TransportPoint('LYDHD', '流云渡货道', P03_R02_L2, 'mm_tp_03', (704, 422))
P03_R02_SP02 = TransportPoint('JYF', '积玉坊', P03_R02_L1, 'mm_tp_03', (541, 795))
P03_R02_SP03 = TransportPoint('JYFNC', '积玉坊南侧', P03_R02_L1, 'mm_tp_03', (567, 986))
P03_R02_SP04 = TransportPoint('LYDCCC', '流云渡乘槎处', P03_R02_L1, 'mm_tp_03', (579, 1369))
P03_R02_SP05 = TransportPoint('BLZX', '冰棱之形凝滞虚影', P03_R02_L1, 'mm_tp_06', (730, 1367))
P03_R02_SP06 = TransportPoint('SSZJ', '圣颂之径侵蚀隧洞', P03_R02_L1, 'mm_tp_09', (542, 1153))
P03_R02_SP07 = TransportPoint('XCHZS', '星槎海中枢', P03_R02_L1, 'mm_sp_02', (578, 1503))
P03_R02_SP08 = TransportPoint('GQYBSGC', '过期邮包收购处', P03_R02_L1, 'mm_sp_03', (388, 777))

# 仙舟罗浮 - 廻星港
P03_R03_SP01 = TransportPoint('FXXZ', '飞星小筑', P03_R03_L2, 'mm_tp_03', (834, 249))
P03_R03_SP02 = TransportPoint('ZCQMJ', '植船区萌甲', P03_R03_L1, 'mm_tp_03', (441, 465))
P03_R03_SP03 = TransportPoint('ZCQFS', '植船区繁生', P03_R03_L1, 'mm_tp_03', (523, 609))
P03_R03_SP04 = TransportPoint('BHQ', '泊航区', P03_R03_L1, 'mm_tp_03', (647, 707))
P03_R03_SP05 = TransportPoint('ZEZX', '震厄之形凝滞虚影', P03_R03_L1, 'mm_tp_06', (729, 803))
P03_R03_SP06 = TransportPoint('YYZJ', '野焰之径侵蚀隧洞', P03_R03_L1, 'mm_tp_09', (455, 374))
P03_R03_SP07 = TransportPoint('XCHZS', '星槎海中枢', P03_R03_L2, 'mm_sp_02', (881, 222))

# 仙舟罗浮 - 长乐天
P03_R04_SP01 = TransportPoint('RMT', '若木亭', P03_R04, 'mm_tp_03', (550, 206))
P03_R04_SP02 = TransportPoint('YXT', '悠暇庭', P03_R04, 'mm_tp_03', (589, 530))
P03_R04_SP03 = TransportPoint('TBS', '太卜司', P03_R04, 'mm_sp_02', (697, 104))
P03_R04_SP04 = TransportPoint('SCF', '神策府', P03_R04, 'mm_sp_02', (427, 145))
P03_R04_SP05 = TransportPoint('JRX1', '金人巷1', P03_R04, 'mm_sp_02', (355, 224))
P03_R04_SP06 = TransportPoint('JRX2', '金人巷2', P03_R04, 'mm_sp_02', (380, 465))
P03_R04_SP07 = TransportPoint('XCHZS', '星槎海中枢', P03_R04, 'mm_sp_02', (494, 588))
P03_R04_SP08 = TransportPoint('ZHXT', '杂货小摊', P03_R04, 'mm_sp_03', (695, 193))
P03_R04_SP09 = TransportPoint('SHJ1', '售货机-1', P03_R04, 'mm_sp_03', (550, 226))  # 这个没有扫描到 坐标可能不准
P03_R04_SP10 = TransportPoint('BET', '宝饵堂', P03_R04, 'mm_sp_03', (745, 232))
P03_R04_SP11 = TransportPoint('SHJ2', '售货机2', P03_R04, 'mm_sp_03', (663, 262))
P03_R04_SP12 = TransportPoint('SYSS', '三余书肆', P03_R04, 'mm_sp_03', (662, 423))
P03_R04_SP13 = TransportPoint('SHJ3', '售货机3', P03_R04, 'mm_sp_03', (444, 505))
P03_R04_SP14 = TransportPoint('XCT', '小吃摊', P03_R04, 'mm_sp_03', (636, 560))
P03_R04_SP15 = TransportPoint('DHSGX', '地衡司公廨', P03_R04, 'mm_sp_05', (538, 294))

# 仙舟罗浮 - 金人巷
P03_R05_SP01 = TransportPoint('QKJ', '乾坤街', P03_R05, 'mm_tp_03', (694, 383))
P03_R05_SP02 = TransportPoint('JRXYS', '金人巷夜市', P03_R05, 'mm_tp_03', (432, 521))
P03_R05_SP03 = TransportPoint('JRXMT', '金人巷码头', P03_R05, 'mm_tp_11', (480, 53))
P03_R05_SP04 = TransportPoint('CLT1', '长乐天1', P03_R05, 'mm_sp_02', (346, 495))
P03_R05_SP05 = TransportPoint('CLT2', '长乐天2', P03_R05, 'mm_sp_02', (447, 536))  # 这个没有扫描到 坐标可能不准
P03_R05_SP06 = TransportPoint('SKT', '寿考堂', P03_R05, 'mm_sp_03', (365, 275))
P03_R05_SP07 = TransportPoint('SZW', '尚滋味', P03_R05, 'mm_sp_03', (423, 347))
P03_R05_SP08 = TransportPoint('GAYDXCT', '高阿姨的小吃摊', P03_R05, 'mm_sp_03', (500, 352))
P03_R05_SP09 = TransportPoint('CJP', '陈机铺', P03_R05, 'mm_sp_03', (653, 369))
P03_R05_SP10 = TransportPoint('DSCZ', '杜氏茶庄', P03_R05, 'mm_sp_03', (582, 392))
P03_R05_SP11 = TransportPoint('MZG', '美馔阁', P03_R05, 'mm_sp_03', (429, 393))  # mei zhuan ge
P03_R05_SP12 = TransportPoint('SHJ', '售货机', P03_R05, 'mm_sp_03', (491, 395))
P03_R05_SP13 = TransportPoint('HSGDDYNC', '霍三哥的大衣内侧', P03_R05, 'mm_sp_07', (775, 266))

# 仙舟罗浮 - 太卜司
P03_R06_SP01 = TransportPoint('JHZ', '界寰阵', P03_R06_L1, 'mm_tp_03', (339, 287))
P03_R06_SP02 = TransportPoint('TYQGZ', '太衍穷观阵', P03_R06_L2, 'mm_tp_03', (553, 601))
P03_R06_SP03 = TransportPoint('SST', '授事厅', P03_R06_L2, 'mm_tp_03', (922, 830))
P03_R06_SP04 = TransportPoint('XT', '祥台', P03_R06_L2, 'mm_tp_03', (416, 1177))
P03_R06_SP05 = TransportPoint('GZS', '工造司', P03_R06_L2, 'mm_sp_02', (1141, 789))
P03_R06_SP06 = TransportPoint('CLT', '长乐天', P03_R06_L2, 'mm_sp_02', (449, 1147))

# 仙舟罗浮 - 工造司
P03_R07_SP01 = TransportPoint('GWYTD', '格物院通道', P03_R07, 'mm_tp_03', (461, 485))
P03_R07_SP02 = TransportPoint('RJFTD', '镕金坊通道', P03_R07, 'mm_tp_03', (821, 602))
P03_R07_SP03 = TransportPoint('XJP', '玄机坪', P03_R07, 'mm_tp_03', (189, 865))
P03_R07_SP04 = TransportPoint('ZHHL', '造化洪炉', P03_R07, 'mm_tp_03', (758, 964))
P03_R07_SP05 = TransportPoint('YOZX', '偃偶之形凝滞虚影', P03_R07, 'mm_tp_06', (388, 655))
P03_R07_SP06 = TransportPoint('DDS', '丹鼎司', P03_R07, 'mm_sp_02', (1029, 767))
P03_R07_SP07 = TransportPoint('TBS', '太卜司', P03_R07, 'mm_sp_02', (170, 928))

# 仙舟罗浮 - 丹鼎司
P03_R08_SP01 = TransportPoint('TZDS', '太真丹室', P03_R08_L1, 'mm_tp_03', (547, 555))
P03_R08_SP02 = TransportPoint('GYT', '观颐台', P03_R08_L1, 'mm_tp_03', (438, 694))
P03_R08_SP03 = TransportPoint('XYSJ', '行医市集', P03_R08_L2, 'mm_tp_03', (826, 898))
P03_R08_SP04 = TransportPoint('QHS', '岐黄署', P03_R08_L2, 'mm_tp_03', (819, 1533))
P03_R08_SP05 = TransportPoint('TRZX', '天人之形凝滞虚影', P03_R08_L2, 'mm_tp_06', (1225, 1087))
P03_R08_SP06 = TransportPoint('YSZJ', '药使之径侵蚀隧洞', P03_R08_L2, 'mm_tp_09', (667, 1504))
P03_R08_SP07 = TransportPoint('LYJ', '麟渊境', P03_R08_L1, 'mm_sp_02', (453, 218))
P03_R08_SP08 = TransportPoint('QLT', '祈龙坛', P03_R08_L1, 'mm_sp_02', (186, 710))
P03_R08_SP09 = TransportPoint('SLDY', '蜃楼遁影', P03_R08_L2, 'mm_sp_01', (846, 815))
P03_R08_SP10 = TransportPoint('GZS', '工造司', P03_R08_L2, 'mm_sp_02', (867, 1564))
P03_R08_SP11 = TransportPoint('YRDXYT', '永仁的小药摊', P03_R08_L2, 'mm_sp_03', (990, 758))
P03_R08_SP12 = TransportPoint('GGDYCT', '汵汵的药材摊', P03_R08_L2, 'mm_sp_03', (837, 843))

# 仙舟罗浮 - 鳞渊境
P03_R09_SP01 = TransportPoint('GXSC', '宫墟深处', P03_R09, 'mm_tp_03', (891, 425))
P03_R09_SP02 = TransportPoint('GHGX', '古海宫墟', P03_R09, 'mm_tp_03', (1113, 425))
P03_R09_SP03 = TransportPoint('XLDYD', '显龙大雩殿', P03_R09, 'mm_tp_03', (1599, 444))
P03_R09_SP04 = TransportPoint('NSZX', '孽兽之形凝滞虚影', P03_R09, 'mm_tp_06', (917, 169))
P03_R09_SP05 = TransportPoint('DDS', '丹鼎司', P03_R09, 'mm_sp_02', (1891, 391))
P03_R09_SP06 = TransportPoint('BSDSS', '不死的神实历战回响', P03_R09, 'mm_boss_03', (470, 450))

# 仙舟罗浮 - 绥园
P03_R10_SP01 = TransportPoint('YXGCL', '偃息馆长廊', P03_R10, 'mm_tp_03', (867, 402), (868, 417))
P03_R10_SP02 = TransportPoint('THLHM', '谈狐林后门', P03_R10, 'mm_tp_03', (209, 480), (235, 480))
P03_R10_SP03 = TransportPoint('QQTRK', '青丘台入口', P03_R10, 'mm_tp_03', (606, 646), (617, 647))
P03_R10_SP04 = TransportPoint('YYTRK', '燕乐亭入口', P03_R10, 'mm_tp_03', (838, 796), (855, 777))
P03_R10_SP05 = TransportPoint('YFZX', '幽府之形凝滞虚影', P03_R10, 'mm_tp_06', (152, 678), (155, 658))
P03_R10_SP06 = TransportPoint('YMZJ', '幽冥之径侵蚀隧洞', P03_R10, 'mm_tp_09', (418, 462), (423, 459))
P03_R10_SP07 = TransportPoint('JHD', '集合点', P03_R10, 'mm_tp_13', (907, 447), (907, 447))
P03_R10_SP08 = TransportPoint('CLT', '长乐天', P03_R10, 'mm_sp_02', (628, 771))
P03_R10_SP09 = TransportPoint('THLCZYT', '谈狐林处镇妖塔', P03_R10, 'mm_sp_08', (235, 410))
P03_R10_SP10 = TransportPoint('YXGCZYT', '偃息馆处镇妖塔', P03_R10, 'mm_sp_08', (839, 463))
P03_R10_SP11 = TransportPoint('QQTCZYT', '青丘台处镇妖塔', P03_R10, 'mm_sp_08', (621, 510))
P03_R10_SP12 = TransportPoint('YYTCZYT', '燕乐亭处镇妖塔', P03_R10, 'mm_sp_08', (833, 711))
P03_R10_SP13 = TransportPoint('DMZCZYT', '狐眠冢处镇妖塔', P03_R10, 'mm_sp_08', (487, 789))
P03_R10_SP14 = TransportPoint('QQTQM', '青丘台栖木', P03_R10, 'mm_sp_09', (487, 515))
P03_R10_SP15 = TransportPoint('DMZQM', '狐眠冢栖木', P03_R10, 'mm_sp_09', (296, 664))
P03_R10_SP16 = TransportPoint('YYTQM', '燕乐亭栖木', P03_R10, 'mm_sp_09', (965, 726))

REGION_2_SP = {
    P01_R01.pr_id: [P01_R01_SP03],
    P01_R02.pr_id: [P01_R02_SP01, P01_R02_SP02, P01_R02_SP03, P01_R02_SP04],
    P01_R03_L1.pr_id: [P01_R03_SP01, P01_R03_SP02, P01_R03_SP03, P01_R03_SP04, P01_R03_SP05, P01_R03_SP06, P01_R03_SP07],
    P01_R04_L1.pr_id: [P01_R04_SP01, P01_R04_SP02, P01_R04_SP03, P01_R04_SP04, P01_R04_SP05, P01_R04_SP06],
    P01_R05_L1.pr_id: [P01_R05_SP01, P01_R05_SP02, P01_R05_SP03, P01_R05_SP04, P01_R05_SP05],
    P02_R01_L1.pr_id: [
        P02_R01_SP01, P02_R01_SP02, P02_R01_SP03, P02_R01_SP04, P02_R01_SP05, P02_R01_SP06, P02_R01_SP07, P02_R01_SP08, P02_R01_SP09, P02_R01_SP10,
        P02_R01_SP11, P02_R01_SP12, P02_R01_SP13, P02_R01_SP14, P02_R01_SP15, P02_R01_SP16, P02_R01_SP17, P02_R01_SP18, P02_R01_SP19],
    P02_R02.pr_id: [P02_R02_SP01, P02_R02_SP02, P02_R02_SP03, P02_R02_SP04, P02_R02_SP05, P02_R02_SP06],
    P02_R03.pr_id: [P02_R03_SP01, P02_R03_SP02, P02_R03_SP03, P02_R03_SP04, P02_R03_SP05, P02_R03_SP06],
    P02_R04.pr_id: [P02_R04_SP01, P02_R04_SP02, P02_R04_SP03, P02_R04_SP04, P02_R04_SP05, P02_R04_SP06, P02_R04_SP07, P02_R04_SP08],
    P02_R05.pr_id: [P02_R05_SP01, P02_R05_SP02, P02_R05_SP03, P02_R05_SP04, P02_R05_SP05, P02_R05_SP06, P02_R05_SP07, P02_R05_SP08, P02_R05_SP09],
    P02_R06.pr_id: [P02_R06_SP01, P02_R06_SP02, P02_R06_SP03, P02_R06_SP04, P02_R06_SP05],
    P02_R07.pr_id: [P02_R07_SP01, P02_R07_SP02, P02_R07_SP03],
    P02_R08_L2.pr_id: [P02_R08_SP01, P02_R08_SP02, P02_R08_SP03],
    P02_R09.pr_id: [P02_R09_SP01, P02_R09_SP02, P02_R09_SP03, P02_R09_SP04, P02_R09_SP05, P02_R09_SP06, P02_R09_SP07, P02_R09_SP08, P02_R09_SP09, P02_R09_SP10],
    P02_R10.pr_id: [P02_R10_SP01, P02_R10_SP02, P02_R10_SP03, P02_R10_SP04, P02_R10_SP05, P02_R10_SP06, P02_R10_SP07, P02_R10_SP08, P02_R10_SP09],
    P02_R11_L1.pr_id: [P02_R11_SP01, P02_R11_SP02, P02_R11_SP03, P02_R11_SP04, P02_R11_SP05, P02_R11_SP06, P02_R11_SP07],
    P02_R12_L1.pr_id: [P02_R12_SP01, P02_R12_SP02, P02_R12_SP03, P02_R12_SP04],
    P03_R01.pr_id: [P03_R01_SP01, P03_R01_SP02, P03_R01_SP03, P03_R01_SP04, P03_R01_SP05, P03_R01_SP06, P03_R01_SP07, P03_R01_SP08, P03_R01_SP09, P03_R01_SP10,
                    P03_R01_SP11, P03_R01_SP12, P03_R01_SP13, P03_R01_SP14, P03_R01_SP15, P03_R01_SP16],
    P03_R02_L1.pr_id: [P03_R02_SP01, P03_R02_SP02, P03_R02_SP03, P03_R02_SP04, P03_R02_SP05, P03_R02_SP06, P03_R02_SP07, P03_R02_SP08],
    P03_R03_L1.pr_id: [P03_R03_SP01, P03_R03_SP02, P03_R03_SP03, P03_R03_SP04, P03_R03_SP05, P03_R03_SP06, P03_R03_SP07],
    P03_R04.pr_id: [P03_R04_SP01, P03_R04_SP02, P03_R04_SP03, P03_R04_SP04, P03_R04_SP05, P03_R04_SP06, P03_R04_SP07, P03_R04_SP08, P03_R04_SP09, P03_R04_SP10,
                    P03_R04_SP10, P03_R04_SP11, P03_R04_SP12, P03_R04_SP13, P03_R04_SP14, P03_R04_SP15],
    P03_R05.pr_id: [P03_R05_SP01, P03_R05_SP02, P03_R05_SP03, P03_R05_SP04, P03_R05_SP05, P03_R05_SP06, P03_R05_SP07, P03_R05_SP08, P03_R05_SP09, P03_R05_SP10,
                    P03_R05_SP11, P03_R05_SP12, P03_R05_SP13],
    P03_R06_L1.pr_id: [P03_R06_SP01, P03_R06_SP02, P03_R06_SP03, P03_R06_SP04, P03_R06_SP05, P03_R06_SP06],
    P03_R07.pr_id: [P03_R07_SP01, P03_R07_SP02, P03_R07_SP03, P03_R07_SP04, P03_R07_SP05, P03_R07_SP06, P03_R07_SP07],
    P03_R08_L1.pr_id: [P03_R08_SP01, P03_R08_SP02, P03_R08_SP03, P03_R08_SP04, P03_R08_SP05, P03_R08_SP06, P03_R08_SP07, P03_R08_SP08, P03_R08_SP09, P03_R08_SP10,
                       P03_R08_SP11, P03_R08_SP12],
    P03_R09.pr_id: [P03_R09_SP01, P03_R09_SP02, P03_R09_SP03, P03_R09_SP04, P03_R09_SP05, P03_R09_SP06],
    P03_R10.pr_id: [P03_R10_SP01, P03_R10_SP02, P03_R10_SP03, P03_R10_SP04, P03_R10_SP05, P03_R10_SP06, P03_R10_SP07, P03_R10_SP08, P03_R10_SP09, P03_R10_SP10,
                    P03_R10_SP11, P03_R10_SP12, P03_R10_SP13, P03_R10_SP14, P03_R10_SP15, P03_R10_SP16]
}


def get_sp_by_cn(planet_cn: str, region_cn: str, floor: int, tp_cn: str) -> TransportPoint:
    p: Planet = get_planet_by_cn(planet_cn)
    r: Region = get_region_by_cn(region_cn, p, floor)
    for i in REGION_2_SP.get(r.pr_id):
        if i.cn != tp_cn:
            continue
        return i


def region_with_another_floor(region: Region, floor: int) -> Region:
    """
    切换层数
    :param region:
    :param floor:
    :return:
    """
    return get_region_by_cn(region.cn, region.planet, floor)


def get_sp_type_in_rect(region: Region, rect: Rect) -> dict:
    """
    获取区域特定矩形内的特殊点 按种类分组
    :param region: 区域
    :param rect: 矩形 为空时返回全部
    :return: 特殊点
    """
    sp_list = REGION_2_SP.get(region.pr_id)
    sp_map = {}
    for sp in sp_list:
        if rect is None or cal_utils.in_rect(sp.lm_pos, rect):
            if sp.template_id not in sp_map:
                sp_map[sp.template_id] = []
            sp_map[sp.template_id].append(sp)

    return sp_map
