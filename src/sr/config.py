from typing import List

from basic import config_utils
from basic.log_utils import log


class ConfigHolder:

    def __init__(self, to_load: List = ['game']):
        self.config = {}
        for c in to_load:
            self.config[c] = config_utils.read_config(c)

    def get_config(self, module: str, prop: str = None):
        """
        获取具体配置
        :param module: 配置模块名称
        :param prop: 具体属性名称
        :return: 配置值
        """
        if module not in self.config:
            log.error('未有模块配置 %s', module)
            return None
        if prop is None:
            return self.config[module]
        if prop not in self.config[module]:
            log.error('模块%s中未配置 %s', module, prop)
            return None
        return self.config[module][prop]

    def update_config(self, module: str, prop: str, value: object, save_file: bool = True):
        """
        更新配置值
        :param module: 配置模块名称
        :param prop: 属性名称
        :param value: 值
        :param save_file: 是否保存到文件
        :return:
        """
        mc = self.get_config(module)
        mc[prop] = value
        if save_file:
            config_utils.save_config(module, mc)
