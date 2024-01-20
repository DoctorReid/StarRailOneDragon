import os
from ctypes import Union
from typing import List, Optional

import yaml

from basic import os_utils


def get_config_file_path(name: str, sub_dir: Optional[List[str]] = None):
    """
    获取配置文件完整路径
    :param name: 配置名
    :param sub_dir: 子目录
    :return: 完整路径
    """
    dir_path = os_utils.get_path_under_work_dir('config')
    if sub_dir is not None:
        dir_path = os_utils.get_path_under_work_dir('config', *sub_dir)
    return os.path.join(dir_path, '%s.yml' % name)


def get_sample_config_file_path(name: str, sub_dir: List[str] = None):
    """
    获取样例配置文件的完整路径
    :param name: 配置名
    :param sub_dir: 子目录
    :return: 完整路径
    """
    return get_config_file_path('%s_sample' % name, sub_dir=sub_dir)


def read_config(name: str, sample: bool = True, sub_dir: List[str] = None):
    """
    读取具体的配置 如果不存在 读取默认配置
    :param name: 配置名
    :param sample: 找不到时是否找同目录下的sample
    :param sub_dir: 子目录
    :return: 配置内容
    """
    path = get_config_file_path(name, sub_dir=sub_dir)
    data = None
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)
    if data is None and sample:
        data = read_sample_config(name, sub_dir=sub_dir)
    return data


def read_sample_config(name: str, sub_dir: List[str] = None):
    """
    读取样例配置
    :param name: 配置名
    :param sub_dir: 子目录
    :return: 配置内容
    """
    path = get_sample_config_file_path(name, sub_dir=sub_dir)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    else:
        return None


def save_config(name: str, data: dict, sub_dir: Optional[List[str]] = None):
    """
    保存配置
    :param name: 配置模块
    :param data: 值
    :param sub_dir: 子目录
    :return:
    """
    path = get_config_file_path(name, sub_dir=sub_dir)
    with open(path, 'w', encoding='utf-8') as file:
        yaml.dump(data, file)


def deep_copy_missing_prop(source: dict, target: dict):
    """
    从一个字典中复制到另一个对象中，只复制缺失的属性
    :param source: 源
    :param target: 目标
    :return:
    """
    for key in source.keys():
        if key not in target:
            target[key] = source[key]
        elif type(source[key]) == dict and type(target[key]) == dict:
            deep_copy_missing_prop(source[key], target[key])


def deep_del_extra_prop(source: dict, target: dict):
    """
    对比目标字典和源字典 删除目标字典多余的属性
    :param source: 源
    :param target: 目标
    :return:
    """
    to_del_keys = []
    for key in target.keys():
        if key not in source:
            to_del_keys.append(key)
        elif type(source[key]) == dict and type(target[key]) == dict:
            deep_del_extra_prop(source[key], target[key])
    for key in to_del_keys:
        del target[key]


def async_sample(name: str, sub_dir: Optional[List[str]] = None) -> dict:
    """
    将样例配置同步到具体配置中
    :param name: 模块名称
    :param sub_dir: 子目录
    :return: 同步后的配置
    """
    sample = read_sample_config(name, sub_dir)
    config = read_config(name, False, sub_dir)
    if config is None:
        config = sample
    else:
        deep_copy_missing_prop(sample, config)
        deep_del_extra_prop(sample, config)

    save_config(name, config, sub_dir=sub_dir)
    return config

