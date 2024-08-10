import difflib
from typing import Optional, List, Dict

from basic import cal_utils, Rect, Point, str_utils
from basic.i18_utils import gt


class Planet:

    def __init__(self, num: int, i: str, cn: str):
        self.num: int = num  # 编号 用于强迫症给文件排序
        self.id: str = i  # 用在找文件夹之类的
        self.cn: str = cn  # 中文

    def __repr__(self):
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
P02 = Planet(2, "YLL6", "雅利洛-VI")
P03 = Planet(3, "XZLF", "仙舟「罗浮」")
P04 = Planet(4, "PNKN", "匹诺康尼")

PLANET_LIST = [P01, P02, P03, P04]


def get_planet_by_cn(cn: str) -> Optional[Planet]:
    """
    根据星球的中文 获取对应常量
    :param cn: 星球中文
    :return: 常量
    """
    for i in PLANET_LIST:
        if i.cn == cn:
            return i
    return None


def best_match_planet_by_name(ocr_word: str) -> Optional[Planet]:
    """
    根据OCR结果匹配一个星球
    :param ocr_word: OCR结果
    :return:
    """
    planet_names = [gt(p.cn, 'ocr') for p in PLANET_LIST]
    idx = str_utils.find_best_match_by_lcs(ocr_word, target_word_list=planet_names)
    if idx is None:
        return None
    else:
        return PLANET_LIST[idx]


class Region:

    def __init__(self, num: int, i: str, cn: str, planet: Planet, floor: int = 0,
                 parent: Optional = None,
                 enter_template_id: Optional[str] = None,
                 enter_lm_pos: Optional[Point] = None,
                 large_map_scale: Optional[int] = None):
        self.num: int = num  # 编号 方便列表排序
        self.id: str = i  # id 用在找文件夹之类的
        self.cn: str = cn  # 中文 用在OCR
        self.planet: Planet = planet
        self.floor: int = floor
        self.parent: Region = parent  # 子区域才会有 属于哪个具体区域
        self.enter_template_id: str = enter_template_id  # 子区域才会有 入口对应的模板ID
        self.enter_lm_pos: Point = enter_lm_pos  # 子区域才会有 在具体区域的哪个位置进入
        self.large_map_scale: int = 0 if large_map_scale is None else large_map_scale

    def __repr__(self):
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
        if self.another_floor:
            return '%s %s' % (gt(self.cn, 'ui'), gt('%d层' % self.floor, 'ocr'))
        else:
            return gt(self.cn, 'ui')


# 空间站黑塔
P01_R00 = Region(0, "GJCX", "观景车厢", None)
P01_R01 = Region(1, "ZKCD", "主控舱段", P01)
P01_R02 = Region(2, "JZCD", "基座舱段", P01)
P01_R03_B1 = Region(3, "SRCD", "收容舱段", P01, -1)
P01_R03_F1 = Region(3, "SRCD", "收容舱段", P01, 1)
P01_R03_F2 = Region(3, "SRCD", "收容舱段", P01, 2)
P01_R04_F1 = Region(4, "ZYCD", "支援舱段", P01, 1)
P01_R04_F2 = Region(4, "ZYCD", "支援舱段", P01, 2)
P01_R05_F1 = Region(5, "JBCD", "禁闭舱段", P01, 1)
P01_R05_F2 = Region(5, "JBCD", "禁闭舱段", P01, 2)
P01_R05_L3 = Region(5, "JBCD", "禁闭舱段", P01, 3)

# 雅利洛
P02_R01_F1 = Region(1, "XZQ", "行政区", P02, floor=1)
P02_R01_B1 = Region(1, "XZQ", "行政区", P02, floor=-1)
P02_R02 = Region(2, "CJXY", "城郊雪原", P02)
P02_R03 = Region(3, "BYTL", "边缘通路", P02)
P02_R04 = Region(4, "TWJQ", "铁卫禁区", P02)
P02_R05 = Region(5, "CXHL", "残响回廊", P02)
P02_R06 = Region(6, "YDL", "永冬岭", P02)
P02_R07 = Region(7, "ZWZZ", "造物之柱", P02)
P02_R08_F2 = Region(8, "JWQSYC", "旧武器试验场", P02, floor=2)
P02_R09 = Region(9, "PYZ", "磐岩镇", P02)
P02_R10 = Region(10, "DKQ", "大矿区", P02)
P02_R11_F1 = Region(11, "MDZ", "铆钉镇", P02, floor=1)
P02_R11_F2 = Region(11, "MDZ", "铆钉镇", P02, floor=2)
P02_R12_F1 = Region(12, "JXJL", "机械聚落", P02, floor=1)
P02_R12_F2 = Region(12, "JXJL", "机械聚落", P02, floor=2)

# 仙舟罗浮
P03_R01 = Region(1, "XCHZS", "星槎海中枢", P03)
P03_R02_F1 = Region(2, "LYD", "流云渡", P03, floor=1)
P03_R02_F2 = Region(2, "LYD", "流云渡", P03, floor=2)
P03_R03_F1 = Region(3, "HXG", "廻星港", P03, floor=1)
P03_R03_F2 = Region(3, "HXG", "廻星港", P03, floor=2)
P03_R04 = Region(4, "CLT", "长乐天", P03)
P03_R05 = Region(5, "JRX", "金人巷", P03)
P03_R06_F1 = Region(6, "TBS", "太卜司", P03, floor=1)
P03_R06_F2 = Region(6, "TBS", "太卜司", P03, floor=2)
P03_R07 = Region(7, "GZS", "工造司", P03)
P03_R08_F1 = Region(8, "DDS", "丹鼎司", P03, floor=1)
P03_R08_F2 = Region(8, "DDS", "丹鼎司", P03, floor=2)
P03_R09 = Region(9, "LYJ", "鳞渊境", P03)
P03_R10 = Region(10, "SY", "绥园", P03)
P03_R11_F1 = Region(11, "YQY", "幽囚狱", P03, floor=1)
P03_R11_B1 = Region(11, "YQY", "幽囚狱", P03, floor=-1)
P03_R11_B2 = Region(11, "YQY", "幽囚狱", P03, floor=-2)
P03_R11_B3 = Region(11, "YQY", "幽囚狱", P03, floor=-3)
P03_R11_B4 = Region(11, "YQY", "幽囚狱", P03, floor=-4)

# 匹诺康尼
P04_R01_F1 = Region(1, "BRMJDXS", "「白日梦」酒店-现实", P04, floor=1)
P04_R01_F2 = Region(1, "BRMJDXS", "「白日梦」酒店-现实", P04, floor=2)
P04_R01_F3 = Region(1, "BRMJDXS", "「白日梦」酒店-现实", P04, floor=3)
P04_R02_F1 = Region(2, "HJDSK", "黄金的时刻", P04, floor=1)
P04_R02_F2 = Region(2, "HJDSK", "黄金的时刻", P04, floor=2)
P04_R02_F3 = Region(2, "HJDSK", "黄金的时刻", P04, floor=3)
P04_R03 = Region(3, "ZMBJ", "筑梦边境", P04)
P04_R04 = Region(4, "ZZDM", "稚子的梦", P04)
P04_R05_F1 = Region(5, "BRMJDMJ", "「白日梦」酒店-梦境", P04, floor=1)
P04_R05_F2 = Region(5, "BRMJDMJ", "「白日梦」酒店-梦境", P04, floor=2)
P04_R05_F3 = Region(5, "BRMJDMJ", "「白日梦」酒店-梦境", P04, floor=3)
P04_R06_F1 = Region(6, "ZLGG", "朝露公馆", P04, floor=1)
P04_R06_F2 = Region(6, "ZLGG", "朝露公馆", P04, floor=2)
P04_R06_SUB_01 = Region(6, "CSSH", "城市沙盒", P04,
                        parent=P04_R06_F1, enter_template_id='mm_sub_01', enter_lm_pos=Point(572, 455))
P04_R07_F1 = Region(7, "KLKYSLY", "克劳克影视乐园", P04, floor=1)
P04_R07_F2 = Region(7, "KLKYSLY", "克劳克影视乐园", P04, floor=2)
P04_R08_F1 = Region(8, "LMJ", "流梦礁", P04, floor=1)
P04_R08_F2 = Region(8, "LMJ", "流梦礁", P04, floor=2)
P04_R09 = Region(9, "SLDRSHXHC", "苏乐达TM热砂海选会场", P04)
P04_R09_SUB_01 = Region(9, "YHLT", "一号擂台", P04,
                        parent=P04_R09, enter_template_id='mm_sub_02', enter_lm_pos=Point(337, 1025),
                        large_map_scale=0)
P04_R09_SUB_02 = Region(9, "EHLT", "二号擂台", P04,
                        parent=P04_R09, enter_template_id='mm_sub_02', enter_lm_pos=Point(447, 1025),
                        large_map_scale=0)
P04_R09_SUB_03_B2 = Region(9, "QHDSL", "枪火的试炼", P04, floor=-2,
                           parent=P04_R09, enter_template_id='mm_sub_02', enter_lm_pos=Point(746, 1192),
                           large_map_scale=0)
P04_R09_SUB_03_B1 = Region(9, "QHDSL", "枪火的试炼", P04, floor=-1,
                           parent=P04_R09, enter_template_id='mm_sub_02', enter_lm_pos=Point(746, 1192),
                           large_map_scale=0)
P04_R09_SUB_03_F1 = Region(9, "QHDSL", "枪火的试炼", P04, floor=1,
                           parent=P04_R09, enter_template_id='mm_sub_02', enter_lm_pos=Point(746, 1192),
                           large_map_scale=0)
P04_R09_SUB_03_F2 = Region(9, "QHDSL", "枪火的试炼", P04, floor=2,
                           parent=P04_R09, enter_template_id='mm_sub_02', enter_lm_pos=Point(746, 1192),
                           large_map_scale=0)
P04_R09_SUB_04 = Region(9, "SJDSL", "时间的试炼入口", P04,
                        parent=P04_R09, enter_template_id='mm_sub_02', enter_lm_pos=Point(857, 1192),
                        large_map_scale=0)
P04_R09_SUB_05 = Region(9, "YJPTZ", "演技派挑战", P04,
                        parent=P04_R09, enter_template_id='mm_sub_02', enter_lm_pos=Point(294, 1404),
                        large_map_scale=0)
P04_R09_SUB_06 = Region(9, "DZPTZ", "动作派挑战", P04,
                        parent=P04_R09, enter_template_id='mm_sub_02', enter_lm_pos=Point(403, 1404),
                        large_map_scale=0)
P04_R10 = Region(10, "PNKNDJY", "匹诺康尼大剧院", P04)
P04_R10_SUB_01_F2 = Region(10, "MJKJ1", "梦境空间1", P04, floor=2,
                           parent=P04_R10, enter_template_id='mm_sp_05', enter_lm_pos=Point(387, 755),
                           large_map_scale=0)
P04_R10_SUB_01_F3 = Region(10, "MJKJ1", "梦境空间1", P04, floor=3,
                           parent=P04_R10, enter_template_id='mm_sp_05', enter_lm_pos=Point(387, 755),
                           large_map_scale=0)


# 这里的顺序需要保持和界面上的区域顺序一致
PLANET_2_REGION: Dict[str, List[Region]] = {
    P01.np_id: [P01_R01, P01_R02, P01_R03_F1, P01_R03_F2, P01_R03_B1, P01_R04_F1, P01_R04_F2, P01_R05_F1, P01_R05_F2, P01_R05_L3],
    P02.np_id: [P02_R01_F1, P02_R01_B1, P02_R02, P02_R03, P02_R04, P02_R05, P02_R06, P02_R07, P02_R08_F2, P02_R09, P02_R10,
                P02_R11_F1, P02_R11_F2, P02_R12_F1, P02_R12_F2],
    P03.np_id: [P03_R01, P03_R02_F1, P03_R02_F2, P03_R03_F1, P03_R03_F2, P03_R04, P03_R05, P03_R06_F1, P03_R06_F2,
                P03_R07, P03_R08_F1, P03_R08_F2, P03_R09, P03_R10, P03_R11_F1, P03_R11_B1, P03_R11_B2, P03_R11_B3, P03_R11_B4],
    P04.np_id: [P04_R01_F1, P04_R01_F2, P04_R01_F3, P04_R02_F1, P04_R02_F2, P04_R02_F3, P04_R03, P04_R04, P04_R05_F1, P04_R05_F2, P04_R05_F3,
                P04_R06_F1, P04_R06_F2, P04_R06_SUB_01, P04_R07_F1, P04_R07_F2, P04_R08_F1, P04_R08_F2,
                P04_R09, P04_R09_SUB_01, P04_R09_SUB_02, P04_R09_SUB_03_B2, P04_R09_SUB_03_B1, P04_R09_SUB_03_F1, P04_R09_SUB_03_F2, P04_R09_SUB_04, P04_R09_SUB_05, P04_R09_SUB_06,
                P04_R10, P04_R10_SUB_01_F2, P04_R10_SUB_01_F3]
}


def get_region_by_cn(cn: str, planet: Planet, floor: int = 0) -> Optional[Region]:
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


def get_sub_region_by_cn(cn: str, region: Region, floor: int = 0) -> Optional[Region]:
    """
    根据区域的中文 获取对应常量
    :param cn: 区域的中文
    :param region: 所属区域
    :param floor: 子区域的层数
    :return: 常量
    """
    for regions in PLANET_2_REGION.values():
        for r in regions:
            if r.parent is not None and r.parent == region and r.cn == cn and r.floor == floor:
                return r
    return None


def best_match_region_by_name(ocr_word: Optional[str], planet: Optional[Planet] = None) -> Optional[Region]:
    """
    根据OCR结果匹配一个区域 随机返回楼层
    :param ocr_word: OCR结果
    :param planet: 所属星球
    :return:
    """
    if ocr_word is None or len(ocr_word) == 0:
        return None

    to_check_region_name_list: List[str] = []

    for np_id, region_list in PLANET_2_REGION.items():
        if planet is not None and planet.np_id != np_id:
            continue
        for region in region_list:
            region_name = gt(region.cn, 'ocr')
            to_check_region_name_list.append(region_name)

    match = difflib.get_close_matches(ocr_word, to_check_region_name_list, n=1)
    if len(match) == 0:
        return None
    best_match = match[0]

    for np_id, region_list in PLANET_2_REGION.items():
        if planet is not None and planet.np_id != np_id:
            continue
        for region in region_list:
            region_name = gt(region.cn, 'ocr')
            if region_name == best_match:
                return region

    return None


def get_region_by_prl_id(prd_id: str) -> Optional[Region]:
    for np_id, region_list in PLANET_2_REGION.items():
        for region in region_list:
            if region.prl_id == prd_id:
                return region

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

    def __repr__(self):
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
P01_R02_SP03 = TransportPoint('KHZX', '空海之形·凝滞虚影', P01_R02, 'mm_tp_06', (540, 938), (554, 923))
P01_R02_SP04 = TransportPoint('TKDT', '太空电梯', P01_R02, 'mm_sp_02', (556, 986))

# 空间站黑塔 - 收容舱段
P01_R03_SP01 = TransportPoint('ZT', '中庭', P01_R03_F1, 'mm_tp_03', (627, 346), (618, 330))
P01_R03_SP02 = TransportPoint('KZZXW', '控制中心外', P01_R03_F1, 'mm_tp_03', (372, 375), (385, 368))
P01_R03_SP03 = TransportPoint('TSJXS', '特殊解析室', P01_R03_F2, 'mm_tp_03', (766, 439), (752, 448))
P01_R03_SP04 = TransportPoint('WMZJ', '无明之间', P01_R03_F1, 'mm_tp_03', (1040, 510), (1009, 515))
P01_R03_SP05 = TransportPoint('HMZL', '毁灭之蕾·拟造花萼（赤）', P01_R03_F1, 'mm_tp_07', (317, 325), (319, 335))
P01_R03_SP06 = TransportPoint('SFZJ', '霜风之径·侵蚀隧洞', P01_R03_F1, 'mm_tp_09', (848, 367), (841, 368))
P01_R03_SP07 = TransportPoint('LJZZ', '裂界征兆', P01_R03_F1, 'mm_sp_01', (459, 342))
P01_R03_SP08 = TransportPoint('TKDT', '太空电梯', P01_R03_F1, 'mm_sp_02', (607, 364))

# 空间站黑塔 - 支援舱段
P01_R04_SP01 = TransportPoint('BJKF', '备件库房', P01_R04_F2, 'mm_tp_03', (424, 239), (444, 233))
P01_R04_SP02 = TransportPoint('YT', '月台', P01_R04_F2, 'mm_tp_03', (779, 403), (788, 394))
P01_R04_SP03 = TransportPoint('DLS', '电力室', P01_R04_F2, 'mm_tp_03', (155, 413), (127, 380))
P01_R04_SP04 = TransportPoint('CHZL', '存护之蕾·拟造花萼（赤）', P01_R04_F2, 'mm_tp_07', (457, 321), (465, 330))
P01_R04_SP05 = TransportPoint('TKDT', '太空电梯', P01_R04_F2, 'mm_sp_02', (105, 379))
P01_R04_SP06 = TransportPoint('HMDKD', '毁灭的开端·历战余响', P01_R04_F2, 'mm_boss_01', (1000, 285), (1005, 295))

# 空间站黑塔 - 禁闭舱段
P01_R05_SP01 = TransportPoint('WC', '温床', P01_R05_F2, 'mm_tp_03', (684, 306), (710, 309))
P01_R05_SP02 = TransportPoint('JSZX', '集散中心', P01_R05_L3, 'mm_tp_03', (642, 500), (609, 484))
P01_R05_SP03 = TransportPoint('PYM', '培养皿', P01_R05_F1, 'mm_tp_03', (669, 560), (677, 540))
P01_R05_SP04 = TransportPoint('YWZBJ', '药物制备间', P01_R05_F2, 'mm_tp_03', (541, 796), (530, 800))
P01_R05_SP05 = TransportPoint('SWHBX', '生物烘焙箱', P01_R05_F2, 'mm_tp_14', (541, 154), (554, 165))
P01_R05_SP06 = TransportPoint('KJYRYG', '开局一人一狗', P01_R05_F2, 'mm_sp_01', (487, 323))
P01_R05_SP07 = TransportPoint('ZXDJY', '蛀星的旧靥·历战余响', P01_R05_F1, 'mm_boss_04', (571, 526), (582, 529))

# 雅利洛 - 行政区
P02_R01_SP01 = TransportPoint('HJGJY', '黄金歌剧院', P02_R01_F1, 'mm_tp_03', (603, 374), (619, 380))
P02_R01_SP02 = TransportPoint('ZYGC', '中央广场', P02_R01_F1, 'mm_tp_03', (487, 806), (501, 801))
P02_R01_SP03 = TransportPoint('GDBG', '歌德宾馆', P02_R01_F1, 'mm_tp_03', (784, 1173), (776, 1183))
P02_R01_SP04 = TransportPoint('LSWHBWG', '历史文化博物馆', P02_R01_F1, 'mm_tp_05', (395, 771))
P02_R01_SP05 = TransportPoint('CJXY', '城郊雪原', P02_R01_F1, 'mm_sp_02', (485, 370))
P02_R01_SP06 = TransportPoint('BYTL', '边缘通路', P02_R01_F1, 'mm_sp_02', (508, 1113))
P02_R01_SP07 = TransportPoint('TWJQ', '铁卫禁区', P02_R01_F1, 'mm_sp_02', (792, 1259))
P02_R01_SP08 = TransportPoint('SHJ1', '售货机1', P02_R01_F1, 'mm_sp_03', (672, 521))
P02_R01_SP09 = TransportPoint('SS', '书商', P02_R01_F1, 'mm_sp_03', (641, 705))
P02_R01_SP10 = TransportPoint('MBR', '卖报人', P02_R01_F1, 'mm_sp_03', (610, 806))
P02_R01_SP11 = TransportPoint('XZQSD', '行政区商店', P02_R01_F1, 'mm_sp_03', (639, 906))
P02_R01_SP12 = TransportPoint('SHJ2', '售货机2', P02_R01_F1, 'mm_sp_03', (697, 1187))
P02_R01_SP13 = TransportPoint('HDCX', '花店长夏', P02_R01_F1, 'mm_sp_05', (602, 588))
P02_R01_SP14 = TransportPoint('KLBB1', '克里珀堡1', P02_R01_F1, 'mm_sp_05', (769, 732))
P02_R01_SP15 = TransportPoint('KLBB2', '克里珀堡2', P02_R01_F1, 'mm_sp_05', (769, 878))
P02_R01_SP16 = TransportPoint('JWXYD', '机械屋永动', P02_R01_F1, 'mm_sp_05', (727, 918))
P02_R01_SP17 = TransportPoint('GDBGRK', '歌德宾馆入口', P02_R01_F1, 'mm_sp_05', (627, 1152))  # 这个跟传送点冲突 区分一下
P02_R01_SP18 = TransportPoint('PYZ', '磐岩镇', P02_R01_B1, 'mm_sp_02', (641, 778))
P02_R01_SP19 = TransportPoint('SHJ3', '售货机3', P02_R01_B1, 'mm_sp_03', (516, 864))

# 雅利洛 - 城郊雪原
P02_R02_SP01 = TransportPoint('CP', '长坡', P02_R02, 'mm_tp_03', (1035, 319), (1023, 321))
P02_R02_SP02 = TransportPoint('ZLD', '着陆点', P02_R02, 'mm_tp_03', (1283, 367), (1271, 384))
P02_R02_SP03 = TransportPoint('XLZL', '巡猎之蕾·拟造花萼（赤）', P02_R02, 'mm_tp_07', (946, 244), (947, 253))
P02_R02_SP04 = TransportPoint('HYZL', '回忆之蕾·拟造花萼（金）', P02_R02, 'mm_tp_08', (1098, 391), (1103, 399))
P02_R02_SP05 = TransportPoint('XZQ', '行政区', P02_R02, 'mm_sp_02', (444, 109))
P02_R02_SP06 = TransportPoint('LK', '玲可', P02_R02, 'mm_sp_03', (1032, 342))

# 雅利洛 - 边缘通路
P02_R03_SP01 = TransportPoint('HCGC', '候车广场', P02_R03, 'mm_tp_03', (598, 832), (580, 833))
P02_R03_SP02 = TransportPoint('XXGC', '休闲广场', P02_R03, 'mm_tp_03', (690, 480), (701, 491))
P02_R03_SP03 = TransportPoint('GDJZ', '歌德旧宅', P02_R03, 'mm_tp_03', (811, 259), (800, 267))
P02_R03_SP04 = TransportPoint('HGZX', '幻光之形·凝滞虚影', P02_R03, 'mm_tp_06', (450, 840), (474, 842))
P02_R03_SP05 = TransportPoint('FRZL', '丰饶之蕾·拟造花萼（赤）', P02_R03, 'mm_tp_07', (659, 509), (669, 510))
P02_R03_SP06 = TransportPoint('YTZL', '以太之蕾·拟造花萼（金）', P02_R03, 'mm_tp_08', (596, 194), (606, 195))

# 雅利洛 - 铁卫禁区
P02_R04_SP01 = TransportPoint('JQGS', '禁区岗哨', P02_R04, 'mm_tp_03', (1162, 576), (1158, 586))
P02_R04_SP02 = TransportPoint('JQQX', '禁区前线', P02_R04, 'mm_tp_03', (538, 596), (530, 587))
P02_R04_SP03 = TransportPoint('NYSN', '能源枢纽', P02_R04, 'mm_tp_03', (750, 1102), (754, 1090))
P02_R04_SP04 = TransportPoint('YHZX', '炎华之形·凝滞虚影', P02_R04, 'mm_tp_06', (463, 442), (464, 465))
P02_R04_SP05 = TransportPoint('XQZJ', '迅拳之径·侵蚀隧洞', P02_R04, 'mm_tp_09', (1143, 624), (1145, 617))
P02_R04_SP06 = TransportPoint('YYHY', '以眼还眼', P02_R04, 'mm_sp_01', (438, 578))
P02_R04_SP07 = TransportPoint('DBJXQ', '冬兵进行曲', P02_R04, 'mm_sp_01', (723, 1073))
P02_R04_SP08 = TransportPoint('CXHL', '残响回廊', P02_R04, 'mm_sp_02', (314, 589))

# 雅利洛 - 残响回廊
P02_R05_SP01 = TransportPoint('ZCLY', '筑城领域', P02_R05, 'mm_tp_03', (770, 442), (781, 426))
P02_R05_SP02 = TransportPoint('WRGC', '污染广场', P02_R05, 'mm_tp_03', (381, 655), (392, 642))
P02_R05_SP03 = TransportPoint('ZZZHS', '作战指挥室', P02_R05, 'mm_tp_03', (495, 856), (511, 849))
P02_R05_SP04 = TransportPoint('GZCQX', '古战场前线', P02_R05, 'mm_tp_03', (570, 1243), (580, 1232))
P02_R05_SP05 = TransportPoint('MLZX', '鸣雷之形·凝滞虚影', P02_R05, 'mm_tp_06', (526, 640), (505, 639))
P02_R05_SP06 = TransportPoint('SJZX', '霜晶之形·凝滞虚影', P02_R05, 'mm_tp_06', (681, 1231), (657, 1238))
P02_R05_SP07 = TransportPoint('PBZJ', '漂泊之径·侵蚀隧洞', P02_R05, 'mm_tp_09', (654, 242), (660, 246))
P02_R05_SP08 = TransportPoint('TWJQ', '铁卫禁区', P02_R05, 'mm_sp02', (389, 626))
P02_R05_SP09 = TransportPoint('YDL', '永冬岭', P02_R05, 'mm_sp02', (733, 1280))  # 这里旁边站着一个传送到造物之柱的士兵

# 雅利洛 - 永冬岭
P02_R06_SP01 = TransportPoint('GZCXY', '古战场雪原', P02_R06, 'mm_tp_03', (366, 776), (372, 793))
P02_R06_SP02 = TransportPoint('ZWPT', '造物平台', P02_R06, 'mm_tp_03', (784, 571), (811, 566))
P02_R06_SP03 = TransportPoint('RZZJ', '睿治之径·侵蚀隧洞', P02_R06, 'mm_tp_09', (585, 663), (581, 661))
P02_R06_SP04 = TransportPoint('CXHL', '残响回廊', P02_R06, 'mm_sp_02', (338, 793))
P02_R06_SP05 = TransportPoint('HCDLM', '寒潮的落幕·历战余响', P02_R06, 'mm_boss_02', (814, 701))

# 雅利洛 - 造物之柱
P02_R07_SP01 = TransportPoint('ZWZZRK', '造物之柱入口', P02_R07, 'mm_tp_03', (382, 426), (373, 426))
P02_R07_SP02 = TransportPoint('ZWZZSGC', '造物之柱施工场', P02_R07, 'mm_tp_03', (660, 616), (647, 597))
P02_R07_SP03 = TransportPoint('CXHL', '残响回廊', P02_R07, 'mm_sp_02', (313, 346))

# 雅利洛 - 旧武器试验场
P02_R08_SP01 = TransportPoint('JSQDZX', '决胜庆典中心', P02_R08_F2, 'mm_tp_03', (583, 836), (572, 837))
P02_R08_SP02 = TransportPoint('YTZXZD', '以太战线终端', P02_R08_F2, 'mm_tp_12', (525, 792), (539, 792))
P02_R08_SP03 = TransportPoint('MDZ', '铆钉镇', P02_R08_F2, 'mm_sp_02', (591, 1032))

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
P02_R10_SP01 = TransportPoint('RK', '入口', P02_R10, 'mm_tp_03', (333, 166), (344, 179))
P02_R10_SP02 = TransportPoint('LLZBNS', '流浪者避难所', P02_R10, 'mm_tp_03', (778, 349), (769, 334))
P02_R10_SP03 = TransportPoint('FKD', '俯瞰点', P02_R10, 'mm_tp_03', (565, 641), (575, 634))
P02_R10_SP04 = TransportPoint('ZKD', '主矿道', P02_R10, 'mm_tp_03', (530, 757), (525, 747))
P02_R10_SP05 = TransportPoint('FMZX', '锋芒之形·凝滞虚影', P02_R10, 'mm_tp_06', (561, 536), (560, 558))
P02_R10_SP06 = TransportPoint('FZZX', '燔灼之形·凝滞虚影', P02_R10, 'mm_tp_06', (836, 630), (836, 650))
P02_R10_SP07 = TransportPoint('XWZL', '虚无之蕾·拟造花萼（赤）', P02_R10, 'mm_tp_07', (295, 243), (307, 242))
P02_R10_SP08 = TransportPoint('CZZL', '藏珍之蕾·拟造花萼（金）', P02_R10, 'mm_tp_08', (554, 686), (557, 691))
P02_R10_SP09 = TransportPoint('PYZ', '磐岩镇', P02_R10, 'mm_sp_02', (351, 144))

# 雅利洛 - 铆钉镇
P02_R11_SP01 = TransportPoint('GEY', '孤儿院', P02_R11_F1, 'mm_tp_03', (600, 211), (603, 225))
P02_R11_SP02 = TransportPoint('FQSJ', '废弃市集', P02_R11_F1, 'mm_tp_03', (465, 374), (474, 363))
P02_R11_SP03 = TransportPoint('RK', '入口', P02_R11_F1, 'mm_tp_03', (613, 675), (601, 663))
P02_R11_SP04 = TransportPoint('XFZX', '巽风之形·凝滞虚影', P02_R11_F1, 'mm_tp_06', (580, 374), (582, 400))
P02_R11_SP05 = TransportPoint('ZSZL', '智识之蕾·拟造花萼（赤）', P02_R11_F1, 'mm_tp_07', (609, 608), (610, 616))
P02_R11_SP06 = TransportPoint('JWQSYC', '旧武器试验场', P02_R11_F1, 'mm_sp_02', (767, 244))  # 与 机械聚落 重合
P02_R11_SP07 = TransportPoint('PYZ', '磐岩镇', P02_R11_F1, 'mm_sp_02', (597, 698))

# 雅利洛 - 机械聚落
P02_R12_SP01 = TransportPoint('LLZYD', '流浪者营地', P02_R12_F2, 'mm_tp_03', (556, 174), (549, 190))
P02_R12_SP02 = TransportPoint('SQLZD', '史瓦罗驻地', P02_R12_F2, 'mm_tp_03', (554, 506), (567, 510))
P02_R12_SP03 = TransportPoint('NYZHSS', '能源转换设施', P02_R12_F1, 'mm_tp_03', (413, 527), (399, 533))
P02_R12_SP04 = TransportPoint('TXZL', '同谐之蕾·拟造花萼（赤）', P02_R12_F1, 'mm_tp_07', (298, 564), (308, 557))

# 仙舟罗浮 - 星槎海中枢
P03_R01_SP01 = TransportPoint('XCMT', '星槎码头', P03_R01, 'mm_tp_03', (448, 352), (452, 347))
P03_R01_SP02 = TransportPoint('KYT', '坤舆台', P03_R01, 'mm_tp_03', (705, 381), (707, 386))
P03_R01_SP03 = TransportPoint('XYDD', '宣夜大道', P03_R01, 'mm_tp_03', (433, 633), (424, 639))
P03_R01_SP04 = TransportPoint('TKZY', '天空之眼', P03_R01, 'mm_sp_01', (621, 420))
P03_R01_SP05 = TransportPoint('LYD', '流云渡', P03_R01, 'mm_sp_02', (854, 179))
P03_R01_SP06 = TransportPoint('CLT', '长乐天', P03_R01, 'mm_sp_02', (544, 242))
P03_R01_SP07 = TransportPoint('HXG', '廻星港', P03_R01, 'mm_sp_02', (342, 759))
P03_R01_SP08 = TransportPoint('SHJ1', '售货机1', P03_R01, 'mm_sp_03', (608, 317))
P03_R01_SP09 = TransportPoint('ZHPLB', '杂货铺老板', P03_R01, 'mm_sp_03', (577, 493))
P03_R01_SP10 = TransportPoint('BYH', '不夜侯', P03_R01, 'mm_sp_03', (353, 519))
P03_R01_SP11 = TransportPoint('SHJ2', '售货机2', P03_R01, 'mm_sp_03', (365, 549))
P03_R01_SP12 = TransportPoint('SHJ3', '售货机3', P03_R01, 'mm_sp_03', (394, 549))
P03_R01_SP13 = TransportPoint('SZG', '赎珠阁', P03_R01, 'mm_sp_04', (380, 606))
P03_R01_SP14 = TransportPoint('SHJ4', '售货机4', P03_R01, 'mm_sp_03', (321, 709))
P03_R01_SP15 = TransportPoint('XCT', '小吃摊', P03_R01, 'mm_sp_03', (441, 713))
P03_R01_SP16 = TransportPoint('SCG', '司辰宫', P03_R01, 'mm_sp_05', (678, 498))
P03_R01_SP17 = TransportPoint('PSQT', '评书奇谭', P03_R01, 'mm_tp_15', (353, 503), (352, 502))

# 仙舟罗浮 - 流云渡
P03_R02_SP01 = TransportPoint('LYDHD', '流云渡货道', P03_R02_F2, 'mm_tp_03', (710, 432), (700, 412))
P03_R02_SP02 = TransportPoint('JYF', '积玉坊', P03_R02_F1, 'mm_tp_03', (546, 806), (528, 791))
P03_R02_SP03 = TransportPoint('JYFNC', '积玉坊南侧', P03_R02_F1, 'mm_tp_03', (573, 997), (565, 994))
P03_R02_SP04 = TransportPoint('LYDCCC', '流云渡乘槎处', P03_R02_F1, 'mm_tp_03', (584, 1380), (593, 1391))
P03_R02_SP05 = TransportPoint('BLZX', '冰棱之形·凝滞虚影', P03_R02_F1, 'mm_tp_06', (735, 1379), (715, 1378))
P03_R02_SP06 = TransportPoint('SSZJ', '圣颂之径·侵蚀隧洞', P03_R02_F1, 'mm_tp_09', (547, 1165), (548, 1158))
P03_R02_SP07 = TransportPoint('XCHZS', '星槎海中枢', P03_R02_F1, 'mm_sp_02', (584, 1514))
P03_R02_SP08 = TransportPoint('GQYBSGC', '过期邮包收购处', P03_R02_F1, 'mm_sp_03', (393, 789))
P03_R02_SP09 = TransportPoint('HYZLNZHEJ', '回忆之蕾·拟造花萼（金）', P03_R02_F1, 'mm_tp_08', (453, 1239))

# 仙舟罗浮 - 廻星港
P03_R03_SP01 = TransportPoint('FXXZ', '飞星小筑', P03_R03_F2, 'mm_tp_03', (834, 249), (841, 262))
P03_R03_SP02 = TransportPoint('ZCQMJ', '植船区萌甲', P03_R03_F1, 'mm_tp_03', (441, 465), (451, 478))
P03_R03_SP03 = TransportPoint('ZCQFS', '植船区繁生', P03_R03_F1, 'mm_tp_03', (523, 609), (522, 580))
P03_R03_SP04 = TransportPoint('BHQ', '泊航区', P03_R03_F1, 'mm_tp_03', (647, 707), (648, 682))
P03_R03_SP05 = TransportPoint('ZEZX', '震厄之形·凝滞虚影', P03_R03_F1, 'mm_tp_06', (729, 803), (730, 781))
P03_R03_SP06 = TransportPoint('YYZJ', '野焰之径·侵蚀隧洞', P03_R03_F1, 'mm_tp_09', (455, 374), (462, 372))
P03_R03_SP07 = TransportPoint('XCHZS', '星槎海中枢', P03_R03_F2, 'mm_sp_02', (881, 222))

# 仙舟罗浮 - 长乐天
P03_R04_SP01 = TransportPoint('RMT', '若木亭', P03_R04, 'mm_tp_03', (550, 206), (559, 193))
P03_R04_SP02 = TransportPoint('YXT', '悠暇庭', P03_R04, 'mm_tp_03', (589, 530), (593, 519))
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
P03_R05_SP01 = TransportPoint('QKJ', '乾坤街', P03_R05, 'mm_tp_03', (694, 383), (714, 382))
P03_R05_SP02 = TransportPoint('JRXYS', '金人巷夜市', P03_R05, 'mm_tp_03', (432, 521), (459, 470))
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
P03_R06_SP01 = TransportPoint('JHZ', '界寰阵', P03_R06_F1, 'mm_tp_03', (340, 302), (335, 284))
P03_R06_SP02 = TransportPoint('TYQGZ', '太衍穷观阵', P03_R06_F2, 'mm_tp_03', (553, 616), (537, 615))
P03_R06_SP03 = TransportPoint('SST', '授事厅', P03_R06_F2, 'mm_tp_03', (922, 845), (909, 834))
P03_R06_SP04 = TransportPoint('XT', '祥台', P03_R06_F2, 'mm_tp_03', (416, 1192), (430, 1180))
P03_R06_SP05 = TransportPoint('GZS', '工造司', P03_R06_F2, 'mm_sp_02', (1141, 804))
P03_R06_SP06 = TransportPoint('CLT', '长乐天', P03_R06_F2, 'mm_sp_02', (449, 1162))
P03_R06_SP07 = TransportPoint('YTZLNZHEJ', '以太之蕾·拟造花萼（金）', P03_R06_F2, 'mm_tp_08', (728, 1035), (726, 1039))

# 仙舟罗浮 - 工造司
P03_R07_SP01 = TransportPoint('GWYTD', '格物院通道', P03_R07, 'mm_tp_03', (461, 495), (478, 462))
P03_R07_SP02 = TransportPoint('RJFTD', '镕金坊通道', P03_R07, 'mm_tp_03', (821, 612), (793, 605))
P03_R07_SP03 = TransportPoint('XJP', '玄机坪', P03_R07, 'mm_tp_03', (189, 875), (205, 856))
P03_R07_SP04 = TransportPoint('ZHHL', '造化洪炉', P03_R07, 'mm_tp_03', (758, 974), (754, 1000))
P03_R07_SP05 = TransportPoint('YOZX', '偃偶之形·凝滞虚影', P03_R07, 'mm_tp_06', (388, 665), (390, 640))
P03_R07_SP06 = TransportPoint('DDS', '丹鼎司', P03_R07, 'mm_sp_02', (1029, 777))
P03_R07_SP07 = TransportPoint('TBS', '太卜司', P03_R07, 'mm_sp_02', (170, 938))
P03_R07_SP08 = TransportPoint('CZZLNZHEJ', '藏珍之蕾·拟造花萼（金）', P03_R07, 'mm_tp_08', (964, 795), (960, 799))

# 仙舟罗浮 - 丹鼎司
P03_R08_SP01 = TransportPoint('TZDS', '太真丹室', P03_R08_F1, 'mm_tp_03', (548, 565), (563, 570))
P03_R08_SP02 = TransportPoint('GYT', '观颐台', P03_R08_F1, 'mm_tp_03', (439, 705), (448, 718))
P03_R08_SP03 = TransportPoint('XYSJ', '行医市集', P03_R08_F2, 'mm_tp_03', (826, 908), (818, 893))
P03_R08_SP04 = TransportPoint('QHS', '岐黄署', P03_R08_F2, 'mm_tp_03', (819, 1542), (853, 1554))
P03_R08_SP05 = TransportPoint('TRZX', '天人之形·凝滞虚影', P03_R08_F2, 'mm_tp_06', (1226, 1097), (1206, 1097))
P03_R08_SP06 = TransportPoint('YSZJ', '药使之径·侵蚀隧洞', P03_R08_F2, 'mm_tp_09', (667, 1514), (668, 1498))
P03_R08_SP07 = TransportPoint('LYJ', '麟渊境', P03_R08_F1, 'mm_sp_02', (454, 229))
P03_R08_SP08 = TransportPoint('QLT', '祈龙坛', P03_R08_F1, 'mm_sp_02', (187, 721))
P03_R08_SP09 = TransportPoint('SLDY', '蜃楼遁影', P03_R08_F2, 'mm_sp_01', (846, 824))
P03_R08_SP10 = TransportPoint('GZS', '工造司', P03_R08_F2, 'mm_sp_02', (868, 1573))
P03_R08_SP11 = TransportPoint('YRDXYT', '永仁的小药摊', P03_R08_F2, 'mm_sp_03', (990, 768))
P03_R08_SP12 = TransportPoint('GGDYCT', '汵汵的药材摊', P03_R08_F2, 'mm_sp_03', (837, 854))
P03_R08_SP13 = TransportPoint('XWZLNZHEC', '虚无之蕾·拟造花萼（赤）', P03_R08_F2, 'mm_tp_07', (607, 1157), (609, 1154))

# 仙舟罗浮 - 鳞渊境
P03_R09_SP01 = TransportPoint('GXSC', '宫墟深处', P03_R09, 'mm_tp_03', (891, 425), (883, 435))
P03_R09_SP02 = TransportPoint('GHGX', '古海宫墟', P03_R09, 'mm_tp_03', (1113, 425), (1127, 434))
P03_R09_SP03 = TransportPoint('XLDYD', '显龙大雩殿', P03_R09, 'mm_tp_03', (1599, 444), (1592, 433))
P03_R09_SP04 = TransportPoint('NSZX', '孽兽之形·凝滞虚影', P03_R09, 'mm_tp_06', (917, 170), (919, 182))
P03_R09_SP05 = TransportPoint('DDS', '丹鼎司', P03_R09, 'mm_sp_02', (1891, 392))
P03_R09_SP06 = TransportPoint('BSDSS', '不死的神实·历战余响', P03_R09, 'mm_boss_03', (476, 448), (474, 443))
P03_R09_SP07 = TransportPoint('HMZLNZHEC', '毁灭之蕾·拟造花萼（赤）', P03_R09, 'mm_tp_07', (919, 697), (920, 696))

# 仙舟罗浮 - 绥园
P03_R10_SP01 = TransportPoint('YXGCL', '偃息馆长廊', P03_R10, 'mm_tp_03', (867, 402), (868, 417))
P03_R10_SP02 = TransportPoint('THLHM', '谈狐林后门', P03_R10, 'mm_tp_03', (210, 481), (235, 480))
P03_R10_SP03 = TransportPoint('QQTRK', '青丘台入口', P03_R10, 'mm_tp_03', (607, 646), (617, 647))
P03_R10_SP04 = TransportPoint('YYTRK', '燕乐亭入口', P03_R10, 'mm_tp_03', (838, 796), (855, 777))
P03_R10_SP05 = TransportPoint('YFZX', '幽府之形·凝滞虚影', P03_R10, 'mm_tp_06', (152, 679), (155, 658))
P03_R10_SP06 = TransportPoint('YMZJ', '幽冥之径·侵蚀隧洞', P03_R10, 'mm_tp_09', (418, 463), (423, 459))
P03_R10_SP07 = TransportPoint('JHD', '集合点', P03_R10, 'mm_tp_13', (908, 447), (907, 447))
P03_R10_SP08 = TransportPoint('CLT', '长乐天', P03_R10, 'mm_sp_02', (629, 772))
P03_R10_SP09 = TransportPoint('THLCZYT', '谈狐林处镇妖塔', P03_R10, 'mm_sp_08', (235, 409))
P03_R10_SP10 = TransportPoint('YXGCZYT', '偃息馆处镇妖塔', P03_R10, 'mm_sp_08', (839, 461))
P03_R10_SP11 = TransportPoint('QQTCZYT', '青丘台处镇妖塔', P03_R10, 'mm_sp_08', (621, 509))
P03_R10_SP12 = TransportPoint('YYTCZYT', '燕乐亭处镇妖塔', P03_R10, 'mm_sp_08', (832, 710))
P03_R10_SP13 = TransportPoint('DMZCZYT', '狐眠冢处镇妖塔', P03_R10, 'mm_sp_08', (487, 787))
P03_R10_SP14 = TransportPoint('QQTQM', '青丘台栖木', P03_R10, 'mm_sp_09', (488, 516))
P03_R10_SP15 = TransportPoint('DMZQM', '狐眠冢栖木', P03_R10, 'mm_sp_09', (297, 665))
P03_R10_SP16 = TransportPoint('YYTQM', '燕乐亭栖木', P03_R10, 'mm_sp_09', (965, 728))
P03_R10_SP17 = TransportPoint('FRZL', '丰饶之蕾·拟造花萼（赤）', P03_R10, 'mm_tp_07', (189, 823), tp_pos=(194, 821))

# 仙舟罗浮 - 幽囚狱
P03_R11_SP01 = TransportPoint('DYLY', '断狱轮钥', P03_R11_B4, 'mm_tp_03', (1340, 863), (1391, 990))
P03_R11_SP02 = TransportPoint('JRY', '焦热狱', P03_R11_B3, 'mm_tp_03', (1557, 1071), (1554, 1082))
P03_R11_SP03 = TransportPoint('YHYQE', '阴寒域·其二', P03_R11_B1, 'mm_tp_03', (1364, 1215), (1341, 1243))
P03_R11_SP04 = TransportPoint('YHYQY', '阴寒域·其一', P03_R11_B1, 'mm_tp_03', (1200, 1258), (1217, 1264))
P03_R11_SP05 = TransportPoint('AHMTCJT', '阿合马铁窗集团', P03_R11_B1, 'mm_sp_03', (1546, 1384))
P03_R11_SP06 = TransportPoint('AHMTCJTYJS', '阿合马铁窗集团日化研究所', P03_R11_B1, 'mm_sp_03', (1116, 1408))
P03_R11_SP07 = TransportPoint('MFMSXQ', '「魔方秘社」西桥', P03_R11_B1, 'mm_sp_19', (1134, 1214))
P03_R11_SP08 = TransportPoint('KLSZDQ', '勘录舍·栈道前', P03_R11_F1, 'mm_tp_03', (1233, 680), (1232, 698))
P03_R11_SP09 = TransportPoint('ZEM', '镇恶门', P03_R11_F1, 'mm_tp_03', (676, 893), (665, 923))
P03_R11_SP10 = TransportPoint('LYJ', '鳞渊境', P03_R11_F1, 'mm_sp_02', (626, 917))

# 匹诺康尼 - 「白日梦」酒店-现实
P04_R01_SP01 = TransportPoint('JDDT', '酒店大堂', P04_R01_F1, 'mm_tp_03', (587, 413), (571, 399))
P04_R01_SP02 = TransportPoint('GBXXQ', '贵宾休息区', P04_R01_F2, 'mm_tp_03', (557, 696), (571, 701))
P04_R01_SP03 = TransportPoint('ADS', '安德森', P04_R01_F2, 'mm_sp_04', (559, 783))
P04_R01_SP04 = TransportPoint('BJMJDMJ', '「白日梦」酒店-梦境', P04_R01_F3, 'mm_sp_10', (743, 981))

# 匹诺康尼 - 黄金的现实
P04_R02_SP01 = TransportPoint('ZBXZGC', '钟表小子广场', P04_R02_F1, 'mm_tp_03', (1055, 450), (1038, 455))
P04_R02_SP02 = TransportPoint('CMSJ', '沉梦商街', P04_R02_F1, 'mm_tp_03', (1292, 606), (1313, 613))
P04_R02_SP03 = TransportPoint('ZBXZDX', '钟表小子雕像', P04_R02_F1, 'mm_sp_11', (1492, 587))
P04_R02_SP04 = TransportPoint('XXHNXD', '小小哈努行动', P04_R02_F1, 'mm_sp_13', (1034, 395))
P04_R02_SP05 = TransportPoint('ADEGY', '艾迪恩公园', P04_R02_F2, 'mm_tp_03', (721, 282), (700, 265))
P04_R02_SP06 = TransportPoint('TMYY', '甜蜜一隅', P04_R02_F2, 'mm_tp_03', (662, 587), (676, 578))
P04_R02_SP07 = TransportPoint('ADGWZX', '奥帝购物中心', P04_R02_F2, 'mm_tp_03', (1450, 593), (1450, 612))
P04_R02_SP08 = TransportPoint('BRMJDDM', '「白日梦」酒店大门', P04_R02_F2, 'mm_tp_03', (1063, 968), (1037, 944))
P04_R02_SP09 = TransportPoint('ZBXZCC', '钟表小子餐车', P04_R02_F2, 'mm_sp_03', (952, 268))
P04_R02_SP10 = TransportPoint('BKTC', '报刊推车', P04_R02_F2, 'mm_sp_03', (1542, 361))
P04_R02_SP11 = TransportPoint('ZBCT', '钟表餐厅', P04_R02_F2, 'mm_sp_03', (1487, 402))
P04_R02_SP12 = TransportPoint('SLDCC', '苏乐达餐车', P04_R02_F2, 'mm_sp_03', (624, 464))
P04_R02_SP13 = TransportPoint('FDND', '斐迪南德', P04_R02_F2, 'mm_sp_03', (1511, 489))
P04_R02_SP14 = TransportPoint('MDFMD', '梦境贩卖店', P04_R02_F2, 'mm_sp_03', (1577, 645))
P04_R02_SP15 = TransportPoint('PNKNCH', '匹诺康尼车行', P04_R02_F2, 'mm_sp_03', (1552, 737))
P04_R02_SP16 = TransportPoint('BMHCC', '爆米花餐车', P04_R02_F2, 'mm_sp_03', (651, 763))
P04_R02_SP17 = TransportPoint('SLDTC', '苏乐达推车', P04_R02_F2, 'mm_sp_03', (1087, 784))
P04_R02_SP18 = TransportPoint('BQLTC', '冰淇淋推车', P04_R02_F2, 'mm_sp_03', (1517, 798))
P04_R02_SP19 = TransportPoint('XXHNXD', '小小哈努行动', P04_R02_F2, 'mm_sp_11', (673, 882))

# 匹诺康尼 - 筑梦边境
P04_R03_SP01 = TransportPoint('JZJSJ', '家族建设局', P04_R03, 'mm_tp_03', (552, 320), (596, 326))
P04_R03_SP02 = TransportPoint('ZMGC', '筑梦广场', P04_R03, 'mm_tp_03', (1318, 704), (1293, 722))
P04_R03_SP03 = TransportPoint('GJTQ', '观景台前', P04_R03, 'mm_tp_03', (270, 1048), (291, 1059))
P04_R03_SP04 = TransportPoint('WDHY', '屋顶花园', P04_R03, 'mm_tp_03', (882, 1341), (894, 1369))
P04_R03_SP05 = TransportPoint('JZZXNZXY', '焦炙之形·凝滞虚影', P04_R03, 'mm_tp_06', (474, 1054), (453, 1059))
P04_R03_SP06 = TransportPoint('HYZLNZHEJ', '回忆之蕾·拟造花萼（金）', P04_R03, 'mm_tp_08', (272, 1398), (275, 1398))
P04_R03_SP07 = TransportPoint('HJDSK', '黄金的时刻', P04_R03, 'mm_sp_02', (626, 229))
P04_R03_SP08 = TransportPoint('XXHNXD', '小小哈努行动', P04_R03, 'mm_sp_11', (1530, 857))
P04_R03_SP09 = TransportPoint('XLZT', '心灵侦探', P04_R03, 'mm_sp_12', (445, 507))
P04_R03_SP10 = TransportPoint('CSJLDDS', '草树经理的「大树」', P04_R03, 'mm_sp_14', (574, 369))

# 匹诺康尼 - 稚子的梦
P04_R04_SP01 = TransportPoint('HYZL', '回忆走廊', P04_R04, 'mm_tp_03', (614, 564), (593, 555))
P04_R04_SP02 = TransportPoint('FHMJ', '洑洄梦境', P04_R04, 'mm_tp_03', (575, 979), (593, 995))
P04_R04_SP03 = TransportPoint('ZBF', '钟表坊', P04_R04, 'mm_tp_03', (701, 1187), (682, 1198))
P04_R04_SP04 = TransportPoint('YTZLNZHEJ', '以太之蕾·拟造花萼（金）', P04_R04, 'mm_tp_08', (573, 1108), (571, 1106))
P04_R04_SP05 = TransportPoint('CHDGDDS', '赤红大哥的「大树」', P04_R04, 'mm_sp_14', (572, 516))

# 匹诺康尼 - 「白日梦」酒店-梦境
P04_R05_SP01 = TransportPoint('JKS', '监控室', P04_R05_F1, 'mm_tp_03', (344, 524), tp_pos=(370, 496))
P04_R05_SP02 = TransportPoint('MJDT', '梦境大堂', P04_R05_F1, 'mm_tp_03', (1178, 1107), tp_pos=(1155, 1140))
P04_R05_SP03 = TransportPoint('FSFRDDS', '妃色夫人的「大树」', P04_R05_F1, 'mm_sp_14', (1107, 1088))
P04_R05_SP04 = TransportPoint('XXHNXD', '小小哈努行动', P04_R05_F2, 'mm_sp_11', (411, 750))
P04_R05_SP05 = TransportPoint('JMJB', '惊梦酒吧', P04_R05_F3, 'mm_tp_03', (437, 198), tp_pos=(425, 221))
P04_R05_SP06 = TransportPoint('BJKF', '铂金客房', P04_R05_F3, 'mm_tp_03', (1491, 699), tp_pos=(1471, 681))
P04_R05_SP07 = TransportPoint('GBXXSZL', '贵宾休息室走廊', P04_R05_F3, 'mm_tp_03', (493, 737), tp_pos=(459, 745))
P04_R05_SP08 = TransportPoint('BNZXNZXY', '冰酿之形·凝滞虚影', P04_R05_F3, 'mm_tp_06', (206, 745), tp_pos=(230, 747))
P04_R05_SP09 = TransportPoint('TXZLNZHEC', '同谐之蕾·拟造花萼（赤）', P04_R05_F3, 'mm_tp_07', (649, 1054), tp_pos=(651, 1059))
P04_R05_SP10 = TransportPoint('CZZLNZHEJ', '藏珍之蕾·拟造花萼（金）', P04_R05_F3, 'mm_tp_08', (1314, 1397), tp_pos=(1318, 1398))
P04_R05_SP11 = TransportPoint('MQZJQSSD', '梦潜之径·侵蚀隧洞', P04_R05_F3, 'mm_tp_09', (1507, 1354), tp_pos=(1504, 1352))
P04_R05_SP12 = TransportPoint('RMC', '入梦池', P04_R05_F3, 'mm_sp_10', (1493, 680))
P04_R05_SP13 = TransportPoint('TYBT', '调饮吧台', P04_R05_F3, 'mm_tp_17', (410, 273), tp_pos=(417, 273))

P04_R06_SP01 = TransportPoint('MZDT', '梦主大厅', P04_R06_F1, 'mm_tp_03', (535, 430), tp_pos=(576, 458))
P04_R06_SP02 = TransportPoint('CLJLDDS', '草绿经理的「大树」', P04_R06_F1, 'mm_sp_14', (580, 415))
P04_R06_SP03 = TransportPoint('YBC', '迎宾处', P04_R06_F2, 'mm_tp_03', (589, 856), tp_pos=(574, 846))

P04_R06_SUB_01_SP01 = TransportPoint('CSSH', '城市沙盒', P04_R06_SUB_01, 'mm_tp_03', (871, 607), tp_pos=(890, 596))
P04_R06_SUB_01_SP02 = TransportPoint('CNZXNZXY', '嗔怒之形·凝滞虚影', P04_R06_SUB_01, 'mm_tp_06', (678, 708), tp_pos=(663, 710))

P04_R07_SP01 = TransportPoint('YCDM', '影城大门', P04_R07_F1, 'mm_tp_03', (1244, 884), tp_pos=(1262, 910))
P04_R07_SP02 = TransportPoint('HJDSK', '黄金的时刻', P04_R07_F1, 'mm_sp_02', (1272, 910))
P04_R07_SP03 = TransportPoint('WEN', '沃尔纳', P04_R07_F1, 'mm_sp_03', (1146, 819))
P04_R07_SP04 = TransportPoint('CSQLY', '仓鼠球乐园', P04_R07_F2, 'mm_tp_03', (664, 424), tp_pos=(688, 433))
P04_R07_SP05 = TransportPoint('FYQRK', '放映区入口', P04_R07_F2, 'mm_tp_03', (490, 895), tp_pos=(528, 912))
P04_R07_SP06 = TransportPoint('HNBPJD', '哈努帮派基地', P04_R07_F2, 'mm_tp_03', (705, 1456), tp_pos=(702, 1442))
P04_R07_SP07 = TransportPoint('CHZLNZHEC', '存护之蕾·拟造花萼（赤）', P04_R07_F2, 'mm_tp_07', (832, 1243), tp_pos=(837, 1247))
P04_R07_SP08 = TransportPoint('MMXZZTCT', '美梦小镇主题餐厅', P04_R07_F2, 'mm_sp_03', (478, 830))
P04_R07_SP09 = TransportPoint('XXHNXD', '小小哈努行动', P04_R07_F2, 'mm_sp_11', (776, 439))
P04_R07_SP10 = TransportPoint('XXHNXD', '小小哈努行动', P04_R07_F2, 'mm_sp_11', (816, 1405))
P04_R07_SP11 = TransportPoint('HJGZDDS', '黄金公子的「大树」', P04_R07_F2, 'mm_sp_14', (819, 493))
P04_R07_SP12 = TransportPoint('CSQQSSDYJG', '《仓鼠球骑士：速度与坚果》', P04_R07_F2, 'mm_sp_17', (756, 333))
P04_R07_SP13 = TransportPoint('ZSZXNZXY', '职司之形·凝滞虚影', P04_R07_F1, 'mm_tp_06', (855, 1040), tp_pos=(873, 1028))  # 2.2新增
P04_R07_SP14 = TransportPoint('MMWSPSDD', '《美梦往事》拍摄地点', P04_R07_F2, 'mm_tp_16', (332, 909), tp_pos=(332, 909))
P04_R07_SP15 = TransportPoint('HNXDLZD', '《哈努兄弟：狼之道》', P04_R07_F2, 'mm_sp_17', (634, 1465))
P04_R07_SP16 = TransportPoint('HNXDDJA', '哈努兄弟大劫案', P04_R07_F2, 'mm_sp_01', (659, 1420))
P04_R07_SP17 = TransportPoint('MMXZ', '美梦仙踪', P04_R07_F2, 'mm_sp_01', (674, 403))

P04_R08_SP01 = TransportPoint('ZX', '窄巷', P04_R08_F1, 'mm_tp_03', (603, 1382), tp_pos=(596, 1370))
P04_R08_SP02 = TransportPoint('ZZDYG', '稚子的月光', P04_R08_F2, 'mm_tp_03', (576, 270), tp_pos=(593, 306))
P04_R08_SP03 = TransportPoint('SC', '睡城', P04_R08_F2, 'mm_tp_03', (894, 868), (879, 880))
P04_R08_SP04 = TransportPoint('SXGC', '时隙广场', P04_R08_F2, 'mm_tp_03', (614, 930), tp_pos=(592, 940))
P04_R08_SP05 = TransportPoint('JMJZ', '旧梦集镇', P04_R08_F2, 'mm_tp_03', (496, 1073), tp_pos=(495, 1093))
P04_R08_SP06 = TransportPoint('ZZDM', '稚子的梦', P04_R08_F2, 'mm_sp_02', (591, 184))
P04_R08_SP07 = TransportPoint('CSKC', '翠丝快餐', P04_R08_F2, 'mm_sp_03', (355, 854))
P04_R08_SP08 = TransportPoint('ZDYF', '自动乐坊', P04_R08_F2, 'mm_sp_03', (369, 978))
P04_R08_SP09 = TransportPoint('JEK', '基尔克', P04_R08_F2, 'mm_sp_03', (357, 1188))
P04_R08_SP10 = TransportPoint('ZLJSDDS', '湛蓝爵士的「大树」', P04_R08_F2, 'mm_sp_14', (549, 1107))

P04_R09_SP01 = TransportPoint('JXZL', '巨星之路', P04_R09, 'mm_tp_03', (585, 635), tp_pos=(572, 638))
P04_R09_SP02 = TransportPoint('HXGC', '海选广场', P04_R09, 'mm_tp_03', (558, 2155), tp_pos=(570, 2118))
P04_R09_SP03 = TransportPoint('XLZLNZHEC', '巡猎之蕾·拟造花萼（赤）', P04_R09, 'mm_tp_07', (517, 1691), tp_pos=(522, 1693))
P04_R09_SP04 = TransportPoint('CHDGDDS', '赤红大哥的「大树」', P04_R09, 'mm_sp_14', (627, 1694))
P04_R09_SP05 = TransportPoint('FCTK', '返程特快', P04_R09, 'mm_sp_18', (570, 801))
P04_R09_SP06 = TransportPoint('HXTK', '海选特快', P04_R09, 'mm_sp_18', (569, 1581))
P04_R09_SP07 = TransportPoint('YHLTRK', '一号擂台入口', P04_R09, 'mm_sub_02', (337, 1025))
P04_R09_SP08 = TransportPoint('EHLTRK', '二号擂台入口', P04_R09, 'mm_sub_02', (447, 1025))
P04_R09_SP09 = TransportPoint('QHDSLRK', '枪火的试炼入口', P04_R09, 'mm_sub_02', (746, 1192))
P04_R09_SP10 = TransportPoint('SJDSLRK', '时间的试炼入口', P04_R09, 'mm_sub_02', (857, 1192))
P04_R09_SP11 = TransportPoint('YJPTZRK', '演技派挑战入口', P04_R09, 'mm_sub_02', (294, 1404))
P04_R09_SP12 = TransportPoint('DZPTZRK', '动作派挑战入口', P04_R09, 'mm_sub_02', (403, 1404))

P04_R09_SUB_01_SP01 = TransportPoint('JXDFZYHLT', '巨星巅峰战·一号擂台', P04_R09_SUB_01, 'mm_tp_03', (736, 510), tp_pos=(763, 525))
P04_R09_SUB_01_SP02 = TransportPoint('FCTK', '返程特快', P04_R09_SUB_01, 'mm_sp_18', (763, 764))

P04_R09_SUB_02_SP01 = TransportPoint('JXDFZEHLT', '巨星巅峰战·二号擂台', P04_R09_SUB_02, 'mm_tp_03', (792, 525), tp_pos=(766, 539))
P04_R09_SUB_02_SP02 = TransportPoint('FCTK', '返程特快', P04_R09_SUB_02, 'mm_sp_18', (765, 779))

P04_R09_SUB_03_SP01 = TransportPoint('HNZX', '哈努战线', P04_R09_SUB_03_B2, 'mm_sp_17', (763, 452))
P04_R09_SUB_03_SP02 = TransportPoint('XXHNXD', '小小哈努行动', P04_R09_SUB_03_B1, 'mm_sp_11', (733, 461))
P04_R09_SUB_03_SP03 = TransportPoint('QHSJQHDSL', '枪火时间·枪火的试炼', P04_R09_SUB_03_F1, 'mm_tp_03', (743, 525), tp_pos=(731, 537))
P04_R09_SUB_03_SP04 = TransportPoint('XXHNXD', '小小哈努行动', P04_R09_SUB_03_F1, 'mm_sp_11', (732, 438))
P04_R09_SUB_03_SP05 = TransportPoint('FCTK', '返程特快', P04_R09_SUB_03_F1, 'mm_sp_18', (724, 630))
P04_R09_SUB_03_SP06 = TransportPoint('HXTK', '海选特快', P04_R09_SUB_03_B2, 'mm_sp_18', (810, 132))

P04_R09_SUB_04_SP01 = TransportPoint('QHSJSJDSLHF', '枪火时间·时间的试炼（后方）', P04_R09_SUB_04, 'mm_tp_03', (918, 185), tp_pos=(934, 195))
P04_R09_SUB_04_SP02 = TransportPoint('QHSJSJDSL', '枪火时间·时间的试炼', P04_R09_SUB_04, 'mm_tp_03', (403, 545), tp_pos=(419, 554))
P04_R09_SUB_04_SP03 = TransportPoint('HXTK', '海选特快', P04_R09_SUB_04, 'mm_sp_18', (404, 173))
P04_R09_SUB_04_SP04 = TransportPoint('FCTK', '返程特快', P04_R09_SUB_04, 'mm_sp_18', (418, 622))

P04_R09_SUB_05_SP01 = TransportPoint('XMQZYJPTZ', '戏梦奇战·演技派挑战', P04_R09_SUB_05, 'mm_tp_03', (736, 527), tp_pos=(718, 531))
P04_R09_SUB_05_SP02 = TransportPoint('HXTK', '海选特快', P04_R09_SUB_05, 'mm_sp_18', (719, 90))
P04_R09_SUB_05_SP03 = TransportPoint('FCTK', '返程特快', P04_R09_SUB_05, 'mm_sp_18', (717, 687))

P04_R09_SUB_06_SP01 = TransportPoint('XMQZDZPTZ', '戏梦奇战·动作派挑战', P04_R09_SUB_06, 'mm_tp_03', (701, 524), tp_pos=(718, 531))
P04_R09_SUB_06_SP02 = TransportPoint('HXTK', '海选特快', P04_R09_SUB_06, 'mm_sp_18', (716, 89))
P04_R09_SUB_06_SP03 = TransportPoint('FCTK', '返程特快', P04_R09_SUB_06, 'mm_sp_18', (718, 686))

P04_R10_SP01 = TransportPoint('TXDT', '调弦大厅', P04_R10, 'mm_tp_03', (796, 770), tp_pos=(796, 756))
P04_R10_SP02 = TransportPoint('JYT', '交谊厅', P04_R10, 'mm_tp_03', (1306, 790), tp_pos=(1282, 767))
P04_R10_SP03 = TransportPoint('FYSL', '福音沙龙', P04_R10, 'mm_tp_03', (283, 792), tp_pos=(319, 782))
P04_R10_SP04 = TransportPoint('SXCL', '上行长廊', P04_R10, 'mm_tp_03', (813, 1306), tp_pos=(796, 1308))
P04_R10_SP05 = TransportPoint('CMDZLLZYX', '尘梦的赞礼·历战余响', P04_R10, 'mm_boss_05', (793, 298), tp_pos=(796, 309))
P04_R10_SP06 = TransportPoint('XXHNXD', '小小哈努行动', P04_R10, 'mm_sp_11', (1267, 882))
P04_R10_SP07 = TransportPoint('FSFRDDS', '妃色夫人的「大树」', P04_R10, 'mm_sp_14', (322, 891))
P04_R10_SP08 = TransportPoint('ZSZLNZHEC', '智识之蕾·拟造花萼（赤）', P04_R10, 'mm_tp_07', (1022, 383), tp_pos=(1028, 381))
P04_R10_SP09 = TransportPoint('YQZJQSCD', '勇骑之径·侵蚀隧洞', P04_R10, 'mm_tp_09', (222, 627), tp_pos=(228, 631))
P04_R10_SP10 = TransportPoint('', '梦境空间', P04_R10, 'mm_sp_05', (385, 749))



REGION_2_SP = {
    P01_R01.pr_id: [P01_R01_SP03],
    P01_R02.pr_id: [P01_R02_SP01, P01_R02_SP02, P01_R02_SP03, P01_R02_SP04],
    P01_R03_F1.pr_id: [P01_R03_SP01, P01_R03_SP02, P01_R03_SP03, P01_R03_SP04, P01_R03_SP05, P01_R03_SP06, P01_R03_SP07],
    P01_R04_F1.pr_id: [P01_R04_SP01, P01_R04_SP02, P01_R04_SP03, P01_R04_SP04, P01_R04_SP05, P01_R04_SP06],
    P01_R05_F1.pr_id: [P01_R05_SP01, P01_R05_SP02, P01_R05_SP03, P01_R05_SP04, P01_R05_SP05, P01_R05_SP06, P01_R05_SP07],
    P02_R01_F1.pr_id: [
        P02_R01_SP01, P02_R01_SP02, P02_R01_SP03, P02_R01_SP04, P02_R01_SP05, P02_R01_SP06, P02_R01_SP07, P02_R01_SP08, P02_R01_SP09, P02_R01_SP10,
        P02_R01_SP11, P02_R01_SP12, P02_R01_SP13, P02_R01_SP14, P02_R01_SP15, P02_R01_SP16, P02_R01_SP17, P02_R01_SP18, P02_R01_SP19],
    P02_R02.pr_id: [P02_R02_SP01, P02_R02_SP02, P02_R02_SP03, P02_R02_SP04, P02_R02_SP05, P02_R02_SP06],
    P02_R03.pr_id: [P02_R03_SP01, P02_R03_SP02, P02_R03_SP03, P02_R03_SP04, P02_R03_SP05, P02_R03_SP06],
    P02_R04.pr_id: [P02_R04_SP01, P02_R04_SP02, P02_R04_SP03, P02_R04_SP04, P02_R04_SP05, P02_R04_SP06, P02_R04_SP07, P02_R04_SP08],
    P02_R05.pr_id: [P02_R05_SP01, P02_R05_SP02, P02_R05_SP03, P02_R05_SP04, P02_R05_SP05, P02_R05_SP06, P02_R05_SP07, P02_R05_SP08, P02_R05_SP09],
    P02_R06.pr_id: [P02_R06_SP01, P02_R06_SP02, P02_R06_SP03, P02_R06_SP04, P02_R06_SP05],
    P02_R07.pr_id: [P02_R07_SP01, P02_R07_SP02, P02_R07_SP03],
    P02_R08_F2.pr_id: [P02_R08_SP01, P02_R08_SP02, P02_R08_SP03],
    P02_R09.pr_id: [P02_R09_SP01, P02_R09_SP02, P02_R09_SP03, P02_R09_SP04, P02_R09_SP05, P02_R09_SP06, P02_R09_SP07, P02_R09_SP08, P02_R09_SP09, P02_R09_SP10],
    P02_R10.pr_id: [P02_R10_SP01, P02_R10_SP02, P02_R10_SP03, P02_R10_SP04, P02_R10_SP05, P02_R10_SP06, P02_R10_SP07, P02_R10_SP08, P02_R10_SP09],
    P02_R11_F1.pr_id: [P02_R11_SP01, P02_R11_SP02, P02_R11_SP03, P02_R11_SP04, P02_R11_SP05, P02_R11_SP06, P02_R11_SP07],
    P02_R12_F1.pr_id: [P02_R12_SP01, P02_R12_SP02, P02_R12_SP03, P02_R12_SP04],
    P03_R01.pr_id: [P03_R01_SP01, P03_R01_SP02, P03_R01_SP03, P03_R01_SP04, P03_R01_SP05, P03_R01_SP06, P03_R01_SP07, P03_R01_SP08, P03_R01_SP09, P03_R01_SP10,
                    P03_R01_SP11, P03_R01_SP12, P03_R01_SP13, P03_R01_SP14, P03_R01_SP15, P03_R01_SP16],
    P03_R02_F1.pr_id: [P03_R02_SP01, P03_R02_SP02, P03_R02_SP03, P03_R02_SP04, P03_R02_SP05, P03_R02_SP06, P03_R02_SP07, P03_R02_SP08, P03_R02_SP09],
    P03_R03_F1.pr_id: [P03_R03_SP01, P03_R03_SP02, P03_R03_SP03, P03_R03_SP04, P03_R03_SP05, P03_R03_SP06, P03_R03_SP07],
    P03_R04.pr_id: [P03_R04_SP01, P03_R04_SP02, P03_R04_SP03, P03_R04_SP04, P03_R04_SP05, P03_R04_SP06, P03_R04_SP07, P03_R04_SP08, P03_R04_SP09, P03_R04_SP10,
                    P03_R04_SP10, P03_R04_SP11, P03_R04_SP12, P03_R04_SP13, P03_R04_SP14, P03_R04_SP15],
    P03_R05.pr_id: [P03_R05_SP01, P03_R05_SP02, P03_R05_SP03, P03_R05_SP04, P03_R05_SP05, P03_R05_SP06, P03_R05_SP07, P03_R05_SP08, P03_R05_SP09, P03_R05_SP10,
                    P03_R05_SP11, P03_R05_SP12, P03_R05_SP13],
    P03_R06_F1.pr_id: [P03_R06_SP01, P03_R06_SP02, P03_R06_SP03, P03_R06_SP04, P03_R06_SP05, P03_R06_SP06, P03_R06_SP07],
    P03_R07.pr_id: [P03_R07_SP01, P03_R07_SP02, P03_R07_SP03, P03_R07_SP04, P03_R07_SP05, P03_R07_SP06, P03_R07_SP07, P03_R07_SP08],
    P03_R08_F1.pr_id: [P03_R08_SP01, P03_R08_SP02, P03_R08_SP03, P03_R08_SP04, P03_R08_SP05, P03_R08_SP06, P03_R08_SP07, P03_R08_SP08, P03_R08_SP09, P03_R08_SP10,
                       P03_R08_SP11, P03_R08_SP12, P03_R08_SP13],
    P03_R09.pr_id: [P03_R09_SP01, P03_R09_SP02, P03_R09_SP03, P03_R09_SP04, P03_R09_SP05, P03_R09_SP06, P03_R09_SP07],
    P03_R10.pr_id: [P03_R10_SP01, P03_R10_SP02, P03_R10_SP03, P03_R10_SP04, P03_R10_SP05, P03_R10_SP06, P03_R10_SP07, P03_R10_SP08, P03_R10_SP09, P03_R10_SP10,
                    P03_R10_SP11, P03_R10_SP12, P03_R10_SP13, P03_R10_SP14, P03_R10_SP15, P03_R10_SP16, P03_R10_SP17],
    P03_R11_F1.pr_id: [P03_R11_SP01, P03_R11_SP02, P03_R11_SP03, P03_R11_SP04, P03_R11_SP05, P03_R11_SP06, P03_R11_SP07,
                       P03_R11_SP08, P03_R11_SP09, P03_R11_SP10],
    P04_R01_F1.pr_id: [P04_R01_SP01, P04_R01_SP02, P04_R01_SP03, P04_R01_SP04],
    P04_R02_F1.pr_id: [P04_R02_SP01, P04_R02_SP02, P04_R02_SP03, P04_R02_SP04, P04_R02_SP05, P04_R02_SP06, P04_R02_SP07, P04_R02_SP08, P04_R02_SP09, P04_R02_SP10,
                       P04_R02_SP11, P04_R02_SP12, P04_R02_SP13, P04_R02_SP14, P04_R02_SP15, P04_R02_SP16, P04_R02_SP17, P04_R02_SP18, P04_R02_SP19],
    P04_R03.pr_id: [P04_R03_SP01, P04_R03_SP02, P04_R03_SP03, P04_R03_SP04, P04_R03_SP05, P04_R03_SP06, P04_R03_SP07, P04_R03_SP08, P04_R03_SP09, P04_R03_SP10],
    P04_R04.pr_id: [P04_R04_SP01, P04_R04_SP02, P04_R04_SP03, P04_R04_SP04, P04_R04_SP05],
    P04_R05_F1.pr_id: [P04_R05_SP01, P04_R05_SP02, P04_R05_SP03, P04_R05_SP04, P04_R05_SP05, P04_R05_SP06, P04_R05_SP07, P04_R05_SP08, P04_R05_SP09, P04_R05_SP10,
                       P04_R05_SP11, P04_R05_SP12],
    P04_R06_F1.pr_id: [P04_R06_SP01, P04_R06_SP02, P04_R06_SP03],
    P04_R06_SUB_01.pr_id: [P04_R06_SUB_01_SP01, P04_R06_SUB_01_SP02],
    P04_R07_F1.pr_id: [P04_R07_SP01, P04_R07_SP02, P04_R07_SP03, P04_R07_SP04, P04_R07_SP05, P04_R07_SP06, P04_R07_SP07, P04_R07_SP08, P04_R07_SP09, P04_R07_SP10,
                       P04_R07_SP11, P04_R07_SP12, P04_R07_SP13, P04_R07_SP14, P04_R07_SP15, P04_R07_SP16, P04_R07_SP17],
    P04_R08_F1.pr_id: [P04_R08_SP01, P04_R08_SP02, P04_R08_SP03, P04_R08_SP04, P04_R08_SP05, P04_R08_SP06, P04_R08_SP07, P04_R08_SP08, P04_R08_SP09, P04_R08_SP10],
    P04_R09.pr_id: [P04_R09_SP01, P04_R09_SP02, P04_R09_SP03, P04_R09_SP04, P04_R09_SP05, P04_R09_SP06, P04_R09_SP07, P04_R09_SP08, P04_R09_SP09, P04_R09_SP10,
                    P04_R09_SP11, P04_R09_SP12],
    P04_R09_SUB_01.pr_id: [P04_R09_SUB_01_SP01, P04_R09_SUB_01_SP02],
    P04_R09_SUB_02.pr_id: [P04_R09_SUB_02_SP01, P04_R09_SUB_02_SP02],
    P04_R09_SUB_03_B2.pr_id: [P04_R09_SUB_03_SP01, P04_R09_SUB_03_SP02, P04_R09_SUB_03_SP03, P04_R09_SUB_03_SP04, P04_R09_SUB_03_SP05, P04_R09_SUB_03_SP06],
    P04_R09_SUB_04.pr_id: [P04_R09_SUB_04_SP01, P04_R09_SUB_04_SP02, P04_R09_SUB_04_SP03, P04_R09_SUB_04_SP04],
    P04_R09_SUB_05.pr_id: [P04_R09_SUB_05_SP01, P04_R09_SUB_05_SP02, P04_R09_SUB_05_SP03],
    P04_R09_SUB_06.pr_id: [P04_R09_SUB_06_SP01, P04_R09_SUB_06_SP02, P04_R09_SUB_06_SP03],
    P04_R10.pr_id: [P04_R10_SP01, P04_R10_SP02, P04_R10_SP03, P04_R10_SP04, P04_R10_SP05, P04_R10_SP06, P04_R10_SP07, P04_R10_SP08, P04_R10_SP09],
}

def get_sp_by_cn(planet_cn: str, region_cn: str, floor: int, tp_cn: str) -> TransportPoint:
    p: Planet = get_planet_by_cn(planet_cn)
    r: Region = get_region_by_cn(region_cn, p, floor)
    for i in REGION_2_SP.get(r.pr_id):
        if i.cn != tp_cn:
            continue
        return i


def region_with_another_floor(region: Region, floor: int) -> Optional[Region]:
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
    if sp_list is None or len(sp_list) == 0:
        return sp_map
    for sp in sp_list:
        if rect is None or cal_utils.in_rect(sp.lm_pos, rect):
            if sp.template_id not in sp_map:
                sp_map[sp.template_id] = []
            sp_map[sp.template_id].append(sp)

    return sp_map
