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


def get_sample_config_file_path(name: str,
                                sub_dir: List[str] = None):
    """
    获取样例配置文件的完整路径
    :param name: 配置名
    :param sub_dir: 子目录
    :return: 完整路径
    """
    return get_config_file_path('%s_sample' % name, sub_dir=sub_dir)


def read_config(name: str,
                script_account_idx: Optional[int] = None,
                sub_dir: List[str] = None) -> Optional[dict]:
    """
    读取具体的配置
    :param name: 配置名
    :param script_account_idx: 脚本账号ID
    :param sub_dir: 子目录
    :return: 配置内容
    """
    sub_dir = get_sub_dir_with_account(script_account_idx, sub_dir)
    path = get_config_file_path(name, sub_dir=sub_dir)
    data: Optional[dict] = None
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

    return data


def get_sub_dir_with_account(
        script_account_idx: Optional[int] = None,
        sub_dir: List[str] = None) -> Optional[List[str]]:
    """
    获取对应的子文件夹目录
    :param script_account_idx: 脚本账号ID
    :param sub_dir: 子目录
    :return:
    """
    if script_account_idx is not None:
        first_dir = '%02d' % script_account_idx
        if sub_dir is None:
            sub_dir = [first_dir]
        else:
            sub_dir = [first_dir] + sub_dir
    return sub_dir


def read_sample_config(name: str,
                       sub_dir: List[str] = None):
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


def save_config(data: dict, name: str,
                script_account_idx: Optional[int] = None,
                sub_dir: Optional[List[str]] = None):
    """
    保存配置
    :param data: 值
    :param name: 配置模块
    :param script_account_idx: 脚本账号ID
    :param sub_dir: 子目录
    :return:
    """
    sub_dir = get_sub_dir_with_account(script_account_idx, sub_dir)
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


def read_config_with_sample(name: str,
                            script_account_idx: Optional[int] = None,
                            sub_dir: Optional[List[str]] = None) -> dict:
    """
    读取配置 并将样例配置同步到具体配置中
    :param name: 模块名称
    :param script_account_idx: 脚本账号ID
    :param sub_dir: 子目录
    :return: 同步后的配置
    """
    sample = read_sample_config(name, sub_dir)
    config = read_config(name, script_account_idx, sub_dir)
    if config is None:
        config = sample
    else:
        deep_copy_missing_prop(sample, config)
        deep_del_extra_prop(sample, config)

    save_config(config, name, script_account_idx=script_account_idx, sub_dir=sub_dir)
    return config

