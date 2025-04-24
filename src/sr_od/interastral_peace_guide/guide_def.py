from typing import Optional


class GuideTab:

    def __init__(self, cn: str):
        """
        打开指南后 上方的TAB
        """
        self.cn: str = cn  # 左上角显示的名字

    @property
    def unique_id(self) -> str:
        return self.cn


class GuideCategory:

    def __init__(self, tab: GuideTab, cn: str, ui_cn: Optional[str] = None,
                 show_in_power_plan: bool = False,
                 remark_in_game: Optional[str] = None):
        """
        打开指南页后 左侧显示的分类
        """

        self.tab: GuideTab = tab  # 指南上的TAB

        self.cn: str = cn  # 中文

        self.ui_cn: str = cn if ui_cn is None else ui_cn  # 界面展示的中文

        self.show_in_power_plan: bool = show_in_power_plan  # 是否在体力计划中显示

        self.remark_in_game: str = remark_in_game  # 游戏中 名称下方的备注

    @property
    def unique_id(self) -> str:
        return '%s %s' % (self.tab.cn, self.cn)


class GuideMission:

    def __init__(self, cate: GuideCategory,
                 mission_name: str,
                 power: int,
                 display_name: str = None,
                 region_name: str = None,
                 show_in_power_plan: bool = False,
                 ):
        """
        打开指南页面后 右侧显示的具体关卡
        """

        self.cate: GuideCategory = cate  # 指南页面的左侧分类

        self.power: int = power  # 挑战一次需要的开拓力

        self.mission_name: str = mission_name  # 副本名字

        self.region_name: str = region_name  # 区域名称

        self.display_name: str = mission_name if display_name is None else display_name  # 界面显示的中文

        self.show_in_power_plan: bool = show_in_power_plan  # 是否在开拓力计划中显示

    @property
    def unique_id(self) -> str:
        return '%s %s %s' % (self.cate.unique_id, self.mission_name, self.region_name)



# class GuideMissionEnum(Enum):
#
#     BUD_1_YLL_1 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P02_R02_SP04, sub_cate=GuideSubCategoryEnum.BUD_1_YYL.value, power=10)
#     BUD_1_YLL_2 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P02_R03_SP06, sub_cate=GuideSubCategoryEnum.BUD_1_YYL.value, power=10)
#     BUD_1_YLL_3 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P02_R10_SP08, sub_cate=GuideSubCategoryEnum.BUD_1_YYL.value, power=10)
#
#     BUG_1_XZLF_1 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P03_R06_SP07, sub_cate=GuideSubCategoryEnum.BUD_1_XZLF.value, power=10)
#     BUG_1_XZLF_2 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P03_R02_SP09, sub_cate=GuideSubCategoryEnum.BUD_1_XZLF.value, power=10)
#     BUG_1_XZLF_3 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P03_R07_SP08, sub_cate=GuideSubCategoryEnum.BUD_1_XZLF.value, power=10)
#
#     BUD_1_PNKN_1 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P04_R03_SP06, sub_cate=GuideSubCategoryEnum.BUD_1_PNKN.value, power=10)
#     BUD_1_PNKN_2 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P04_R04_SP04, sub_cate=GuideSubCategoryEnum.BUD_1_PNKN.value, power=10)
#     BUD_1_PNKN_3 = GuideMission(cate=GuideCategoryEnum.BUD_1.value, tp=map_const.P04_R05_SP10, sub_cate=GuideSubCategoryEnum.BUD_1_PNKN.value, power=10)
#
#     BUD_2_HM_1 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P01_R03_SP05, power=10)
#     BUD_2_HM_2 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P03_R09_SP07, power=10)
#
#     BUD_2_CH_1 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P01_R04_SP04, power=10)
#     BUD_2_CH_2 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P04_R07_SP07, power=10)
#
#     BUD_2_XL_1 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P02_R02_SP03, power=10)
#     BUD_2_XL_2 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P04_R09_SP03, power=10)
#
#     BUD_2_FR_1 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P02_R03_SP05, power=10)
#     BUD_2_FR_2 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P03_R10_SP17, power=10)
#
#     BUD_2_ZS_1 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P02_R11_SP05, power=10)
#     BUD_2_ZS_2 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P04_R10_SP09, power=10)
#
#     BUD_2_TX_1 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P02_R12_SP04, power=10)
#     BUD_2_TX_2 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P04_R05_SP09, power=10)
#
#     BUD_2_XW_1 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P02_R10_SP07, power=10)
#     BUD_2_XW_2 = GuideMission(cate=GuideCategoryEnum.BUD_2.value, tp=map_const.P03_R08_SP13, power=10)
#
#     SHAPE_01 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P02_R11_SP04, power=30)
#     SHAPE_02 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P02_R05_SP05, power=30)
#     SHAPE_03 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P02_R04_SP04, power=30)
#     SHAPE_04 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P02_R10_SP05, power=30)
#     SHAPE_05 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P02_R05_SP06, power=30)
#     SHAPE_06 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P02_R03_SP04, power=30)
#     SHAPE_07 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P03_R02_SP05, power=30)
#     SHAPE_08 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P03_R03_SP05, power=30)
#     SHAPE_09 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P03_R07_SP05, power=30)
#     SHAPE_10 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P02_R10_SP06, power=30)
#     SHAPE_11 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P03_R08_SP05, power=30)
#     SHAPE_12 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P01_R02_SP03, power=30)
#     SHAPE_13 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P03_R09_SP04, power=30)
#     SHAPE_14 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P03_R10_SP05, power=30)
#     SHAPE_15 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P04_R05_SP08, power=30)
#     SHAPE_16 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P04_R03_SP05, power=30)
#     SHAPE_17 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P04_R06_SUB_01_SP02, power=30)
#     SHAPE_18 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P04_R07_SP13, power=30)
#     SHAPE_19 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P03_R11_SP12, power=30)
#     SHAPE_20 = GuideMission(cate=GuideCategoryEnum.SHAPE.value, tp=map_const.P04_R10_SP11, power=30)
#
#     PATH_01 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P02_R04_SP05, power=40)
#     PATH_02 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P02_R05_SP07, power=40)
#     PATH_03 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P02_R06_SP03, power=40)
#     PATH_04 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P03_R02_SP06, power=40)
#     PATH_05 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P03_R03_SP06, power=40)
#     PATH_06 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P03_R08_SP06, power=40)
#     PATH_07 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P03_R10_SP06, power=40)
#     PATH_08 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P01_R03_SP06, power=40)
#     PATH_09 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P04_R05_SP11, power=40)
#     PATH_10 = GuideMission(cate=GuideCategoryEnum.PATH.value, tp=map_const.P04_R10_SP10, power=40)
#
#     ECHO_01 = GuideMission(cate=GuideCategoryEnum.ECHO_OF_WAR.value, tp=map_const.P01_R04_SP06, power=30)
#     ECHO_02 = GuideMission(cate=GuideCategoryEnum.ECHO_OF_WAR.value, tp=map_const.P02_R06_SP05, power=30)
#     ECHO_03 = GuideMission(cate=GuideCategoryEnum.ECHO_OF_WAR.value, tp=map_const.P03_R09_SP06, power=30)
#     ECHO_04 = GuideMission(cate=GuideCategoryEnum.ECHO_OF_WAR.value, tp=map_const.P01_R05_SP07, power=30)
#     ECHO_05 = GuideMission(cate=GuideCategoryEnum.ECHO_OF_WAR.value, tp=map_const.P04_R10_SP08, power=30)
#     ECHO_06 = GuideMission(cate=GuideCategoryEnum.ECHO_OF_WAR.value, tp=map_const.P03_R12_SP15, power=30)
#
#     SIM_UNI_00 = GuideMission(cate=GuideCategoryEnum.SI_SIM_UNI.value, sim_world=SimUniWorldEnum.WORLD_00.value, power=40, show_in_tp_plan=False)
#     SIM_UNI_03 = GuideMission(cate=GuideCategoryEnum.SI_SIM_UNI.value, sim_world=SimUniWorldEnum.WORLD_03.value, power=40)
#     SIM_UNI_04 = GuideMission(cate=GuideCategoryEnum.SI_SIM_UNI.value, sim_world=SimUniWorldEnum.WORLD_04.value, power=40)
#     SIM_UNI_05 = GuideMission(cate=GuideCategoryEnum.SI_SIM_UNI.value, sim_world=SimUniWorldEnum.WORLD_05.value, power=40)
#     SIM_UNI_06 = GuideMission(cate=GuideCategoryEnum.SI_SIM_UNI.value, sim_world=SimUniWorldEnum.WORLD_06.value, power=40)
#     SIM_UNI_07 = GuideMission(cate=GuideCategoryEnum.SI_SIM_UNI.value, sim_world=SimUniWorldEnum.WORLD_07.value, power=40)
#     SIM_UNI_08 = GuideMission(cate=GuideCategoryEnum.SI_SIM_UNI.value, sim_world=SimUniWorldEnum.WORLD_08.value, power=40)
#     SIM_UNI_09 = GuideMission(cate=GuideCategoryEnum.SI_SIM_UNI.value, sim_world=SimUniWorldEnum.WORLD_09.value, power=40)
#
#     OE_11 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_11.value, power=40)
#     OE_10 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_10.value, power=40)
#     OE_09 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_09.value, power=40)
#     OE_08 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_08.value, power=40)
#     OE_07 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_07.value, power=40)
#     OE_06 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_06.value, power=40)
#     OE_05 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_05.value, power=40)
#     OE_04 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_04.value, power=40)
#     OE_03 = GuideMission(cate=GuideCategoryEnum.ORNAMENT_EXTRACTION.value, ornament_extraction=OrnamentExtractionEnum.OE_03.value, power=40)
#
#     SIM_UNI_NORMAL = GuideMission(cate=GuideCategoryEnum.SU_SIM_UNI.value, sim_uni_type=SimUniTypeEnum.NORMAL.value, power=40, show_in_tp_plan=False)
#     SIM_UNI_SWARM = GuideMission(cate=GuideCategoryEnum.SU_SIM_UNI.value, sim_uni_type=SimUniTypeEnum.EXTEND_SWARM.value, power=40, show_in_tp_plan=False)
#     SIM_UNI_GOLD = GuideMission(cate=GuideCategoryEnum.SU_SIM_UNI.value, sim_uni_type=SimUniTypeEnum.EXTEND_GOLD.value, power=40, show_in_tp_plan=False)
#
#     @staticmethod
#     def get_by_unique_id(unique_id: str) -> Optional[GuideMission]:
#         """
#         根据唯一ID获取对应的关卡
#         :param unique_id:
#         :return:
#         """
#         for enum in GuideMissionEnum:
#             if enum.value.unique_id == unique_id:
#                 return enum.value
#         return None
#
#     @staticmethod
#     def get_list_by_category(cate: GuideCategory) -> List[GuideMission]:
#         list_of_cate: List[GuideMission] = []
#         for enum in GuideMissionEnum:
#             if enum.value.cate == cate:
#                 list_of_cate.append(enum.value)
#         return list_of_cate
