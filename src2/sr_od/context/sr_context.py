from typing import Optional, List

from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.utils import i18_utils
from sr_od.app.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig
from sr_od.app.sim_uni.sim_uni_config import SimUniConfig
from sr_od.app.world_patrol.world_patrol_config import WorldPatrolConfig
from sr_od.app.world_patrol.world_patrol_route_data import WorldPatrolRouteData
from sr_od.app.world_patrol.world_patrol_run_record import WorldPatrolRunRecord
from sr_od.config.character_const import Character, TECHNIQUE_ATTACK, TECHNIQUE_BUFF, TECHNIQUE_BUFF_ATTACK
from sr_od.config.game_config import GameConfig
from sr_od.config.yolo_config import YoloConfig
from sr_od.context.context_pos_info import ContextPosInfo
from sr_od.context.preheat_context import SrPreheatContext
from sr_od.context.sr_pc_controller import SrPcController
from sr_od.screen_state.yolo_screen_detector import YoloScreenDetector
from sr_od.sr_map.sr_map_data import SrMapData


class TeamInfo:

    def __init__(self,
                 character_list: Optional[List[Character]] = None,
                 current_active: int = 0):
        """
        当前组队信息
        """
        self.character_list: List[Character] = character_list
        self.current_active: int = current_active  # 当前使用的是第几个角色

    @property
    def is_attack_technique(self) -> bool:
        """
        当前角色使用的秘技是否buff类型
        :return:
        """
        if self.character_list is None or len(self.character_list) == 0:
            return False
        if self.current_active < 0 or self.current_active >= len(self.character_list):
            return False
        if self.character_list[self.current_active] is None:
            return False
        return self.character_list[self.current_active].technique_type in [TECHNIQUE_ATTACK]

    @property
    def is_buff_technique(self) -> bool:
        """
        当前角色使用的秘技是否buff类型
        :return:
        """
        if self.character_list is None or len(self.character_list) == 0:
            return False
        if self.current_active < 0 or self.current_active >= len(self.character_list):
            return False
        if self.character_list[self.current_active] is None:
            return False
        return self.character_list[self.current_active].technique_type in [TECHNIQUE_BUFF, TECHNIQUE_BUFF_ATTACK]

    def update_character_list(self, new_character_list: List[Character]):
        self.character_list = new_character_list

    def same_as_current(self, new_character_list: List[Character]):
        """
        是否跟当前配队一致
        :param new_character_list:
        :return:
        """
        if self.character_list is None and new_character_list is None:
            return True
        elif self.character_list is None:
            return False
        elif new_character_list is None:
            return False
        elif self.character_list is not None and len(self.character_list) != len(new_character_list):
            return False
        else:
            for i in range(len(self.character_list)):
                if self.character_list[i] is None and new_character_list[i] is None:
                    return True
                elif self.character_list[i] is None or new_character_list[i] is None:
                    return False
                elif self.character_list[i].id != new_character_list[i].id:
                    return False
            return True


class SimUniInfo:

    def __init__(self):
        """
        模拟宇宙信息
        """
        self.world_num: int = 0  # 当前第几世界


class DetectInfo:

    def __init__(self):
        """
        用于目标检测的一些信息
        """
        self.view_down: bool = False  # 当前视角是否已经下移 形成俯视角度


class SrContext(OneDragonContext):

    def __init__(self):
        """
        """
        OneDragonContext.__init__(self)

        self.controller: Optional[SrPcController] = None
        self.is_pc: bool = True
        self.record_coordinate: bool = False  # 记录坐标

        self.map_data: SrMapData = SrMapData()
        self.world_patrol_route_data: WorldPatrolRouteData = WorldPatrolRouteData(self.map_data)

        self.pos_info: ContextPosInfo = ContextPosInfo()
        self.team_info: TeamInfo = TeamInfo()
        self.sim_uni_info = SimUniInfo()
        self.detect_info: DetectInfo = DetectInfo()
        self.yolo_detector: Optional[YoloScreenDetector] = None

        # 秘技相关
        self.technique_used: bool = False  # 新一轮战斗前是否已经使用秘技了
        self.no_technique_recover_consumables: bool = False  # 没有恢复秘技的物品了 为True的时候就不使用秘技了
        self.consumable_used: bool = False  # 是否已经使用过消耗品了

        # 共用配置
        self.yolo_config: YoloConfig = YoloConfig()
        self.yolo_detector = YoloScreenDetector(
            world_patrol_model_name=self.yolo_config.world_patrol,
            sim_uni_model_name=self.yolo_config.sim_uni,
            standard_resolution_h=self.project_config.screen_standard_height,
            standard_resolution_w=self.project_config.screen_standard_width
        )
        self.preheat_context = SrPreheatContext(self)

        # 实例独有的配置
        self.load_instance_config()

    def init_by_config(self) -> None:
        """
        根据配置进行初始化
        :return:
        """
        OneDragonContext.init_by_config(self)
        i18_utils.update_default_lang(self.game_config.lang)

        self.controller = SrPcController(
            game_config=self.game_config,
            win_title=self.game_config.win_title,
            standard_width=self.project_config.screen_standard_width,
            standard_height=self.project_config.screen_standard_height
        )

    def load_instance_config(self) -> None:
        OneDragonContext.load_instance_config(self)

        self.game_config: GameConfig = GameConfig(self.current_instance_idx)

        self.world_patrol_config: WorldPatrolConfig = WorldPatrolConfig(self.current_instance_idx)
        self.world_patrol_record: WorldPatrolRunRecord = WorldPatrolRunRecord(self.current_instance_idx)

        self.sim_uni_config: SimUniConfig = SimUniConfig(self.current_instance_idx)

    @property
    def sim_uni_challenge_config(self) -> Optional[SimUniChallengeConfig]:
        if self.sim_uni_info.world_num == 0 or self.sim_uni_config is None:
            return None
        else:
            return self.sim_uni_config.get_challenge_config(self.sim_uni_info.world_num)

    def init_for_world_patrol(self) -> None:
        self.ocr.init_model()
        self.preheat_context.preheat_for_world_patrol_async()
        self.yolo_detector.init_world_patrol_model(self.yolo_config.world_patrol)

    def init_for_sim_uni(self) -> None:
        self.yolo_detector.init_sim_uni_model(self.yolo_config.sim_uni)
