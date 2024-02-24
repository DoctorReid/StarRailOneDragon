from typing import Optional

from basic.config import ConfigHolder
from sr.app.app_description import AppDescriptionEnum
from sr.sim_uni.sim_uni_challenge_config import SimUniChallengeConfig
from sr.sim_uni.sim_uni_const import SimUniWorldEnum


class SimUniConfig(ConfigHolder):

    def __init__(self, account_idx: Optional[int] = None):
        super().__init__(AppDescriptionEnum.SIM_UNIVERSE.value.id, account_idx=account_idx)

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
