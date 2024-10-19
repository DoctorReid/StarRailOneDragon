from typing import List

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig
from one_dragon.utils import yolo_config_utils

_DEFAULT_WORLD_PATROL = 'yolov8n-640-simuni-0601'
_DEFAULT_SIM_UNI = 'yolov8n-640-simuni-0601'


class YoloConfig(YamlConfig):

    def __init__(self):
        YamlConfig.__init__(self, 'yolo', instance_idx=None)

    @property
    def world_patrol(self) -> str:
        return self.get('world_patrol', _DEFAULT_WORLD_PATROL)

    @world_patrol.setter
    def world_patrol(self, new_value: str) -> None:
        self.update('world_patrol', new_value)

    @property
    def sim_uni(self) -> str:
        return self.get('sim_uni', _DEFAULT_SIM_UNI)

    @sim_uni.setter
    def sim_uni(self, new_value: str) -> None:
        self.update('sim_uni', new_value)

    def using_old_model(self) -> bool:
        """
        是否在使用旧模型
        :return:
        """
        return self.world_patrol != _DEFAULT_WORLD_PATROL or self.sim_uni != _DEFAULT_SIM_UNI


def get_world_patrol_opts() -> List[ConfigItem]:
    """
    获取锄大地模型的选项
    :return:
    """
    models_list = yolo_config_utils.get_available_models('world_patrol')
    if _DEFAULT_WORLD_PATROL not in models_list:
        models_list.append(_DEFAULT_WORLD_PATROL)

    return [ConfigItem(i) for i in models_list]


def get_sim_uni_opts() -> List[ConfigItem]:
    """
    获取模拟宇宙模型的选项
    :return:
    """
    models_list = yolo_config_utils.get_available_models('sim_uni')
    if _DEFAULT_SIM_UNI not in models_list:
        models_list.append(_DEFAULT_SIM_UNI)

    return [ConfigItem(i) for i in models_list]
