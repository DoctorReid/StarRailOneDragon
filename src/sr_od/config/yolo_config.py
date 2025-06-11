import os
from typing import List

from one_dragon.base.config.config_item import ConfigItem
from one_dragon.base.config.yaml_config import YamlConfig
from one_dragon.base.matcher.ocr.onnx_ocr_matcher import DEFAULT_OCR_MODEL_NAME, get_ocr_model_dir, \
    get_ocr_download_url_github, get_ocr_download_url_gitee, get_final_file_list
from one_dragon.base.web.common_downloader import CommonDownloaderParam
from one_dragon_qt.widgets.setting_card.yaml_config_adapter import YamlConfigAdapter
from one_dragon.utils import yolo_config_utils

_GITHUB_MODEL_DOWNLOAD_URL = 'https://github.com/OneDragon-Anything/OneDragon-YOLO/releases/download/sr_model'
_GITEE_MODEL_DOWNLOAD_URL = 'https://gitee.com/OneDragon-Anything/OneDragon-YOLO/releases/download/sr_model'

_DEFAULT_WORLD_PATROL = 'yolov8n-640-simuni-0601'
_BACKUP_WORLD_PATROL = 'yolov8n-640-simuni-0601'

_DEFAULT_SIM_UNI = 'yolov8n-640-simuni-0601'
_BACKUP_SIM_UNI = 'yolov8n-640-simuni-0601'


class YoloConfig(YamlConfig):

    def __init__(self):
        YamlConfig.__init__(self, 'yolo', instance_idx=None)

    @property
    def ocr(self) -> str:
        return self.get('ocr', DEFAULT_OCR_MODEL_NAME)

    @ocr.setter
    def ocr(self, new_value: str) -> None:
        self.update('ocr', new_value)

    @property
    def ocr_gpu(self) -> bool:
        return self.get('ocr_gpu', False)

    @ocr_gpu.setter
    def ocr_gpu(self, new_value: bool) -> None:
        self.update('ocr_gpu', new_value)

    @property
    def world_patrol(self) -> str:
        """
        锄大地模型 只允许使用最新的两个模型
        :return:
        """
        current = self.get('world_patrol', _DEFAULT_WORLD_PATROL)
        if current != _DEFAULT_WORLD_PATROL and current != _BACKUP_WORLD_PATROL:
            current = _DEFAULT_WORLD_PATROL
            self.world_patrol = _DEFAULT_WORLD_PATROL
        return current

    @world_patrol.setter
    def world_patrol(self, new_value: str) -> None:
        self.update('world_patrol', new_value)

    @property
    def world_patrol_backup(self) -> str:
        return _BACKUP_WORLD_PATROL

    @property
    def world_patrol_gpu(self) -> bool:
        return self.get('world_patrol_gpu', True)

    @world_patrol_gpu.setter
    def world_patrol_gpu(self, new_value: bool) -> None:
        self.update('world_patrol_gpu', new_value)

    @property
    def world_patrol_gpu_adapter(self) -> YamlConfigAdapter:
        return YamlConfigAdapter(self, 'world_patrol_gpu', True)

    @property
    def sim_uni(self) -> str:
        """
        模拟宇宙模型 只允许使用最新的两个模型
        :return:
        """
        current = self.get('sim_uni', _DEFAULT_SIM_UNI)
        if current != _DEFAULT_SIM_UNI and current != _BACKUP_SIM_UNI:
            current = _DEFAULT_SIM_UNI
            self.sim_uni = _DEFAULT_SIM_UNI
        return current

    @sim_uni.setter
    def sim_uni(self, new_value: str) -> None:
        self.update('sim_uni', new_value)

    @property
    def sim_uni_backup(self) -> str:
        return _BACKUP_SIM_UNI

    @property
    def sim_uni_gpu(self) -> bool:
        return self.get('sim_uni_gpu', True)

    @sim_uni_gpu.setter
    def sim_uni_gpu(self, new_value: bool) -> None:
        self.update('sim_uni_gpu', new_value)

    @property
    def sim_uni_gpu_adapter(self) -> YamlConfigAdapter:
        return YamlConfigAdapter(self, 'sim_uni_gpu', True)

    def using_old_model(self) -> bool:
        """
        是否在使用旧模型
        :return:
        """
        return (self.world_patrol != _DEFAULT_WORLD_PATROL
                or self.sim_uni != _DEFAULT_SIM_UNI
                )


def get_ocr_opts() -> list[ConfigItem]:
    models_list = [DEFAULT_OCR_MODEL_NAME]
    config_list: list[ConfigItem] = []
    for model in models_list:
        model_dir = get_ocr_model_dir(model)
        zip_file_name: str = f'{model}.zip'
        param = CommonDownloaderParam(
            save_file_path=model_dir,
            save_file_name=zip_file_name,
            github_release_download_url=get_ocr_download_url_github(model),
            gitee_release_download_url=get_ocr_download_url_gitee(model),
            check_existed_list=get_final_file_list(model),
        )
        config_list.append(
            ConfigItem(
                label=model,
                value=param,
            )
        )

    return config_list


def get_world_patrol_opts() -> List[ConfigItem]:
    """
    获取锄大地模型的选项
    :return:
    """
    models_list = yolo_config_utils.get_available_models('world_patrol')
    if _DEFAULT_WORLD_PATROL not in models_list:
        models_list.append(_DEFAULT_WORLD_PATROL)

    config_list: list[ConfigItem] = []
    for model in models_list:
        model_dir = yolo_config_utils.get_model_dir('world_patrol', model)
        zip_file_name: str = f'{model}.zip'
        param = CommonDownloaderParam(
            save_file_path=model_dir,
            save_file_name=zip_file_name,
            github_release_download_url=f'{_GITHUB_MODEL_DOWNLOAD_URL}/{zip_file_name}',
            gitee_release_download_url=f'{_GITEE_MODEL_DOWNLOAD_URL}/{zip_file_name}',
            check_existed_list=[
                os.path.join(model_dir, 'model.onnx'),
                os.path.join(model_dir, 'labels.csv'),
            ],
        )
        config_list.append(
            ConfigItem(
                label=model,
                value=param,
            )
        )

    return config_list


def get_sim_uni_opts() -> List[ConfigItem]:
    """
    获取模拟宇宙模型的选项
    :return:
    """
    models_list = yolo_config_utils.get_available_models('sim_uni')
    if _DEFAULT_SIM_UNI not in models_list:
        models_list.append(_DEFAULT_SIM_UNI)

    config_list: list[ConfigItem] = []
    for model in models_list:
        model_dir = yolo_config_utils.get_model_dir('sim_uni', model)
        zip_file_name: str = f'{model}.zip'
        param = CommonDownloaderParam(
            save_file_path=model_dir,
            save_file_name=zip_file_name,
            github_release_download_url=f'{_GITHUB_MODEL_DOWNLOAD_URL}/{zip_file_name}',
            gitee_release_download_url=f'{_GITEE_MODEL_DOWNLOAD_URL}/{zip_file_name}',
            check_existed_list=[
                os.path.join(model_dir, 'model.onnx'),
                os.path.join(model_dir, 'labels.csv'),
            ],
        )
        config_list.append(
            ConfigItem(
                label=model,
                value=param,
            )
        )

    return config_list
