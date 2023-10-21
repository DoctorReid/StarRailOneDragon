from basic import cal_utils


class Planet:

    def __init__(self, i: str, cn: str, ocr_str: str = None):
        self.id: str = i  # id 用在找文件夹之类的
        self.cn: str = cn  # 中文
        self.ocr_str: str = ocr_str if ocr_str is not None else cn # 用于ocr

    def __str__(self):
        return '%s - %s' % (self.cn, self.id)


P01_KZJ = Planet("kjzht", "空间站黑塔", ocr_str='空间站')
P02_YYL = Planet("yll6", "雅利洛", ocr_str='雅利洛')
P03_XZLF = Planet("xzlf", "仙舟罗浮", ocr_str='罗浮')

PLANET_LIST = [P01_KZJ, P02_YYL, P03_XZLF]


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

    def __init__(self, i: str, cn: str, planet: Planet, level: int = 0, ocr_str: str=None):
        self.id: str = i  # id 用在找文件夹之类的
        self.cn: str = cn  # 中文 用在OCR
        self.planet: Planet = planet
        self.level: int = level
        self.ocr_str: str = cn if ocr_str is None else ocr_str

    def __str__(self):
        return '%s - %s' % (self.cn, self.id)

    def get_pr_id(self):
        return '%s-%s' % (self.planet.id, self.id)

    def get_level_str(self):
        """
        层数 正数用 l1 负数用 b1
        :return:
        """
        if self.level == 0:
            return ''
        elif self.level > 0:
            return '-l%d' % self.level
        elif self.level < 0:
            return 'b%d' % abs(self.level)

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

    def another_floor(self):
        return self.level != 0


R0_GJCX = Region("gjcx", "观景车厢", None)

# 空间站黑塔
P01_R01_ZKCD = Region("zkcd", "主控舱段", P01_KZJ)
P01_R02_JZCD = Region("jzcd", "基座舱段", P01_KZJ)
P01_R03_SRCD_B1 = Region("srcd", "收容舱段", P01_KZJ, -1)
P01_R03_SRCD_L1 = Region("srcd", "收容舱段", P01_KZJ, 1)
P01_R03_SRCD_L2 = Region("srcd", "收容舱段", P01_KZJ, 2)
P01_R04_ZYCD_L1 = Region("zycd", "支援舱段", P01_KZJ, 1)
P01_R04_ZYCD_L2 = Region("zycd", "支援舱段", P01_KZJ, 2)

# 雅利洛
P02_R01_L1 = Region("xzq", "行政区", P02_YYL, level=1)
P02_R01_B1 = Region("xzq", "行政区", P02_YYL, level=-1)
P02_R02 = Region("cjxy", "城郊雪原", P02_YYL)
P02_R03 = Region("bytl", "边缘通路", P02_YYL)
P02_R04 = Region("twjq", "铁卫禁区", P02_YYL)
P02_R05 = Region("cxhl", "残响回廊", P02_YYL)
P02_R06 = Region("ydl", "永冬岭", P02_YYL)
P02_R07 = Region("zwzz", "造物之柱", P02_YYL)
P02_R08_L2 = Region("jwqsyc", "旧武器试验场", P02_YYL, level=2)
P02_R09 = Region("pyz", "磐岩镇", P02_YYL)
P02_R10 = Region("dkq", "大矿区", P02_YYL)
P02_R11_L1 = Region("mdz", "铆钉镇", P02_YYL, level=1)
P02_R11_L2 = Region("mdz", "铆钉镇", P02_YYL, level=2)
P02_R12_L1 = Region("jxjl", "机械聚落", P02_YYL, level=1)
P02_R12_L2 = Region("jxjl", "机械聚落", P02_YYL, level=2)

# 仙舟罗浮
P03_R01 = Region("xchzs", "星槎海中枢", P03_XZLF)
P03_R02_L1 = Region("lyd", "流云渡", P03_XZLF, level=1)
P03_R02_L2 = Region("lyd", "流云渡", P03_XZLF, level=2)
P03_R03_L1 = Region("hxg", "廻星港", P03_XZLF, level=1, ocr_str='迥星港')
P03_R03_L2 = Region("hxg", "廻星港", P03_XZLF, level=2, ocr_str='迥星港')
P03_R04 = Region("clt", "长乐天", P03_XZLF)
P03_R05 = Region("jrx", "金人巷", P03_XZLF)
P03_R06_L1 = Region("tbs", "太卜司", P03_XZLF, level=1)
P03_R06_L2 = Region("tbs", "太卜司", P03_XZLF, level=2)
P03_R07 = Region("gzs", "工造司", P03_XZLF)
P03_R08_L1 = Region("dds", "丹鼎司", P03_XZLF, level=1)
P03_R08_L2 = Region("dds", "丹鼎司", P03_XZLF, level=2)
P03_R09 = Region("lyj", "鳞渊境", P03_XZLF)

PLANET_2_REGION = {
    P01_KZJ.id: [P01_R01_ZKCD, P01_R02_JZCD, P01_R03_SRCD_L1, P01_R03_SRCD_L2, P01_R03_SRCD_B1, P01_R04_ZYCD_L1, P01_R04_ZYCD_L2],
    P02_YYL.id: [P02_R01_L1, P02_R01_B1, P02_R02, P02_R03, P02_R04, P02_R05, P02_R06, P02_R07, P02_R08_L2, P02_R09, P02_R10,
                 P02_R11_L1, P02_R11_L2, P02_R12_L1, P02_R12_L2],
    P03_XZLF.id: [P03_R01, P03_R02_L1, P03_R02_L2, P03_R03_L1, P03_R03_L2, P03_R04, P03_R05, P03_R06_L1, P03_R06_L2,
                  P03_R07, P03_R08_L1, P03_R08_L2, P03_R09]
}


def get_region_by_cn(cn: str, planet: Planet, level: int = 0) -> Region:
    """
    根据区域的中文 获取对应常量
    :param cn: 区域的中文
    :param planet: 所属星球 传入后会判断 为以后可能重名准备
    :param level: 层数
    :return: 常量
    """
    for i in PLANET_2_REGION[planet.id]:
        if i.cn != cn:
            continue
        if level is not None and i.level != level:
            continue
        return i
    return None


class TransportPoint:

    def __init__(self, id: str, cn: str, region: Region, template_id: str, lm_pos: tuple, ocr_str: str = None):
        self.id: str = id  # 英文 用在找图
        self.cn: str = cn  # 中文 用在OCR
        self.region: Region = region  # 所属区域
        self.planet: Planet = region.planet  # 所属星球
        self.template_id: str = template_id  # 匹配模板
        self.lm_pos: tuple = lm_pos  # 在大地图的坐标
        self.ocr_str: str = cn if ocr_str is None else ocr_str

    def __str__(self):
        return '%s - %s' % (self.cn, self.id)


P01_R01_SP01 = TransportPoint('jcy', '监察域', P01_R01_ZKCD, 'mm_tp_03', (529, 231))
P01_R01_SP02 = TransportPoint('hxtl', '核心通路', P01_R01_ZKCD, 'mm_tp_03', (592, 691))
P01_R01_SP03_HTBGS = TransportPoint('htdbgs', '黑塔的办公室', P01_R01_ZKCD, 'mm_tp_04', (245, 796), ocr_str='办公室')
P01_R01_SP04 = TransportPoint('fssq', '封锁扇区', P01_R01_ZKCD, 'mm_sp_01', (228, 744))
P01_R01_SP05 = TransportPoint('tkdt', '太空电梯', P01_R01_ZKCD, 'mm_sp_02', (562, 837))
P01_R01_SP06 = TransportPoint('ngzy', '内购专员', P01_R01_ZKCD, 'mm_sp_04', (535, 628))

# 空间站黑塔 - 基座舱段
P01_R02_SP01_JKS = TransportPoint('jks', '监控室', P01_R02_JZCD, 'mm_tp_03', (635, 143))
P01_R02_SP02 = TransportPoint('jdzx', '接待中心', P01_R02_JZCD, 'mm_tp_03', (493, 500))
P01_R02_SP03 = TransportPoint('khzx', '空海之形', P01_R02_JZCD, 'mm_tp_06', (540, 938))
P01_R02_SP04 = TransportPoint('tkdt', '太空电梯', P01_R02_JZCD, 'mm_sp_02', (556, 986))

# 空间站黑塔 - 收容舱段
P01_R03_SP01_KZZXW = TransportPoint('kzzxw', '控制中心外', P01_R03_SRCD_L1, 'mm_tp_03', (365, 360))
P01_R03_SP02 = TransportPoint('zt', '中庭', P01_R03_SRCD_L1, 'mm_tp_03', (619, 331))
P01_R03_SP03 = TransportPoint('tsjxs', '特殊解析室', P01_R03_SRCD_L2, 'mm_tp_03', (758, 424))
P01_R03_SP04 = TransportPoint('wmzj', '无明之间', P01_R03_SRCD_L1, 'mm_tp_03', (1033, 495))
P01_R03_SP05_HMZL = TransportPoint('hmzl', '毁灭之蕾', P01_R03_SRCD_L1, 'mm_tp_07', (309, 310))
P01_R03_SP06 = TransportPoint('sfzj', '霜风之径', P01_R03_SRCD_L1, 'mm_tp_09', (840, 352))
P01_R03_SP07 = TransportPoint('ljzz', '裂界征兆', P01_R03_SRCD_L1, 'mm_sp_01', (452, 327))
P01_R03_SP08 = TransportPoint('tkdt', '太空电梯', P01_R03_SRCD_L1, 'mm_sp_02', (600, 349))

# 空间站黑塔 - 支援舱段
P01_R04_SP01 = TransportPoint('dls', '电力室', P01_R04_ZYCD_L2, 'mm_tp_03', (155, 380))
P01_R04_SP02 = TransportPoint('bjkf', '备件库房', P01_R04_ZYCD_L2, 'mm_tp_03', (424, 206))
P01_R04_SP03 = TransportPoint('yt', '月台', P01_R04_ZYCD_L2, 'mm_tp_03', (778, 370))
P01_R04_SP04 = TransportPoint('chzl', '存护之蕾', P01_R04_ZYCD_L2, 'mm_tp_07', (457, 288), ocr_str='存护')
P01_R04_SP05 = TransportPoint('tkdt', '太空电梯', P01_R04_ZYCD_L2, 'mm_sp_02', (105, 345))
P01_R04_SP06 = TransportPoint('hmdkd', '毁灭的开端', P01_R04_ZYCD_L2, 'mm_boss_01', (1000, 252))

# 雅利洛 - 行政区
P02_R01_SP01 = TransportPoint('hjgjy', '黄金歌剧院', P02_R01_L1, 'mm_tp_03', (603, 374))
P02_R01_SP02 = TransportPoint('zygc', '中央广场', P02_R01_L1, 'mm_tp_03', (487, 806))
P02_R01_SP03 = TransportPoint('gdbg', '歌德宾馆', P02_R01_L1, 'mm_tp_03', (784, 1173))
P02_R01_SP04 = TransportPoint('lswhbwg', '历史文化博物馆', P02_R01_L1, 'mm_tp_05', (395, 771))
P02_R01_SP05 = TransportPoint('cjxy', '城郊雪原', P02_R01_L1, 'mm_sp_02', (485, 370))
P02_R01_SP06 = TransportPoint('bytl', '边缘通路', P02_R01_L1, 'mm_sp_02', (508, 1113))
P02_R01_SP07 = TransportPoint('twjq', '铁卫禁区', P02_R01_L1, 'mm_sp_02', (792, 1259))
P02_R01_SP08 = TransportPoint('shj-s', '售货机-上', P02_R01_L1, 'mm_sp_03', (672, 521), ocr_str='售货机')
P02_R01_SP09 = TransportPoint('ss', '书商', P02_R01_L1, 'mm_sp_03', (641, 705))
P02_R01_SP10 = TransportPoint('mbr', '卖报人', P02_R01_L1, 'mm_sp_03', (610, 806))
P02_R01_SP11 = TransportPoint('xzqsd', '行政区商店', P02_R01_L1, 'mm_sp_03', (639, 906))
P02_R01_SP12 = TransportPoint('shj-x', '售货机-下', P02_R01_L1, 'mm_sp_03', (697, 1187), ocr_str='售货机')
P02_R01_SP13 = TransportPoint('hd-cx', '花店-长夏', P02_R01_L1, 'mm_sp_05', (602, 588), ocr_str='花店')
P02_R01_SP14 = TransportPoint('klbb-s', '克里珀堡-上', P02_R01_L1, 'mm_sp_05', (769, 732), ocr_str='克里珀堡')
P02_R01_SP15 = TransportPoint('klbb-x', '克里珀堡-下', P02_R01_L1, 'mm_sp_05', (769, 878), ocr_str='克里珀堡')
P02_R01_SP16 = TransportPoint('jxw-yd', '机械屋-永动', P02_R01_L1, 'mm_sp_05', (727, 918))
P02_R01_SP17 = TransportPoint('gdbg-rk', '歌德宾馆-入口', P02_R01_L1, 'mm_sp_05', (627, 1152), ocr_str='歌德宾馆')
P02_R01_SP18 = TransportPoint('pyz', '磐岩镇', P02_R01_B1, 'mm_sp_02', (641, 778))
P02_R01_SP19 = TransportPoint('shj-d', '售货机-底', P02_R01_B1, 'mm_sp_03', (516, 864), ocr_str='售货机')

# 雅利洛 - 城郊雪原
P02_R02_SP01 = TransportPoint('cp', '长坡', P02_R02, 'mm_tp_03', (1035, 319))
P02_R02_SP02 = TransportPoint('zld', '着陆点', P02_R02, 'mm_tp_03', (1283, 367))
P02_R02_SP03 = TransportPoint('xlzl', '巡猎之蕾', P02_R02, 'mm_tp_07', (946, 244))
P02_R02_SP04 = TransportPoint('hyzl', '回忆之蕾', P02_R02, 'mm_tp_08', (1098, 391))
P02_R02_SP05 = TransportPoint('xzq', '行政区', P02_R02, 'mm_sp_02', (444, 109))
P02_R02_SP06 = TransportPoint('lk', '玲可', P02_R02, 'mm_sp_03', (1032, 342))

# 雅利洛 - 边缘通路
P02_R03_SP01 = TransportPoint('hcgc', '候车广场', P02_R03, 'mm_tp_03', (598, 832))
P02_R03_SP02 = TransportPoint('xxgc', '休闲广场', P02_R03, 'mm_tp_03', (690, 480))
P02_R03_SP03 = TransportPoint('gdjz', '歌德旧宅', P02_R03, 'mm_tp_03', (811, 259), ocr_str='歌德')
P02_R03_SP04 = TransportPoint('hgzx', '幻光之形', P02_R03, 'mm_tp_06', (450, 840))
P02_R03_SP05 = TransportPoint('frzl', '丰饶之蕾', P02_R03, 'mm_tp_07', (659, 509))
P02_R03_SP06 = TransportPoint('ytzl', '以太之蕾', P02_R03, 'mm_tp_08', (596, 194))

# 雅利洛 - 铁卫禁区
P02_R04_SP01 = TransportPoint('jqgs', '禁区岗哨', P02_R04, 'mm_tp_03', (1162, 576))
P02_R04_SP02 = TransportPoint('jqqx', '禁区前线', P02_R04, 'mm_tp_03', (538, 596))
P02_R04_SP03 = TransportPoint('nysn', '能源枢纽', P02_R04, 'mm_tp_03', (750, 1102))
P02_R04_SP04 = TransportPoint('yhzx', '炎华之形', P02_R04, 'mm_tp_06', (463, 442))
P02_R04_SP05 = TransportPoint('xqzj', '迅拳之径', P02_R04, 'mm_tp_09', (1143, 624))
P02_R04_SP06 = TransportPoint('yyhy', '以眼还眼', P02_R04, 'mm_sp_01', (438, 578))
P02_R04_SP07 = TransportPoint('dbjxq', '冬兵进行曲', P02_R04, 'mm_sp_01', (723, 1073))
P02_R04_SP08 = TransportPoint('cxhl', '残响回廊', P02_R04, 'mm_sp_02', (314, 589))

# 雅利洛 - 残响回廊
P02_R05_SP01 = TransportPoint('zcly', '筑城领域', P02_R05, 'mm_tp_03', (770, 442))
P02_R05_SP02 = TransportPoint('wrgc', '污染广场', P02_R05, 'mm_tp_03', (381, 655))
P02_R05_SP03 = TransportPoint('zzzhs', '作战指挥室', P02_R05, 'mm_tp_03', (495, 856))
P02_R05_SP04 = TransportPoint('gzcqx', '古战场前线', P02_R05, 'mm_tp_03', (570, 1243))
P02_R05_SP05 = TransportPoint('mlzx', '鸣雷之形', P02_R05, 'mm_tp_06', (526, 640))
P02_R05_SP06 = TransportPoint('sjzx', '霜晶之形', P02_R05, 'mm_tp_06', (681, 1231))
P02_R05_SP07 = TransportPoint('pbzj', '漂泊之径', P02_R05, 'mm_tp_09', (654, 242))
P02_R05_SP08 = TransportPoint('twjq', '铁卫禁区', P02_R05, 'mm_sp02', (389, 626))
P02_R05_SP09 = TransportPoint('ydl', '永冬岭', P02_R05, 'mm_sp02', (733, 1280))  # 这里旁边站着一个传送到造物之柱的士兵

# 雅利洛 - 永冬岭
P02_R06_SP01 = TransportPoint('gzc', '古战场', P02_R06, 'mm_tp_03', (366, 776))
P02_R06_SP02 = TransportPoint('zwpt', '造物平台', P02_R06, 'mm_tp_03', (784, 571))
P02_R06_SP03 = TransportPoint('rzzj', '睿治之径', P02_R06, 'mm_tp_09', (585, 663))
P02_R06_SP04 = TransportPoint('cxhl', '残响回廊', P02_R06, 'mm_sp_02', (338, 793))
P02_R06_SP05 = TransportPoint('hcdlm', '寒潮的落幕', P02_R06, 'mm_boss_02', (814, 701))

# 雅利洛 - 造物之柱
P02_R07_SP01 = TransportPoint('zwzz-rk', '造物之柱-入口', P02_R07, 'mm_tp_03', (382, 426), ocr_str='入口')
P02_R07_SP02 = TransportPoint('zwzz-sgc', '造物之柱-施工场', P02_R07, 'mm_tp_03', (660, 616), ocr_str='施工场')
P02_R07_SP03 = TransportPoint('cxhl', '残响回廊', P02_R07, 'mm_sp_02', (313, 346))

# 雅利洛 - 旧武器试验场
P02_R08_SP01 = TransportPoint('jsqdzx', '决胜庆典中心', P02_R08_L2, 'mm_tp_03', (583, 836))
P02_R08_SP02 = TransportPoint('ytzxzd', '以太战线终端', P02_R08_L2, 'mm_tp_12', (525, 792))
P02_R08_SP03 = TransportPoint('mdz', '铆钉镇', P02_R08_L2, 'mm_sp_02', (591, 1032))

# 雅利洛 - 磐岩镇
P02_R09_SP01 = TransportPoint('gddfd', '歌德大饭店', P02_R09, 'mm_tp_03', (614, 236))
P02_R09_SP02 = TransportPoint('bjjlb', '搏击俱乐部', P02_R09, 'mm_tp_03', (419, 251))
P02_R09_SP03 = TransportPoint('ntsdzs', '娜塔莎的诊所', P02_R09, 'mm_tp_03', (416, 417))
P02_R09_SP04 = TransportPoint('pyzcjls', '磐岩镇超级联赛', P02_R09, 'mm_tp_10', (358, 262))
P02_R09_SP05 = TransportPoint('mdz', '铆钉镇', P02_R09, 'mm_sp_02', (630, 114))
P02_R09_SP06 = TransportPoint('dkq', '大矿区', P02_R09, 'mm_sp_02', (453, 595))
P02_R09_SP07 = TransportPoint('ddsd', '地底商店', P02_R09, 'mm_sp_03', (632, 306))
P02_R09_SP08 = TransportPoint('xct', '小吃摊', P02_R09, 'mm_sp_04', (706, 458))
P02_R09_SP09 = TransportPoint('gddfd', '歌德大饭店', P02_R09, 'mm_sp_05', (688, 222))
P02_R09_SP10 = TransportPoint('ntsdzs-kr', '娜塔莎的诊所-入口', P02_R09, 'mm_sp_05', (393, 475))

# 雅利洛 - 大矿区
P02_R10_SP01 = TransportPoint('rk', '入口', P02_R10, 'mm_tp_03', (333, 166))
P02_R10_SP02 = TransportPoint('llzbns', '流浪者避难所', P02_R10, 'mm_tp_03', (778, 349))
P02_R10_SP03 = TransportPoint('fkd', '俯瞰点', P02_R10, 'mm_tp_03', (565, 641))
P02_R10_SP04 = TransportPoint('zkd', '主矿道', P02_R10, 'mm_tp_03', (530, 757))
P02_R10_SP05 = TransportPoint('fmzx', '锋芒之形', P02_R10, 'mm_tp_06', (561, 536))
P02_R10_SP06 = TransportPoint('fzzx', '燔灼之形', P02_R10, 'mm_tp_06', (836, 630))
P02_R10_SP07 = TransportPoint('xwzl', '虚无之蕾', P02_R10, 'mm_tp_07', (295, 243))
P02_R10_SP08 = TransportPoint('czzl', '藏珍之蕾', P02_R10, 'mm_tp_08', (554, 686))
P02_R10_SP09 = TransportPoint('pyz', '磐岩镇', P02_R10, 'mm_sp_02', (351, 144))

# 雅利洛 - 铆钉镇
P02_R11_SP01 = TransportPoint('gey', '孤儿院', P02_R11_L1, 'mm_tp_03', (600, 211))
P02_R11_SP02 = TransportPoint('fqjs', '废弃市集', P02_R11_L1, 'mm_tp_03', (465, 374))
P02_R11_SP03 = TransportPoint('rk', '入口', P02_R11_L1, 'mm_tp_03', (613, 675))
P02_R11_SP04 = TransportPoint('xfzx', '巽风之形', P02_R11_L1, 'mm_tp_06', (580, 374), ocr_str='风之形')
P02_R11_SP05 = TransportPoint('zszl', '智识之蕾', P02_R11_L1, 'mm_tp_07', (609, 608))
P02_R11_SP06 = TransportPoint('jwqsyc', '旧武器试验场', P02_R11_L1, 'mm_sp_02', (767, 244))  # 与 机械聚落 重合
P02_R11_SP07 = TransportPoint('pyz', '磐岩镇', P02_R11_L1, 'mm_sp_02', (597, 698))

# 雅利洛 - 机械聚落
P02_R12_SP01 = TransportPoint('llzyd', '流浪者营地', P02_R12_L2, 'mm_tp_03', (556, 174))
P02_R12_SP02 = TransportPoint('sqlzd', '史瓦罗驻地', P02_R12_L2, 'mm_tp_03', (554, 506))
P02_R12_SP03 = TransportPoint('nyzhss', '能源转换设施', P02_R12_L1, 'mm_tp_03', (413, 527))
P02_R12_SP04 = TransportPoint('txzl', '同谐之蕾', P02_R12_L1, 'mm_tp_07', (298, 564), ocr_str='同谐')

# 仙舟罗浮 - 星槎海中枢
P03_R01_SP01 = TransportPoint('xcmt', '星槎码头', P03_R01, 'mm_tp_03', (443, 341))
P03_R01_SP02 = TransportPoint('kyt', '坤舆台', P03_R01, 'mm_tp_03', (700, 370))
P03_R01_SP03 = TransportPoint('xydd', '宣夜大道', P03_R01, 'mm_tp_03', (428, 622))
P03_R01_SP04 = TransportPoint('tkzy', '天空之眼', P03_R01, 'mm_sp_01', (616, 409))
P03_R01_SP05 = TransportPoint('lyd', '流云渡', P03_R01, 'mm_sp_02', (849, 168))
P03_R01_SP06 = TransportPoint('clt', '长乐天', P03_R01, 'mm_sp_02', (539, 231))
P03_R01_SP07 = TransportPoint('hxg', '廻星港', P03_R01, 'mm_sp_02', (337, 748))
P03_R01_SP08 = TransportPoint('shj-1', '售货机-1', P03_R01, 'mm_sp_03', (603, 306))
P03_R01_SP09 = TransportPoint('zhplb', '杂货铺老板', P03_R01, 'mm_sp_03', (572, 482))
P03_R01_SP10 = TransportPoint('byh', '不夜侯', P03_R01, 'mm_sp_03', (348, 508))
P03_R01_SP11 = TransportPoint('shj-2', '售货机-2', P03_R01, 'mm_sp_03', (360, 538))
P03_R01_SP12 = TransportPoint('shj-3', '售货机-3', P03_R01, 'mm_sp_03', (389, 538))
P03_R01_SP13 = TransportPoint('szg', '赎珠阁', P03_R01, 'mm_sp_04', (375, 595))
P03_R01_SP14 = TransportPoint('shj-4', '售货机-4', P03_R01, 'mm_sp_03', (316, 698))
P03_R01_SP15 = TransportPoint('xct', '小吃摊', P03_R01, 'mm_sp_03', (436, 702))
P03_R01_SP16 = TransportPoint('scg', '司辰宫', P03_R01, 'mm_sp_05', (673, 487))

# 仙舟罗浮 - 流云渡
P03_R02_SP01 = TransportPoint('lydhd', '流云渡货道', P03_R02_L2, 'mm_tp_03', (704, 422))
P03_R02_SP02 = TransportPoint('jyf', '积玉坊', P03_R02_L1, 'mm_tp_03', (541, 795))
P03_R02_SP03 = TransportPoint('jyfnc', '积玉坊南侧', P03_R02_L1, 'mm_tp_03', (567, 986))
P03_R02_SP04 = TransportPoint('lydccc', '流云渡乘槎处', P03_R02_L1, 'mm_tp_03', (579, 1369))
P03_R02_SP05 = TransportPoint('blzx', '冰棱之形', P03_R02_L1, 'mm_tp_06', (730, 1367))
P03_R02_SP06 = TransportPoint('sszj', '圣颂之径', P03_R02_L1, 'mm_tp_09', (542, 1153))
P03_R02_SP07 = TransportPoint('xchzs', '星槎海中枢', P03_R02_L1, 'mm_sp_02', (578, 1503))
P03_R02_SP08 = TransportPoint('gqybsgc', '过期邮包收购处', P03_R02_L1, 'mm_sp_03', (388, 777))

# 仙舟罗浮 - 廻星港
P03_R03_SP01 = TransportPoint('fxxz', '飞星小筑', P03_R03_L2, 'mm_tp_03', (834, 249))
P03_R03_SP02 = TransportPoint('zcq-mj', '植船区-萌甲', P03_R03_L1, 'mm_tp_03', (441, 465), ocr_str='萌甲')
P03_R03_SP03 = TransportPoint('zcq-fs', '植船区-繁生', P03_R03_L1, 'mm_tp_03', (523, 609), ocr_str='繁生')
P03_R03_SP04 = TransportPoint('bhq', '泊航区', P03_R03_L1, 'mm_tp_03', (647, 707))
P03_R03_SP05 = TransportPoint('zezx', '震厄之形', P03_R03_L1, 'mm_tp_06', (729, 803))
P03_R03_SP06 = TransportPoint('yyzj', '野焰之径', P03_R03_L1, 'mm_tp_09', (455, 374))
P03_R03_SP07 = TransportPoint('xchzs', '星槎海中枢', P03_R03_L2, 'mm_sp_02', (881, 222))



# [21:48:12] [run 39] [INFO]: 当前选择区域 长乐天
# [21:48:12] [run 46] [INFO]: 完成步骤
# [21:48:27] [init_large_map 210] [INFO]: 地图特殊点坐标
# [21:48:27] [init_large_map 214] [INFO]: SP00 = TransportPoint('', '', , 'mm_tp_03', (550, 206))
# [21:48:27] [init_large_map 214] [INFO]: SP01 = TransportPoint('', '', , 'mm_tp_03', (589, 530))
# [21:48:27] [init_large_map 214] [INFO]: SP02 = TransportPoint('', '', , 'mm_sp_02', (697, 104))
# [21:48:27] [init_large_map 214] [INFO]: SP03 = TransportPoint('', '', , 'mm_sp_02', (427, 145))
# [21:48:27] [init_large_map 214] [INFO]: SP04 = TransportPoint('', '', , 'mm_sp_02', (355, 224))
# [21:48:27] [init_large_map 214] [INFO]: SP05 = TransportPoint('', '', , 'mm_sp_02', (380, 465))
# [21:48:27] [init_large_map 214] [INFO]: SP06 = TransportPoint('', '', , 'mm_sp_02', (494, 588))
# [21:48:27] [init_large_map 214] [INFO]: SP07 = TransportPoint('', '', , 'mm_sp_03', (695, 193))
# [21:48:27] [init_large_map 214] [INFO]: SP08 = TransportPoint('', '', , 'mm_sp_03', (745, 232))
# [21:48:27] [init_large_map 214] [INFO]: SP09 = TransportPoint('', '', , 'mm_sp_03', (663, 262))
# [21:48:27] [init_large_map 214] [INFO]: SP10 = TransportPoint('', '', , 'mm_sp_03', (662, 423))
# [21:48:27] [init_large_map 214] [INFO]: SP11 = TransportPoint('', '', , 'mm_sp_03', (444, 505))
# [21:48:27] [init_large_map 214] [INFO]: SP12 = TransportPoint('', '', , 'mm_sp_03', (636, 560))
# [21:48:27] [init_large_map 214] [INFO]: SP13 = TransportPoint('', '', , 'mm_sp_04', (695, 193))
# [21:48:27] [init_large_map 214] [INFO]: SP14 = TransportPoint('', '', , 'mm_sp_04', (744, 232))
# [21:48:27] [init_large_map 214] [INFO]: SP15 = TransportPoint('', '', , 'mm_sp_04', (663, 262))
# [21:48:27] [init_large_map 214] [INFO]: SP16 = TransportPoint('', '', , 'mm_sp_04', (662, 423))
# [21:48:27] [init_large_map 214] [INFO]: SP17 = TransportPoint('', '', , 'mm_sp_04', (443, 506))
# [21:48:27] [init_large_map 214] [INFO]: SP18 = TransportPoint('', '', , 'mm_sp_04', (636, 560))
# [21:48:27] [init_large_map 214] [INFO]: SP19 = TransportPoint('', '', , 'mm_sp_05', (538, 294))

#
# [21:49:27] [run 39] [INFO]: 当前选择区域 金人巷
# [21:49:27] [run 46] [INFO]: 完成步骤
# [21:49:41] [init_large_map 210] [INFO]: 地图特殊点坐标
# [21:49:41] [init_large_map 214] [INFO]: SP00 = TransportPoint('', '', , 'mm_tp_03', (694, 383))
# [21:49:41] [init_large_map 214] [INFO]: SP01 = TransportPoint('', '', , 'mm_tp_03', (432, 521))
# [21:49:41] [init_large_map 214] [INFO]: SP02 = TransportPoint('', '', , 'mm_tp_11', (480, 53))
# [21:49:41] [init_large_map 214] [INFO]: SP03 = TransportPoint('', '', , 'mm_sp_02', (346, 495))
# [21:49:41] [init_large_map 214] [INFO]: SP04 = TransportPoint('', '', , 'mm_sp_03', (365, 275))
# [21:49:41] [init_large_map 214] [INFO]: SP05 = TransportPoint('', '', , 'mm_sp_03', (423, 347))
# [21:49:41] [init_large_map 214] [INFO]: SP06 = TransportPoint('', '', , 'mm_sp_03', (500, 352))
# [21:49:41] [init_large_map 214] [INFO]: SP07 = TransportPoint('', '', , 'mm_sp_03', (653, 369))
# [21:49:41] [init_large_map 214] [INFO]: SP08 = TransportPoint('', '', , 'mm_sp_03', (582, 392))
# [21:49:41] [init_large_map 214] [INFO]: SP09 = TransportPoint('', '', , 'mm_sp_03', (429, 393))
# [21:49:41] [init_large_map 214] [INFO]: SP10 = TransportPoint('', '', , 'mm_sp_03', (491, 395))
# [21:49:41] [init_large_map 214] [INFO]: SP11 = TransportPoint('', '', , 'mm_sp_04', (364, 275))
# [21:49:41] [init_large_map 214] [INFO]: SP12 = TransportPoint('', '', , 'mm_sp_04', (499, 353))
# [21:49:41] [init_large_map 214] [INFO]: SP13 = TransportPoint('', '', , 'mm_sp_04', (653, 369))
# [21:49:41] [init_large_map 214] [INFO]: SP14 = TransportPoint('', '', , 'mm_sp_04', (582, 392))
# [21:49:41] [init_large_map 214] [INFO]: SP15 = TransportPoint('', '', , 'mm_sp_04', (429, 393))
# [21:49:41] [init_large_map 214] [INFO]: SP16 = TransportPoint('', '', , 'mm_sp_04', (491, 395))
# [21:49:41] [init_large_map 214] [INFO]: SP17 = TransportPoint('', '', , 'mm_sp_07', (775, 266))


# [21:51:01] [run 39] [INFO]: 当前选择区域 太卜司
# [21:51:01] [run_ocr 45] [DEBUG]: OCR结果 {'1层': <basic.img.MatchResultList object at 0x0000027B9F62BDD0>}
# [21:51:01] [run 62] [INFO]: 当前层数 1层
# [21:51:01] [run 46] [INFO]: 完成步骤
# [21:51:57] [init_large_map 210] [INFO]: 地图特殊点坐标
# [21:51:57] [init_large_map 214] [INFO]: SP00 = TransportPoint('', '', , 'mm_tp_03', (339, 287))
# [21:51:57] [init_large_map 214] [INFO]: SP01 = TransportPoint('', '', , 'mm_tp_03', (553, 601))
# [21:51:57] [init_large_map 214] [INFO]: SP02 = TransportPoint('', '', , 'mm_tp_03', (922, 830))
# [21:51:57] [init_large_map 214] [INFO]: SP03 = TransportPoint('', '', , 'mm_tp_03', (416, 1177))

#
# [21:53:42] [run 39] [INFO]: 当前选择区域 太卜司
# [21:53:42] [run_ocr 45] [DEBUG]: OCR结果 {'2层': <basic.img.MatchResultList object at 0x000001B5FFDCE9D0>}
# [21:53:42] [run 62] [INFO]: 当前层数 2层
# [21:53:42] [run 46] [INFO]: 完成步骤
# [21:54:37] [init_large_map 210] [INFO]: 地图特殊点坐标
# [21:54:37] [init_large_map 214] [INFO]: SP00 = TransportPoint('', '', , 'mm_tp_03', (340, 287))
# [21:54:37] [init_large_map 214] [INFO]: SP01 = TransportPoint('', '', , 'mm_tp_03', (553, 601))
# [21:54:37] [init_large_map 214] [INFO]: SP02 = TransportPoint('', '', , 'mm_tp_03', (922, 830))
# [21:54:37] [init_large_map 214] [INFO]: SP03 = TransportPoint('', '', , 'mm_tp_03', (415, 1177))
# [21:54:37] [init_large_map 214] [INFO]: SP04 = TransportPoint('', '', , 'mm_sp_02', (1141, 789))
# [21:54:37] [init_large_map 214] [INFO]: SP05 = TransportPoint('', '', , 'mm_sp_02', (449, 1147))


# [21:55:06] [run 39] [INFO]: 当前选择区域 工造司
# [21:55:06] [run 46] [INFO]: 完成步骤
# [21:56:38] [init_large_map 210] [INFO]: 地图特殊点坐标
# [21:56:38] [init_large_map 214] [INFO]: SP00 = TransportPoint('', '', , 'mm_tp_03', (461, 485))
# [21:56:38] [init_large_map 214] [INFO]: SP01 = TransportPoint('', '', , 'mm_tp_03', (821, 602))
# [21:56:38] [init_large_map 214] [INFO]: SP02 = TransportPoint('', '', , 'mm_tp_03', (189, 865))
# [21:56:38] [init_large_map 214] [INFO]: SP03 = TransportPoint('', '', , 'mm_tp_03', (758, 964))
# [21:56:38] [init_large_map 214] [INFO]: SP04 = TransportPoint('', '', , 'mm_tp_06', (388, 655))
# [21:56:38] [init_large_map 214] [INFO]: SP05 = TransportPoint('', '', , 'mm_sp_02', (1029, 767))
# [21:56:38] [init_large_map 214] [INFO]: SP06 = TransportPoint('', '', , 'mm_sp_02', (170, 928))

# [21:58:20] [run 39] [INFO]: 当前选择区域 丹鼎司
# [21:58:20] [run_ocr 45] [DEBUG]: OCR结果 {'1层': <basic.img.MatchResultList object at 0x000002667F047150>}
# [21:58:20] [run 62] [INFO]: 当前层数 1层
# [21:58:20] [run 46] [INFO]: 完成步骤
# [22:00:11] [init_large_map 210] [INFO]: 地图特殊点坐标
# [22:00:11] [init_large_map 214] [INFO]: SP00 = TransportPoint('', '', , 'mm_tp_03', (547, 555))
# [22:00:11] [init_large_map 214] [INFO]: SP01 = TransportPoint('', '', , 'mm_tp_03', (438, 694))
# [22:00:11] [init_large_map 214] [INFO]: SP02 = TransportPoint('', '', , 'mm_tp_03', (826, 898))
# [22:00:11] [init_large_map 214] [INFO]: SP03 = TransportPoint('', '', , 'mm_tp_03', (819, 1533))
# [22:00:11] [init_large_map 214] [INFO]: SP04 = TransportPoint('', '', , 'mm_tp_06', (1225, 1087))
# [22:00:11] [init_large_map 214] [INFO]: SP05 = TransportPoint('', '', , 'mm_tp_09', (667, 1504))
# [22:00:11] [init_large_map 214] [INFO]: SP06 = TransportPoint('', '', , 'mm_sp_02', (453, 218))
# [22:00:12] [init_large_map 214] [INFO]: SP07 = TransportPoint('', '', , 'mm_sp_02', (186, 710))


# [22:01:00] [run 39] [INFO]: 当前选择区域 丹鼎司
# [22:01:00] [run_ocr 45] [DEBUG]: OCR结果 {'2层': <basic.img.MatchResultList object at 0x00000297FFFAAE90>}
# [22:01:00] [run 62] [INFO]: 当前层数 2层
# [22:01:00] [run 46] [INFO]: 完成步骤
# [22:03:00] [init_large_map 210] [INFO]: 地图特殊点坐标
# [22:03:00] [init_large_map 214] [INFO]: SP00 = TransportPoint('', '', , 'mm_tp_03', (547, 555))
# [22:03:00] [init_large_map 214] [INFO]: SP01 = TransportPoint('', '', , 'mm_tp_03', (439, 694))
# [22:03:00] [init_large_map 214] [INFO]: SP02 = TransportPoint('', '', , 'mm_tp_03', (826, 897))
# [22:03:00] [init_large_map 214] [INFO]: SP03 = TransportPoint('', '', , 'mm_tp_03', (818, 1533))
# [22:03:00] [init_large_map 214] [INFO]: SP04 = TransportPoint('', '', , 'mm_tp_06', (1224, 1087))
# [22:03:00] [init_large_map 214] [INFO]: SP05 = TransportPoint('', '', , 'mm_tp_09', (667, 1504))
# [22:03:00] [init_large_map 214] [INFO]: SP06 = TransportPoint('', '', , 'mm_sp_01', (846, 815))
# [22:03:00] [init_large_map 214] [INFO]: SP07 = TransportPoint('', '', , 'mm_sp_02', (867, 1564))
# [22:03:00] [init_large_map 214] [INFO]: SP08 = TransportPoint('', '', , 'mm_sp_03', (990, 758))
# [22:03:00] [init_large_map 214] [INFO]: SP09 = TransportPoint('', '', , 'mm_sp_03', (837, 843))
# [22:03:00] [init_large_map 214] [INFO]: SP10 = TransportPoint('', '', , 'mm_sp_04', (989, 759))
# [22:03:00] [init_large_map 214] [INFO]: SP11 = TransportPoint('', '', , 'mm_sp_04', (836, 844))

# [22:03:38] [run 39] [INFO]: 当前选择区域 鳞渊境
# [22:03:38] [run 46] [INFO]: 完成步骤
# [22:05:02] [init_large_map 210] [INFO]: 地图特殊点坐标
# [22:05:02] [init_large_map 214] [INFO]: SP00 = TransportPoint('', '', , 'mm_tp_03', (891, 345))
# [22:05:02] [init_large_map 214] [INFO]: SP01 = TransportPoint('', '', , 'mm_tp_03', (1113, 345))
# [22:05:02] [init_large_map 214] [INFO]: SP02 = TransportPoint('', '', , 'mm_tp_03', (1599, 364))
# [22:05:02] [init_large_map 214] [INFO]: SP03 = TransportPoint('', '', , 'mm_tp_06', (917, 89))
# [22:05:02] [init_large_map 214] [INFO]: SP04 = TransportPoint('', '', , 'mm_sp_02', (1891, 311))


REGION_2_SP = {
    P01_R01_ZKCD.get_pr_id(): [P01_R01_SP03_HTBGS],
    P01_R02_JZCD.get_pr_id(): [P01_R02_SP01_JKS],
    P01_R03_SRCD_L1.get_pr_id(): [P01_R03_SP01_KZZXW, P01_R03_SP02, P01_R03_SP03, P01_R03_SP04, P01_R03_SP05_HMZL, P01_R03_SP06, P01_R03_SP07],
    P01_R04_ZYCD_L1.get_pr_id(): [P01_R04_SP01, P01_R04_SP02, P01_R04_SP03, P01_R04_SP04, P01_R04_SP05, P01_R04_SP06],
    P02_R01_L1.get_pr_id(): [
        P02_R01_SP01, P02_R01_SP02, P02_R01_SP03, P02_R01_SP04, P02_R01_SP05, P02_R01_SP06, P02_R01_SP07, P02_R01_SP08, P02_R01_SP09, P02_R01_SP10,
        P02_R01_SP11, P02_R01_SP12, P02_R01_SP13, P02_R01_SP14, P02_R01_SP15, P02_R01_SP16, P02_R01_SP17, P02_R01_SP18, P02_R01_SP19],
    P02_R02.get_pr_id(): [P02_R02_SP01, P02_R02_SP02, P02_R02_SP03, P02_R02_SP04, P02_R02_SP05, P02_R02_SP06],
    P02_R03.get_pr_id(): [P02_R03_SP01, P02_R03_SP02, P02_R03_SP03, P02_R03_SP04, P02_R03_SP05, P02_R03_SP06],
    P02_R04.get_pr_id(): [P02_R04_SP01, P02_R04_SP02, P02_R04_SP03, P02_R04_SP04, P02_R04_SP05, P02_R04_SP06, P02_R04_SP07, P02_R04_SP08],
    P02_R05.get_pr_id(): [P02_R05_SP01, P02_R05_SP02, P02_R05_SP03, P02_R05_SP04, P02_R05_SP05, P02_R05_SP06, P02_R05_SP07, P02_R05_SP08, P02_R05_SP09],
    P02_R06.get_pr_id(): [P02_R06_SP01, P02_R06_SP02, P02_R06_SP03, P02_R06_SP04, P02_R06_SP05],
    P02_R07.get_pr_id(): [P02_R07_SP01, P02_R07_SP02, P02_R07_SP03],
    P02_R08_L2.get_pr_id(): [P02_R08_SP01, P02_R08_SP02, P02_R08_SP03],
    P02_R09.get_pr_id(): [P02_R09_SP01, P02_R09_SP02, P02_R09_SP03, P02_R09_SP04, P02_R09_SP05, P02_R09_SP06, P02_R09_SP07, P02_R09_SP08, P02_R09_SP09, P02_R09_SP10],
    P02_R10.get_pr_id(): [P02_R10_SP01, P02_R10_SP02, P02_R10_SP03, P02_R10_SP04, P02_R10_SP05, P02_R10_SP06, P02_R10_SP07, P02_R10_SP08, P02_R10_SP09],
    P02_R11_L1.get_pr_id(): [P02_R11_SP01, P02_R11_SP02, P02_R11_SP03, P02_R11_SP04, P02_R11_SP05, P02_R11_SP06, P02_R11_SP07],
    P02_R12_L1.get_pr_id(): [P02_R12_SP01, P02_R12_SP02, P02_R12_SP03, P02_R12_SP04],
    P03_R01.get_pr_id(): [P03_R01_SP01, P03_R01_SP02, P03_R01_SP03, P03_R01_SP04, P03_R01_SP05, P03_R01_SP06, P03_R01_SP07, P03_R01_SP08, P03_R01_SP09, P03_R01_SP10,
                          P03_R01_SP11, P03_R01_SP12, P03_R01_SP13, P03_R01_SP14, P03_R01_SP15, P03_R01_SP16],
    P03_R02_L1.get_pr_id(): [P03_R02_SP01, P03_R02_SP02, P03_R02_SP03, P03_R02_SP04, P03_R02_SP05, P03_R02_SP06, P03_R02_SP07, P03_R02_SP08],
    P03_R03_L1.get_pr_id(): [P03_R03_SP01, P03_R03_SP02, P03_R03_SP03, P03_R03_SP04, P03_R03_SP05, P03_R03_SP06, P03_R03_SP07]

}


def get_sp_by_cn(planet_cn: str, region_cn: str, level: int, tp_cn: str) -> TransportPoint:
    p: Planet = get_planet_by_cn(planet_cn)
    r: Region = get_region_by_cn(region_cn, p, level)
    for i in REGION_2_SP.get(r.get_pr_id()):
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





def get_sp_type_in_rect(region: Region, rect: tuple) -> dict:
    """
    获取区域特定矩形内的特殊点 按种类分组
    :param region: 区域
    :param rect: 矩形 为空时返回全部
    :return: 特殊点
    """
    sp_list = REGION_2_SP.get(region.get_pr_id())
    sp_map = {}
    for sp in sp_list:
        if rect is None or cal_utils.in_rect(sp.lm_pos, rect):
            if sp.template_id not in sp_map:
                sp_map[sp.template_id] = []
            sp_map[sp.template_id].append(sp)

    return sp_map
