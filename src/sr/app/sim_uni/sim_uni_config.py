import os
import shutil
from typing import List, Optional

from basic import os_utils
from sr.config import ConfigHolder
from sr.sim_uni.sim_uni_const import SimUniWorldEnum

_MAX_WITH_SAMPLE = 8


class SimUniChallengeConfig(ConfigHolder):

    def __init__(self, idx: int):
        super().__init__('%02d' % idx, sub_dir=['sim_uni', 'challenge_config'], sample=idx <= _MAX_WITH_SAMPLE)

        self.idx = idx

    def _init_after_read_file(self):
        pass

    @property
    def uid(self) -> str:
        return '%02d' % self.idx

    @property
    def name(self) -> str:
        return self.get('name', '')

    @name.setter
    def name(self, new_value: str):
        self.update('name', new_value)

    @property
    def path(self) -> str:
        """
        返回命途ID SimUniPath.name
        :return:
        """
        return self.get('path', '')

    @path.setter
    def path(self, new_value: str):
        self.update('path', new_value)

    @property
    def bless_priority(self) -> List[str]:
        """
        祝福优先级
        :return:
        """
        return self.get('bless_priority', [])

    @bless_priority.setter
    def bless_priority(self, new_list: List[str]):
        self.update('bless_priority', new_list)

    @property
    def level_type_priority(self) -> List[str]:
        """
        楼层优先级
        :return:
        """
        return self.get('level_type_priority', [])

    @level_type_priority.setter
    def level_type_priority(self, new_list: List[str]):
        self.update('level_type_priority', new_list)

    @property
    def curio_priority(self) -> List[str]:
        """
        楼层优先级
        :return:
        """
        return self.get('curio_priority', [])

    @curio_priority.setter
    def curio_priority(self, new_list: List[str]):
        self.update('curio_priority', new_list)


def load_all_challenge_config() -> List[SimUniChallengeConfig]:
    config_list = []
    for i in range(1, _MAX_WITH_SAMPLE + 1):  # 有模板的部分
        config_list.append(SimUniChallengeConfig(i))

    base_dir = get_challenge_config_dir()
    for file in os.listdir(base_dir):
        if not file.endswith('.yml'):
            continue

        if file.endswith('_sample.yml'):
            continue

        idx = int(file[:-4])
        if idx <= _MAX_WITH_SAMPLE:
            continue

        config_list.append(SimUniChallengeConfig(idx))

    return config_list


def get_challenge_config_dir() -> str:
    return os_utils.get_path_under_work_dir('config', 'sim_uni', 'challenge_config')


def get_next_id() -> int:
    """
    为新建获取下一个id
    :return:
    """
    base_dir = get_challenge_config_dir()
    idx = _MAX_WITH_SAMPLE + 1  # 获取合法的下标
    while True:
        route_dir = os.path.join(base_dir, '%02d' % idx)
        if os.path.exists(route_dir):
            idx += 1
        else:
            break
    return idx


def create_new_challenge_config(sample_idx: int = 0) -> SimUniChallengeConfig:
    """
    创建一个新的配置
    :return:
    """
    idx = get_next_id()
    base_dir = get_challenge_config_dir()

    from_file = os.path.join(base_dir, '01_sample.yml' if sample_idx == 0 else ('%02d.yml' % sample_idx))
    to_file = os.path.join(base_dir, '%02d.yml' % idx)

    shutil.copy2(from_file, to_file)

    return SimUniChallengeConfig(idx)


class SimUniAppConfig(ConfigHolder):

    def __init__(self):
        super().__init__('app_config', sub_dir=['sim_uni'])

    def get_challenge_config(self, sim_uni_num: int) -> SimUniChallengeConfig:
        """
        获取模拟宇宙对应的挑战配置
        :param sim_uni_num: 第几宇宙
        :return:
        """
        key = 'sim_uni_%02d' % sim_uni_num
        return SimUniChallengeConfig(int(self.get(key, '05')))

    @property
    def weekly_uni_num(self) -> str:
        """
        每周挑战的第几宇宙设置
        :return:
        """
        return self.get('weekly_uni_num', SimUniWorldEnum.WORLD_08.name)

    @weekly_uni_num.setter
    def weekly_uni_num(self, new_value: str):
        self.update('weekly_uni_num', new_value)

    @property
    def weekly_uni_diff(self) -> int:
        """
        每周挑战的宇宙难度设置
        :return:
        """
        return self.get('weekly_uni_diff', 4)

    @weekly_uni_diff.setter
    def weekly_uni_diff(self, new_value: int):
        self.update('weekly_uni_diff', new_value)

    @property
    def weekly_times(self) -> int:
        """
        每周挑战的次数
        :return:
        """
        return self.get('weekly_times', 34)

    @weekly_times.setter
    def weekly_times(self, new_value: int):
        self.update('weekly_times', new_value)

    @property
    def daily_times(self) -> int:
        """
        每天挑战的次数
        :return:
        """
        return self.get('daily_times', 5)

    @daily_times.setter
    def daily_times(self, new_value: int):
        self.update('daily_times', new_value)


_sim_uni_app_config: Optional[SimUniAppConfig] = None


def get_sim_uni_app_config() -> SimUniAppConfig:
    global _sim_uni_app_config
    if _sim_uni_app_config is None:
        _sim_uni_app_config = SimUniAppConfig()
    return _sim_uni_app_config