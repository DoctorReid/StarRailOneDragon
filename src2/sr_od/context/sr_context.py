from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.utils import i18_utils
from sr_od.app.world_patrol.world_patrol_config import WorldPatrolConfig
from sr_od.config.game_config import GameConfig
from sr_od.world_patrol.world_patrol_map_data import WorldPatrolMapData
from sr_od.world_patrol.world_patrol_route_data import WorldPatrolRouteData


class SrContext(OneDragonContext):

    def __init__(self):
        """
        """
        OneDragonContext.__init__(self)

        self.world_patrol_map_data: WorldPatrolMapData = WorldPatrolMapData()
        self.world_patrol_route_data: WorldPatrolRouteData = WorldPatrolRouteData(self.world_patrol_map_data)

        # 实例独有的配置
        self.load_instance_config()

    def init_by_config(self) -> None:
        """
        根据配置进行初始化
        :return:
        """
        OneDragonContext.init_by_config(self)
        i18_utils.update_default_lang(self.game_config.lang)

    def load_instance_config(self) -> None:
        OneDragonContext.load_instance_config(self)

        self.game_config: GameConfig = GameConfig(self.current_instance_idx)
        self.world_patrol_config: WorldPatrolConfig = WorldPatrolConfig(self.current_instance_idx)
