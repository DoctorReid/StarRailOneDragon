from typing import Set

from basic import cal_utils


class Planet:

    def __init__(self, i: str, cn: str):
        self.id: str = i  # id 用在找文件夹之类的
        self.cn: str = cn  # 中文 用在OCR

    def __str__(self):
        return '%s - %s' % (self.cn, self.id)


P01_KZJ = Planet("kjzht", "空间站")
P02_YYL = Planet("yll6", "雅利洛")
P03_XZLF = Planet("zxlf", "罗浮")


def get_planet_by_cn(cn: str) -> Planet:
    """
    根据星球的中文 获取对应常量
    :param cn: 星球中文
    :return: 常量
    """
    arr = [P01_KZJ, P02_YYL, P03_XZLF]
    for i in arr:
        if i.cn == cn:
            return i
    return None


class Region:

    def __init__(self, i: str, cn: str, planet: Planet, level: int = 0):
        self.id: str = i  # id 用在找文件夹之类的
        self.cn: str = cn  # 中文 用在OCR
        self.planet: Planet = planet
        self.level: int = level

    def __str__(self):
        return '%s - %s' % (self.cn, self.id)

    def get_pr_id(self):
        return '%s-%s' % (self.planet.id, self.id)

    def get_rl_id(self):
        """
        :return 区域id + 楼层id 用于文件夹
        """
        if self.level == 0:
            return '%s' % self.id
        elif self.level > 0:
            return '%s-l%d' % (self.id, self.level)
        elif self.level < 0:
            return '%s-b%d' % (self.id, abs(self.level))

    def get_prl_id(self):
        """
        :return 星球id + 区域id + 楼层id 用于文件夹
        """
        if self.level == 0:
            return '%s-%s' % (self.planet.id, self.id)
        elif self.level > 0:
            return '%s-%s-l%d' % (self.planet.id, self.id, self.level)
        elif self.level < 0:
            return '%s-%s-b%d' % (self.planet.id, self.id, abs(self.level))


R0_GJCX = Region("gjcx", "观景车厢", None)

P01_R01_ZKCD = Region("zkcd", "主控舱段", P01_KZJ)
P01_R02_JZCD = Region("jzcd", "基座舱段", P01_KZJ)
P01_R03_SRCD_B1 = Region("srcd", "收容舱段", P01_KZJ, -1)
P01_R03_SRCD_L1 = Region("srcd", "收容舱段", P01_KZJ, 1)
P01_R03_SRCD_L2 = Region("srcd", "收容舱段", P01_KZJ, 2)
P01_R04_ZYCD_L1 = Region("zycd", "支援舱段", P01_KZJ, 1)
P01_R04_ZYCD_L2 = Region("zycd", "支援舱段", P01_KZJ, 2)

P02_R01_XZQ = Region("xzq", "行政区", P02_YYL)
P02_R02 = Region("cjxy", "城郊雪原", P02_YYL)
P02_R07 = Region("ydl", "永冬岭", P02_YYL)
P02_R09_MDZ = Region("mdz", "铆钉镇", P02_YYL)


def get_region_by_cn(cn: str, planet: Planet = None, level: int = 0) -> Region:
    """
    根据区域的中文 获取对应常量
    :param cn: 区域的中文
    :param planet: 所属星球 传入后会判断 为以后可能重名准备
    :param level: 层数
    :return: 常量
    """
    arr = [
        R0_GJCX,
        P01_R01_ZKCD, P01_R02_JZCD, P01_R03_SRCD_L1, P01_R03_SRCD_L2, P01_R03_SRCD_B1, P01_R04_ZYCD_L1, P01_R04_ZYCD_L2,
        P02_R01_XZQ, P02_R02, P02_R07, P02_R09_MDZ,
    ]
    for i in arr:
        if i.cn != cn:
            continue
        if planet is not None and i.planet != planet:
            continue
        if level is not None and i.level != level:
            continue
        return i
    return None


class TransportPoint:

    def __init__(self, id: str, cn: str, region: Region, template_id: str, lm_pos: tuple):
        self.id: str = id  # 英文 用在找图
        self.cn: str = cn  # 中文 用在OCR
        self.region: Region = region  # 所属区域
        self.planet: Planet = region.planet  # 所属星球
        self.template_id: str = template_id  # 匹配模板
        self.lm_pos: tuple = lm_pos  # 在大地图的坐标

    def __str__(self):
        return '%s - %s' % (self.cn, self.id)


P01_R01_SP01 = TransportPoint('', '', P01_R01_ZKCD, 'mm_tp_03', (529, 231))
P01_R01_SP02 = TransportPoint('', '', P01_R01_ZKCD, 'mm_tp_03', (592, 691))
P01_R01_SP03_HTBGS = TransportPoint('htdbgs', '办公室', P01_R01_ZKCD, 'mm_tp_04', (245, 796))
P01_R01_SP04 = TransportPoint('', '', P01_R01_ZKCD, 'mm_sp_01', (228, 744))
P01_R01_SP05 = TransportPoint('', '', P01_R01_ZKCD, 'mm_sp_02', (562, 837))
P01_R01_SP06 = TransportPoint('', '', P01_R01_ZKCD, 'mm_sp_04', (535, 628))

P01_R02_SP01_JKS = TransportPoint('jks', '监控室', P01_R02_JZCD, 'mm_tp_03', (635, 143))
P01_R02_SP02 = TransportPoint('', '', P01_R02_JZCD, 'mm_tp_03', (493, 500))
P01_R02_SP03 = TransportPoint('', '', P01_R02_JZCD, 'mm_tp_06', (540, 938))
P01_R02_SP04 = TransportPoint('', '', P01_R02_JZCD, 'mm_tp_06', (556, 986))

# 空间站黑塔 - 收容舱段
P01_R03_SP01_KZZXW = TransportPoint('kzzxw', '控制中心外', P01_R03_SRCD_L1, 'mm_tp_03', (365, 360))
P01_R03_SP02 = TransportPoint('zt', '中庭', P01_R03_SRCD_L1, 'mm_tp_03', (619, 331))
P01_R03_SP03 = TransportPoint('', '', P01_R03_SRCD_L2, 'mm_tp_03', (758, 424))
P01_R03_SP04 = TransportPoint('', '', P01_R03_SRCD_L2, 'mm_tp_03', (1033, 495))
P01_R03_SP05_HMZL = TransportPoint('hmzl', '毁灭之蕾', P01_R03_SRCD_L1, 'mm_tp_07', (309, 310))
P01_R03_SP06 = TransportPoint('', '', P01_R03_SRCD_L1, 'mm_tp_09', (840, 352))
P01_R03_SP07 = TransportPoint('', '', P01_R03_SRCD_L1, 'mm_sp_02', (600, 349))

# 空间站黑塔 - 支援舱段
P01_R04_SP01 = TransportPoint('dls', '电力室', P01_R04_ZYCD_L2, 'mm_tp_03', (155, 380))
P01_R04_SP02 = TransportPoint('bjkf', '备件库房', P01_R04_ZYCD_L2, 'mm_tp_03', (424, 206))
P01_R04_SP03 = TransportPoint('yt', '月台', P01_R04_ZYCD_L2, 'mm_tp_03', (778, 370))
P01_R04_SP04 = TransportPoint('chzl', '存护之蕾', P01_R04_ZYCD_L2, 'mm_tp_07', (457, 288))
P01_R04_SP05 = TransportPoint('tkdt', '太空电梯', P01_R04_ZYCD_L2, 'mm_sp_02', (105, 345))

# 雅利洛 - 城郊雪原
P02_R02_SP01 = TransportPoint('cp', '长坡', P02_R02, 'mm_tp_03', (1035, 319))
P02_R02_SP02 = TransportPoint('zld', '着陆点', P02_R02, 'mm_tp_03', (1283, 367))
P02_R02_SP03 = TransportPoint('xlzl', '巡猎之蕾', P02_R02, 'mm_tp_07', (946, 244))
P02_R02_SP04 = TransportPoint('hyzl', '回忆之蕾', P02_R02, 'mm_tp_08', (1098, 391))
P02_R02_SP05 = TransportPoint('xzq', '行政区', P02_R02, 'mm_sp_02', (444, 109))
P02_R02_SP06 = TransportPoint('lk', '玲可', P02_R02, 'mm_sp_03', (1032, 342))

# 雅利洛 - 永冬岭
P02_R07_SP01 = TransportPoint('gzc', '古战场', P02_R07, 'mm_tp_03', (366, 776))
P02_R07_SP02 = TransportPoint('zwpt', '造物平台', P02_R07, 'mm_tp_03', (784, 571))
P02_R07_SP03 = TransportPoint('rzzj', '睿治之径', P02_R07, 'mm_tp_09', (585, 663))
P02_R07_SP04 = TransportPoint('cxhl', '残响回廊', P02_R07, 'mm_sp_02', (338, 793))


def get_sp_by_cn(planet_cn: str, region_cn: str, level: int, tp_cn: str) -> TransportPoint:
    arr = [
        P01_R01_SP01, P01_R01_SP02, P01_R01_SP03_HTBGS, P01_R01_SP04, P01_R01_SP04, P01_R01_SP05, P01_R01_SP06,
        P01_R02_SP01_JKS, P01_R02_SP02, P01_R02_SP03, P01_R02_SP04,
        P01_R03_SP01_KZZXW, P01_R03_SP02, P01_R03_SP03, P01_R03_SP04, P01_R03_SP05_HMZL, P01_R03_SP06, P01_R03_SP07,
        P01_R04_SP01, P01_R04_SP02, P01_R04_SP03, P01_R04_SP04, P01_R04_SP05,
        P02_R02_SP01, P02_R02_SP02, P02_R02_SP03, P02_R02_SP04, P02_R02_SP05, P02_R02_SP06,
        P02_R07_SP01, P02_R07_SP02, P02_R07_SP03, P02_R07_SP04,
    ]

    for i in arr:
        if i.planet.cn != planet_cn:
            continue
        if i.region.cn != region_cn:
            continue
        if i.region.level != level:
            continue
        if i.cn != tp_cn:
            continue
        return i


def region_with_another_floor(region: Region, level: int) -> Region:
    """
    切换层数
    :param region:
    :param level:
    :return:
    """
    return get_region_by_cn(region.cn, region.planet, level)


region_2_sp = {
    P01_R01_ZKCD.get_pr_id(): [P01_R01_SP03_HTBGS],
    P01_R02_JZCD.get_pr_id(): [P01_R02_SP01_JKS],
    P01_R03_SRCD_L1.get_pr_id(): [P01_R03_SP01_KZZXW, P01_R03_SP02, P01_R03_SP03, P01_R03_SP04, P01_R03_SP05_HMZL, P01_R03_SP06, P01_R03_SP07],
    P01_R04_ZYCD_L1.get_pr_id(): [P01_R04_SP01, P01_R04_SP02, P01_R04_SP03, P01_R04_SP04, P01_R04_SP05],
    P02_R02.get_pr_id(): [P02_R02_SP01, P02_R02_SP02, P02_R02_SP03, P02_R02_SP04, P02_R02_SP05, P02_R02_SP06],
    P02_R07.get_pr_id(): [P02_R07_SP01, P02_R07_SP02, P02_R07_SP03, P02_R07_SP04]
}


def get_sp_type_in_rect(region: Region, rect: tuple) -> dict:
    """
    获取区域特定矩形内的特殊点 按种类分组
    :param region: 区域
    :param rect: 矩形 为空时返回全部
    :return: 特殊点
    """
    sp_list = region_2_sp.get(region.get_pr_id())
    sp_map = {}
    for sp in sp_list:
        if rect is None or cal_utils.in_rect(sp.lm_pos, rect):
            if sp.template_id not in sp_map:
                sp_map[sp.template_id] = []
            sp_map[sp.template_id].append(sp)

    return sp_map
