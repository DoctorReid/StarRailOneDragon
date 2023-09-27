TEMPLATE_ARROW = "arrow"
TEMPLATE_ARROW_LEN = 30  # 箭头的图片大小
TEMPLATE_ARROW_R = TEMPLATE_ARROW_LEN // 2  # 箭头的图片半径
TEMPLATE_TRANSPORT_LEN = 50  # 传送点的图片大小

THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP = 0.7  # 特殊点模板在大地图上的阈值
THRESHOLD_SP_TEMPLATE_IN_LITTLE_MAP = 0.7  # 特殊点模板在小地图上的阈值
THRESHOLD_SP_TEMPLATE_IN_LITTLE_MAP_CENTER = 0.4  # 特殊点模板在小地图中心的阈值
THRESHOLD_ARROW_IN_LITTLE_MAP = 0.9  # 小地图箭头的阈值

COLOR_WHITE_GRAY = 255  # 地图上道路颜色
COLOR_WHITE_BGR = (255, 255, 255)  # 白色
COLOR_WHITE_BGRA = (255, 255, 255, 255)  # 白色
COLOR_MAP_ROAD_GRAY = 0  # 地图上道路颜色
COLOR_MAP_ROAD_BGR = (0, 0, 0)  # 地图上道路颜色
COLOR_MAP_ROAD_BGRA = (0, 0, 0, 255)  # 地图上道路颜色
COLOR_MAP_EDGE_BGR = (0, 255, 0)  # 地图上边的颜色
COLOR_ARROW_BGR = (255, 200, 0)  # 小箭头颜色
COLOR_ARROW_ALPHA = (0, 0, 0, 0)  # 透明


class LabelValue:

    def __init__(self, id: str, cn: str):
        self.id = id  # id 用在找文件夹之类的
        self.cn = cn  # 中文 用在OCR

    def __str__(self):
        return '%s - %s' % (self.cn, self.id)


R0_GJCX = LabelValue("gjcx", "共享")

P1_KZJ = LabelValue("kjzht", "空间站")
R1_01_ZKCD = LabelValue("zkcd", "主控舱段")
R1_02_JZCD = LabelValue("jzcd", "基座舱段")
R1_03_SRCD = LabelValue("srcd", "收容舱段")
R1_04_ZYCD = LabelValue("zycd", "支援舱段")

P2_YYL = LabelValue("yll6", "雅利洛")
R2_01_XZQ = LabelValue("xzq", "行政区")
R2_09_MDZ = LabelValue("mdz", "铆钉镇")

P3_XZLF = LabelValue("zxlf", "罗浮")


def get_planet_region_by_cn(cn: str) -> LabelValue:
    """
    根据星球或区域的中文 获取对应常量
    :param cn: 星球或区域的中文
    :return: 常量
    """
    arr = [
        R0_GJCX,
        P1_KZJ, R1_01_ZKCD, R1_02_JZCD, R1_03_SRCD, R1_04_ZYCD,
        P2_YYL, R2_01_XZQ, R2_09_MDZ,
        P3_XZLF,
    ]
    for i in arr:
        if i.cn == cn:
            return i
    return None