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


R0_GJCX = Region("gjcx", "观景车厢", None)

P01_R01_ZKCD = Region("zkcd", "主控舱段", P01_KZJ)
P01_R02_JZCD = Region("jzcd", "基座舱段", P01_KZJ)
P01_R03_SRCD_L1 = Region("srcd", "收容舱段", P01_KZJ, 1)
P01_R03_SRCD_L2 = Region("srcd", "收容舱段", P01_KZJ, 2)
P01_R03_SRCD_LB1 = Region("srcd", "收容舱段", P01_KZJ, -1)
P01_R04_ZYCD_L1 = Region("zycd", "支援舱段", P01_KZJ, 1)
P01_R04_ZYCD_L2 = Region("zycd", "支援舱段", P01_KZJ, 2)

P02_R01_XZQ = Region("xzq", "行政区", P02_YYL)
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
        P01_R01_ZKCD, P01_R02_JZCD, P01_R03_SRCD_L1, P01_R03_SRCD_L2, P01_R03_SRCD_LB1, P01_R04_ZYCD,
        P02_R01_XZQ, P02_R09_MDZ,
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


P01_R01_TP01_HTBGS = TransportPoint('htbgs', '黑塔办公室', P01_R01_ZKCD, 'mm_tp_04', None)
P01_R02_TP01_JKS = TransportPoint('jks', '监控室', P01_R02_JZCD, 'mm_tp_03', (644.3733488387657, 129.73816947897126))
P01_R03_TP01_KZZXW = TransportPoint('kzzxw', '控制中心外', P01_R03_SRCD_L1, 'mm_tp_03', (377.78668267527456, 350.0337457282807))


def get_tp_by_cn(planet_cn: str, region_cn: str, level: int, tp_cn: str) -> TransportPoint:
    arr = [
        P01_R01_TP01_HTBGS,
        P01_R02_TP01_JKS,
        P01_R03_TP01_KZZXW
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
