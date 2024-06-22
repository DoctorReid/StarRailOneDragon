from enum import Enum
from typing import Optional, List

from basic import Rect
from sr.const import map_const
from sr.const.map_const import TransportPoint
from sr.screen_area import ScreenArea
from sr.screen_area.interastral_peace_guide import ScreenGuide
from sr.sim_uni.sim_uni_const import SimUniWorld, OrnamentExtraction, SimUniWorldEnum, OrnamentExtractionEnum, \
    SimUniType, SimUniTypeEnum


class GuideTab:

    def __init__(self, cn: str, num: int, rect: Rect, area: ScreenArea):
        """
        打开指南后 上方的TAB
        """

        self.cn: str = cn
        """中文"""

        self.num: int = num
        """TAB顺序"""

        self.rect: Rect = rect
        """按钮位置"""

        self.area: ScreenArea = area
        """按钮位置"""


class GuideTabEnum(Enum):

    # 这里是没有展开时候的画面
    TAB_1 = GuideTab(cn='每日实训', num=1, rect=Rect(300, 170, 430, 245), area=ScreenGuide.GUIDE_TAB_1.value)
    TAB_2 = GuideTab(cn='生存索引', num=2, rect=Rect(430, 170, 545, 245), area=ScreenGuide.GUIDE_TAB_2.value)
    TAB_3 = GuideTab(cn='模拟宇宙', num=3, rect=Rect(545, 170, 650, 245), area=ScreenGuide.GUIDE_TAB_3.value)
    TAB_4 = GuideTab(cn='逐光捡金', num=4, rect=Rect(650, 170, 780, 245), area=ScreenGuide.GUIDE_TAB_4.value)
    TAB_5 = GuideTab(cn='战术训练', num=5, rect=Rect(780, 170, 900, 245), area=ScreenGuide.GUIDE_TAB_5.value)


class GuideCategory:

    def __init__(self, tab: GuideTab, cn: str, ui_cn: Optional[str] = None):
        """
        打开指南页后 左侧显示的分类
        """

        self.tab: GuideTab = tab
        """指南上的TAB"""

        self.cn: str = cn
        """中文"""

        self.ui_cn: str = cn if ui_cn is None else ui_cn
        """界面展示的中文"""


class GuideCategoryEnum(Enum):

    BUD_1 = GuideCategory(tab=GuideTabEnum.TAB_2.value, cn='拟造花萼（金）', ui_cn='经验信用')
    BUD_2 = GuideCategory(tab=GuideTabEnum.TAB_2.value, cn='拟造花萼（赤）', ui_cn='光锥行迹')
    SHAPE = GuideCategory(tab=GuideTabEnum.TAB_2.value, cn='凝滞虚影', ui_cn='角色突破')
    PATH = GuideCategory(tab=GuideTabEnum.TAB_2.value, cn='侵蚀虫洞', ui_cn='遗器')
    ECHO_OF_WAR = GuideCategory(tab=GuideTabEnum.TAB_2.value, cn='历战余响')
    SI_SIM_UNI = GuideCategory(tab=GuideTabEnum.TAB_2.value, cn='模拟宇宙')
    ORNAMENT_EXTRACTION = GuideCategory(tab=GuideTabEnum.TAB_2.value, cn='饰品提取')

    SU_OE = GuideCategory(tab=GuideTabEnum.TAB_3.value, cn='差分宇宙')
    SU_SIM_UNI = GuideCategory(tab=GuideTabEnum.TAB_3.value, cn='模拟宇宙')

    @staticmethod
    def get_by_ui_cn(ui_cn: str, tab=GuideTabEnum.TAB_2.value) -> Optional[GuideCategory]:
        for enum in GuideCategoryEnum:
            if enum.value.tab == tab and enum.value.ui_cn == ui_cn:
                return enum.value
        return None


class GuideSubCategory:

    def __init__(self, cate: GuideCategory, area: ScreenArea):
        """
        打开指南页后 选择左侧分类后 右侧出现的二级分类
        """
        self.cate: GuideCategory = cate
        self.area: ScreenArea = area


class GuideSubCategoryEnum(Enum):

    BUD_1_YYL = GuideSubCategory(GuideCategoryEnum.BUD_1.value, ScreenGuide.BUD_1_SUB_CATE_1.value)
    BUD_1_XZLF = GuideSubCategory(GuideCategoryEnum.BUD_1.value, ScreenGuide.BUD_1_SUB_CATE_2.value)
    BUD_1_PNKN = GuideSubCategory(GuideCategoryEnum.BUD_1.value, ScreenGuide.BUD_1_SUB_CATE_3.value)


class GuideMission:

    def __init__(self, cate: GuideCategory, power: int,
                 tp: Optional[TransportPoint] = None,
                 sim_world: Optional[SimUniWorld] = None,
                 ornament_extraction: Optional[OrnamentExtraction] = None,
                 sim_uni_type: Optional[SimUniType] = None,
                 sub_cate: Optional[GuideSubCategory] = None,
                 show_in_tp_plan: bool = True,
                 ):
        """
        打开指南页面后 右侧显示的具体关卡
        """

        self.cate: GuideCategory = cate
        """指南页面的左侧分类"""

        self.sub_cate: Optional[GuideSubCategory] = sub_cate
        """指南页面右侧的二级分类"""

        self.power: int = power
        """挑战一次需要的开拓力"""

        self.tp: TransportPoint = tp
        """地图上的传送点 有的话就传入"""

        self.sim_world: SimUniWorld = sim_world
        """挑战的模拟宇宙世界 有的话就传入"""

        self.ornament_extraction: OrnamentExtraction = ornament_extraction
        """饰品提取的关卡 有的话就传入"""

        self.sim_uni_type: SimUniType = sim_uni_type
        """选择的模拟宇宙类型 有的话就传入"""

        self.show_in_tp_plan: bool = show_in_tp_plan
        """是否在开拓力计划中显示"""

    @property
    def ui_cn(self) -> str:
        """
        在UI上显示的简短名称
        :return:
        """
        if self.cate == GuideCategoryEnum.BUD_1.value:
            if self.tp in [map_const.P02_R02_SP04, map_const.P03_R06_SP07, map_const.P04_R03_SP06]:
                prefix = '角色经验'
            elif self.tp in [map_const.P02_R03_SP06, map_const.P03_R02_SP09, map_const.P04_R04_SP04]:
                prefix = '光锥经验'
            elif self.tp in [map_const.P02_R10_SP08, map_const.P03_R07_SP08, map_const.P04_R05_SP10]:
                prefix = '信用点'
            else:
                prefix = ''
            return prefix + '·' + self.sub_cate.area.text
        elif self.cate == GuideCategoryEnum.BUD_2.value:
            return self.tp.cn[:2] + '·' + self.tp.region.cn
        elif self.cate == GuideCategoryEnum.SHAPE.value:
            if self.tp in [map_const.P01_R02_SP03, map_const.P03_R09_SP04, map_const.P04_R03_SP05]:
                prefix = '量子'
            elif self.tp in [map_const.P02_R11_SP04, map_const.P03_R08_SP05]:
                prefix = '风'
            elif self.tp in [map_const.P02_R05_SP05, map_const.P03_R03_SP05]:
                prefix = '雷'
            elif self.tp in [map_const.P02_R04_SP04, map_const.P02_R10_SP06, map_const.P04_R06_SUB_01_SP02]:
                prefix = '火'
            elif self.tp in [map_const.P02_R10_SP05, map_const.P03_R10_SP05, map_const.P04_R07_SP13]:
                prefix = '物理'
            elif self.tp in [map_const.P02_R05_SP06, map_const.P03_R02_SP05, map_const.P04_R05_SP08]:
                prefix = '冰'
            elif self.tp in [map_const.P02_R03_SP04, map_const.P03_R07_SP05]:
                prefix = '虚数'
            else:
                prefix = ''
            return prefix + '·' + self.tp.region.cn
        elif self.cate == GuideCategoryEnum.PATH.value:
            if self.tp == map_const.P01_R03_SP06:
                return '猎人 翔鹰'
            elif self.tp == map_const.P02_R04_SP05:
                return '拳王 怪盗'
            elif self.tp == map_const.P02_R05_SP07:
                return '过客 快枪手'
            elif self.tp == map_const.P02_R06_SP03:
                return '铁卫 天才'
            elif self.tp == map_const.P03_R02_SP06:
                return '圣骑士 乐队'
            elif self.tp == map_const.P03_R03_SP06:
                return '火匠 废土客'
            elif self.tp == map_const.P03_R08_SP06:
                return '莳者 信使'
            elif self.tp == map_const.P03_R10_SP06:
                return '大公 系囚'
            elif self.tp == map_const.P04_R05_SP11:
                return '先驱 钟表匠'
            else:
                return ''
        elif self.cate == GuideCategoryEnum.SI_SIM_UNI.value:
            return self.sim_world.name
        elif self.cate == GuideCategoryEnum.ECHO_OF_WAR.value:
            return self.tp.cn[:-5]  # 去除 '·历战余响'
        elif self.cate == GuideCategoryEnum.ORNAMENT_EXTRACTION.value:
            return self.ornament_extraction.name
        elif self.cate == GuideCategoryEnum.SU_SIM_UNI.value:
            return self.sim_uni_type.name
        else:
            return ''

    @property
    def unique_id(self) -> str:
        if self.tp is not None:
            return self.tp.unique_id
        elif self.sim_world is not None:
            return self.sim_world.unique_id
        elif self.ornament_extraction is not None:
            return self.ornament_extraction.unique_id
        elif self.sim_uni_type is not None:
            return self.sim_uni_type.uid
        else:
            return ''

    @property
    def name_in_guide(self) -> str:
        """
        在指南中显示的名字
        :return:
        """
        if self.tp is not None:
            return self.tp.cn
        elif self.sim_world is not None:
            return self.sim_world.name
        elif self.ornament_extraction is not None:
            return self.ornament_extraction.name
        elif self.sim_uni_type is not None:
            return self.sim_uni_type.name
        else:
            return ''


class GuideMissionEnum(Enum):

    BUD_1_YLL_1 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P02_R02_SP04, sub_cate=GuideSubCategoryEnum.BUD_1_YYL.value, power=10)
    BUD_1_YLL_2 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P02_R03_SP06, sub_cate=GuideSubCategoryEnum.BUD_1_YYL.value, power=10)
    BUD_1_YLL_3 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P02_R10_SP08, sub_cate=GuideSubCategoryEnum.BUD_1_YYL.value, power=10)

    BUG_1_XZLF_1 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P03_R06_SP07, sub_cate=GuideSubCategoryEnum.BUD_1_XZLF.value, power=10)
    BUG_1_XZLF_2 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P03_R02_SP09, sub_cate=GuideSubCategoryEnum.BUD_1_XZLF.value, power=10)
    BUG_1_XZLF_3 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P03_R07_SP08, sub_cate=GuideSubCategoryEnum.BUD_1_XZLF.value, power=10)

    BUD_1_PNKN_1 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P04_R03_SP06, sub_cate=GuideSubCategoryEnum.BUD_1_PNKN.value, power=10)
    BUD_1_PNKN_2 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P04_R04_SP04, sub_cate=GuideSubCategoryEnum.BUD_1_PNKN.value, power=10)
    BUD_1_PNKN_3 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P04_R05_SP10, sub_cate=GuideSubCategoryEnum.BUD_1_PNKN.value, power=10)

    BUD_2_HM_1 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P01_R03_SP05, power=10)
    BUD_2_HM_2 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P03_R09_SP07, power=10)

    BUD_2_CH_1 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P01_R04_SP04, power=10)
    BUD_2_CH_2 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P04_R07_SP07, power=10)

    BUD_2_XL_1 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P02_R02_SP03, power=10)
    BUD_2_XL_2 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P04_R09_SP03, power=10)

    BUD_2_FR_1 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P02_R03_SP05, power=10)
    BUD_2_FR_2 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P03_R10_SP17, power=10)

    BUD_2_ZS_1 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P02_R11_SP05, power=10)

    BUD_2_TX_1 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P02_R12_SP04, power=10)
    BUD_2_TX_2 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P04_R05_SP09, power=10)

    BUD_2_XW_1 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P02_R10_SP07, power=10)
    BUD_2_XW_2 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P03_R08_SP13, power=10)

    SHAPE_01 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P02_R11_SP04, power=30)
    SHAPE_02 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P02_R05_SP05, power=30)
    SHAPE_03 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P02_R04_SP04, power=30)
    SHAPE_04 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P02_R10_SP05, power=30)
    SHAPE_05 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P02_R05_SP06, power=30)
    SHAPE_06 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P02_R03_SP04, power=30)
    SHAPE_07 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P03_R02_SP05, power=30)
    SHAPE_08 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P03_R03_SP05, power=30)
    SHAPE_09 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P03_R07_SP05, power=30)
    SHAPE_10 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P02_R10_SP06, power=30)
    SHAPE_11 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P03_R08_SP05, power=30)
    SHAPE_12 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P01_R02_SP03, power=30)
    SHAPE_13 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P03_R09_SP04, power=30)
    SHAPE_14 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P03_R10_SP05, power=30)
    SHAPE_15 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P04_R05_SP08, power=30)
    SHAPE_16 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P04_R03_SP05, power=30)
    SHAPE_17 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P04_R06_SUB_01_SP02, power=30)
    SHAPE_18 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P04_R07_SP13, power=30)

    PATH_01 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P02_R04_SP05, power=40)
    PATH_02 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P02_R05_SP07, power=40)
    PATH_03 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P02_R06_SP03, power=40)
    PATH_04 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P03_R02_SP06, power=40)
    PATH_05 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P03_R03_SP06, power=40)
    PATH_06 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P03_R08_SP06, power=40)
    PATH_07 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P03_R10_SP06, power=40)
    PATH_08 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P01_R03_SP06, power=40)
    PATH_09 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P04_R05_SP11, power=40)

    ECHO_01 = GuideMission(cate=GuideCategoryEnum.ECHO_OF_WAR.value, tp=map_const.P01_R04_SP06, power=30)
    ECHO_02 = GuideMission(cate=GuideCategoryEnum.ECHO_OF_WAR.value, tp=map_const.P02_R06_SP05, power=30)
    ECHO_03 = GuideMission(cate=GuideCategoryEnum.ECHO_OF_WAR.value, tp=map_const.P03_R09_SP06, power=30)
    ECHO_04 = GuideMission(cate=GuideCategoryEnum.ECHO_OF_WAR.value, tp=map_const.P01_R05_SP07, power=30)
    ECHO_05 = GuideMission(cate=GuideCategoryEnum.ECHO_OF_WAR.value, tp=map_const.P04_R10_SP08, power=30)

    SIM_UNI_00 = GuideMission(cate=GuideCategoryEnum.SI_SIM_UNI.value, sim_world=SimUniWorldEnum.WORLD_00.value, power=40, show_in_tp_plan=False)
    SIM_UNI_03 = GuideMission(cate=GuideCategoryEnum.SI_SIM_UNI.value, sim_world=SimUniWorldEnum.WORLD_03.value, power=40)
    SIM_UNI_04 = GuideMission(cate=GuideCategoryEnum.SI_SIM_UNI.value, sim_world=SimUniWorldEnum.WORLD_04.value, power=40)
    SIM_UNI_05 = GuideMission(cate=GuideCategoryEnum.SI_SIM_UNI.value, sim_world=SimUniWorldEnum.WORLD_05.value, power=40)
    SIM_UNI_06 = GuideMission(cate=GuideCategoryEnum.SI_SIM_UNI.value, sim_world=SimUniWorldEnum.WORLD_06.value, power=40)
    SIM_UNI_07 = GuideMission(cate=GuideCategoryEnum.SI_SIM_UNI.value, sim_world=SimUniWorldEnum.WORLD_07.value, power=40)
    SIM_UNI_08 = GuideMission(cate=GuideCategoryEnum.SI_SIM_UNI.value, sim_world=SimUniWorldEnum.WORLD_08.value, power=40)
    SIM_UNI_09 = GuideMission(cate=GuideCategoryEnum.SI_SIM_UNI.value, sim_world=SimUniWorldEnum.WORLD_09.value, power=40)

    OE_10 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_10.value, power=40)
    OE_09 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_09.value, power=40)
    OE_08 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_08.value, power=40)
    OE_07 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_07.value, power=40)
    OE_06 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_06.value, power=40)
    OE_05 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_05.value, power=40)
    OE_04 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_04.value, power=40)
    OE_03 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_03.value, power=40)

    SIM_UNI_GOLD = GuideMission(cate=GuideCategoryEnum.SU_SIM_UNI.value, sim_uni_type=SimUniTypeEnum.NORMAL.value, power=40, show_in_tp_plan=False)
    SIM_UNI_SWARM = GuideMission(cate=GuideCategoryEnum.SU_SIM_UNI.value, sim_uni_type=SimUniTypeEnum.EXTEND_SWARM.value, power=40, show_in_tp_plan=False)
    SIM_UNI_NORMAL = GuideMission(cate=GuideCategoryEnum.SU_SIM_UNI.value, sim_uni_type=SimUniTypeEnum.EXTEND_GOLD.value, power=40, show_in_tp_plan=False)

    @staticmethod
    def get_by_unique_id(unique_id: str) -> Optional[GuideMission]:
        """
        根据唯一ID获取对应的关卡
        :param unique_id:
        :return:
        """
        for enum in GuideMissionEnum:
            if enum.value.unique_id == unique_id:
                return enum.value
        return None

    @staticmethod
    def get_list_by_category(cate: GuideCategory) -> List[GuideMission]:
        list_of_cate: List[GuideMission] = []
        for enum in GuideMissionEnum:
            if enum.value.cate == cate:
                list_of_cate.append(enum.value)
        return list_of_cate
