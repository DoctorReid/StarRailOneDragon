from enum import Enum
from typing import Optional, Union, List

from sr.const import map_const
from sr.const.map_const import TransportPoint

from sr.image.sceenshot.screen_state import ScreenState
from sr.screen_area import ScreenArea
from sr.screen_area.interastral_peace_guide import ScreenGuide
from sr.sim_uni.sim_uni_const import SimUniWorld, SimUniWorldEnum


class SurvivalIndexCategory:

    def __init__(self, tab: ScreenState, cn: str, ui_cn: Optional[str] = None):
        """
        生存索引左侧的类目
        """
        self.tab: ScreenState = tab
        """指南上的TAB"""

        self.cn: str = cn
        """中文"""

        self.ui_cn: str = cn if ui_cn is None else ui_cn
        """界面展示的中文"""


class SurvivalIndexCategoryEnum(Enum):

    BUD_1 = SurvivalIndexCategory(tab=ScreenState.GUIDE_SURVIVAL_INDEX, cn='拟造花萼（金）', ui_cn='经验信用')
    BUD_2 = SurvivalIndexCategory(tab=ScreenState.GUIDE_SURVIVAL_INDEX, cn='拟造花萼（赤）',  ui_cn='光锥行迹')
    SHAPE = SurvivalIndexCategory(tab=ScreenState.GUIDE_SURVIVAL_INDEX, cn='凝滞虚影',  ui_cn='角色突破')
    PATH = SurvivalIndexCategory(tab=ScreenState.GUIDE_SURVIVAL_INDEX, cn='侵蚀虫洞',  ui_cn='遗器')
    ECHO_OF_WAR = SurvivalIndexCategory(tab=ScreenState.GUIDE_SURVIVAL_INDEX, cn='历战余响')
    SIM_UNI = SurvivalIndexCategory(tab=ScreenState.GUIDE_SURVIVAL_INDEX, cn='模拟宇宙')

    @staticmethod
    def get_by_ui_cn(ui_cn: str) -> Optional[SurvivalIndexCategory]:
        for enum in SurvivalIndexCategoryEnum:
            if enum.value.ui_cn == ui_cn:
                return enum.value
        return None


class SurvivalIndexSubCategory:

    def __init__(self, cate: SurvivalIndexCategory, area: ScreenArea):
        """
        生存索引二级分类
        """
        self.cate: SurvivalIndexCategory = cate
        self.area: ScreenArea = area


class SurvivalIndexSubCategoryEnum(Enum):

    BUD_1_YYL = SurvivalIndexSubCategory(SurvivalIndexCategoryEnum.BUD_1.value, ScreenGuide.BUD_1_SUB_CATE_1.value)
    BUD_1_XZLF = SurvivalIndexSubCategory(SurvivalIndexCategoryEnum.BUD_1.value, ScreenGuide.BUD_1_SUB_CATE_2.value)
    BUD_1_PNKN = SurvivalIndexSubCategory(SurvivalIndexCategoryEnum.BUD_1.value, ScreenGuide.BUD_1_SUB_CATE_3.value)


class SurvivalIndexMission:

    def __init__(self, cate: SurvivalIndexCategory,
                 tp: Union[TransportPoint, SimUniWorld],
                 power: int,
                 sub_cate: Optional[SurvivalIndexSubCategory] = None):
        self.cate: SurvivalIndexCategory = cate
        self.sub_cate: Optional[SurvivalIndexSubCategory] = sub_cate
        self.tp: Union[TransportPoint, SimUniWorld] = tp
        self.power: int = power

    @property
    def survival_index_cn(self) -> str:
        """
        在生存索引中显示的中文名称
        :return:
        """
        if self.sub_cate is not None:
            return self.tp.cn[:4] + '·' + self.sub_cate.area.text
        else:
            return self.tp.cn

    @property
    def ui_cn(self) -> str:
        """
        在UI上显示的简短名称
        :return:
        """
        if self.cate == SurvivalIndexCategoryEnum.BUD_1.value:
            if self.tp in [map_const.P02_R02_SP04, map_const.P03_R06_SP07, map_const.P04_R03_SP06]:
                prefix = '角色经验'
            elif self.tp in [map_const.P02_R03_SP06, map_const.P03_R02_SP09, map_const.P04_R04_SP04]:
                prefix = '光锥经验'
            elif self.tp in [map_const.P02_R10_SP08, map_const.P03_R07_SP08, map_const.P04_R05_SP10]:
                prefix = '信用点'
            else:
                prefix = ''
            return prefix + '·' + self.sub_cate.area.text
        elif self.cate == SurvivalIndexCategoryEnum.BUD_2.value:
            return self.tp.cn[:2] + '·' + self.tp.region.cn
        elif self.cate == SurvivalIndexCategoryEnum.SHAPE.value:
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
        elif self.cate == SurvivalIndexCategoryEnum.PATH.value:
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
        elif self.cate == SurvivalIndexCategoryEnum.SIM_UNI.value:
            return self.tp.name
        elif self.cate == SurvivalIndexCategoryEnum.ECHO_OF_WAR.value:
            return self.tp.cn[:-5]  # 去除 '·历战余响'
        else:
            return ''

    @property
    def unique_id(self) -> str:
        return self.tp.unique_id


class SurvivalIndexMissionEnum(Enum):

    BUD_1_YLL_1 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_1.value, tp=map_const.P02_R02_SP04, sub_cate=SurvivalIndexSubCategoryEnum.BUD_1_YYL.value, power=10)
    BUD_1_YLL_2 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_1.value, tp=map_const.P02_R03_SP06, sub_cate=SurvivalIndexSubCategoryEnum.BUD_1_YYL.value, power=10)
    BUD_1_YLL_3 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_1.value, tp=map_const.P02_R10_SP08, sub_cate=SurvivalIndexSubCategoryEnum.BUD_1_YYL.value, power=10)

    BUG_1_XZLF_1 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_1.value, tp=map_const.P03_R06_SP07, sub_cate=SurvivalIndexSubCategoryEnum.BUD_1_XZLF.value, power=10)
    BUG_1_XZLF_2 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_1.value, tp=map_const.P03_R02_SP09, sub_cate=SurvivalIndexSubCategoryEnum.BUD_1_XZLF.value, power=10)
    BUG_1_XZLF_3 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_1.value, tp=map_const.P03_R07_SP08, sub_cate=SurvivalIndexSubCategoryEnum.BUD_1_XZLF.value, power=10)

    BUD_1_PNKN_1 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_1.value, tp=map_const.P04_R03_SP06, sub_cate=SurvivalIndexSubCategoryEnum.BUD_1_PNKN.value, power=10)
    BUD_1_PNKN_2 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_1.value, tp=map_const.P04_R04_SP04, sub_cate=SurvivalIndexSubCategoryEnum.BUD_1_PNKN.value, power=10)
    BUD_1_PNKN_3 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_1.value, tp=map_const.P04_R05_SP10, sub_cate=SurvivalIndexSubCategoryEnum.BUD_1_PNKN.value, power=10)

    BUD_2_HM_1 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_2.value, tp=map_const.P01_R03_SP05, power=10)
    BUD_2_HM_2 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_2.value, tp=map_const.P03_R09_SP07, power=10)

    BUD_2_CH_1 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_2.value, tp=map_const.P01_R04_SP04, power=10)
    BUD_2_CH_2 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_2.value, tp=map_const.P04_R07_SP07, power=10)

    BUD_2_XL_1 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_2.value, tp=map_const.P02_R02_SP03, power=10)

    BUD_2_FR_1 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_2.value, tp=map_const.P02_R03_SP05, power=10)
    BUD_2_FR_2 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_2.value, tp=map_const.P03_R10_SP17, power=10)

    BUD_2_ZS_1 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_2.value, tp=map_const.P02_R11_SP05, power=10)

    BUD_2_TX_1 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_2.value, tp=map_const.P02_R12_SP04, power=10)
    BUD_2_TX_2 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_2.value, tp=map_const.P04_R05_SP09, power=10)

    BUD_2_XW_1 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_2.value, tp=map_const.P02_R10_SP07, power=10)
    BUD_2_XW_2 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.BUD_2.value, tp=map_const.P03_R08_SP13, power=10)

    SHAPE_01 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P02_R11_SP04, power=30)
    SHAPE_02 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P02_R05_SP05, power=30)
    SHAPE_03 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P02_R04_SP04, power=30)
    SHAPE_04 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P02_R10_SP05, power=30)
    SHAPE_05 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P02_R05_SP06, power=30)
    SHAPE_06 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P02_R03_SP04, power=30)
    SHAPE_07 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P03_R02_SP05, power=30)
    SHAPE_08 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P03_R03_SP05, power=30)
    SHAPE_09 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P03_R07_SP05, power=30)
    SHAPE_10 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P02_R10_SP06, power=30)
    SHAPE_11 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P03_R08_SP05, power=30)
    SHAPE_12 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P01_R02_SP03, power=30)
    SHAPE_13 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P03_R09_SP04, power=30)
    SHAPE_14 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P03_R10_SP05, power=30)
    SHAPE_15 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P04_R05_SP08, power=30)
    SHAPE_16 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P04_R03_SP05, power=30)
    SHAPE_17 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P04_R06_SUB_01_SP02, power=30)
    SHAPE_18 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SHAPE.value, tp=map_const.P04_R07_SP13, power=30)

    PATH_01 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.PATH.value, tp=map_const.P02_R04_SP05, power=40)
    PATH_02 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.PATH.value, tp=map_const.P02_R05_SP07, power=40)
    PATH_03 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.PATH.value, tp=map_const.P02_R06_SP03, power=40)
    PATH_04 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.PATH.value, tp=map_const.P03_R02_SP06, power=40)
    PATH_05 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.PATH.value, tp=map_const.P03_R03_SP06, power=40)
    PATH_06 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.PATH.value, tp=map_const.P03_R08_SP06, power=40)
    PATH_07 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.PATH.value, tp=map_const.P03_R10_SP06, power=40)
    PATH_08 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.PATH.value, tp=map_const.P01_R03_SP06, power=40)
    PATH_09 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.PATH.value, tp=map_const.P04_R05_SP11, power=40)

    ECHO_01 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.ECHO_OF_WAR.value, tp=map_const.P01_R04_SP06, power=30)
    ECHO_02 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.ECHO_OF_WAR.value, tp=map_const.P02_R06_SP05, power=30)
    ECHO_03 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.ECHO_OF_WAR.value, tp=map_const.P03_R09_SP06, power=30)
    ECHO_04 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.ECHO_OF_WAR.value, tp=map_const.P01_R05_SP07, power=30)

    SIM_UNI_03 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SIM_UNI.value, tp=SimUniWorldEnum.WORLD_03.value, power=40)
    SIM_UNI_04 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SIM_UNI.value, tp=SimUniWorldEnum.WORLD_04.value, power=40)
    SIM_UNI_05 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SIM_UNI.value, tp=SimUniWorldEnum.WORLD_05.value, power=40)
    SIM_UNI_06 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SIM_UNI.value, tp=SimUniWorldEnum.WORLD_06.value, power=40)
    SIM_UNI_07 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SIM_UNI.value, tp=SimUniWorldEnum.WORLD_07.value, power=40)
    SIM_UNI_08 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SIM_UNI.value, tp=SimUniWorldEnum.WORLD_08.value, power=40)
    SIM_UNI_09 = SurvivalIndexMission(cate=SurvivalIndexCategoryEnum.SIM_UNI.value, tp=SimUniWorldEnum.WORLD_09.value, power=40)

    @staticmethod
    def get_by_unique_id(unique_id: str) -> Optional[SurvivalIndexMission]:
        """
        根据唯一ID获取对应的关卡
        :param unique_id:
        :return:
        """
        for enum in SurvivalIndexMissionEnum:
            if enum.value.unique_id == unique_id:
                return enum.value
        return None

    @staticmethod
    def get_list_by_category(cate: SurvivalIndexCategory) -> List[SurvivalIndexMission]:
        list_of_cate: List[SurvivalIndexMission] = []
        for enum in SurvivalIndexMissionEnum:
            if enum.value.cate == cate:
                list_of_cate.append(enum.value)
        return list_of_cate
