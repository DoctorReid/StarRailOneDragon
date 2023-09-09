import os


def join_dir_path_with_mk(path: str, sub: str) -> str:
    """
    拼接目录路径和子目录
    如果拼接后的目录不存在 则创建
    :param path: 目录路径
    :param sub: 子目录
    :return: 子目录路径
    """
    sub_path = os.path.join(path, sub)
    if not os.path.exists(sub_path):
        os.mkdir(sub_path)
    return sub_path


def get_env(key: str) -> str:
    """
    获取环境变量
    :param key: key
    :return: value
    """
    return os.environ.get(key)


def is_debug() -> bool:
    """
    判断当前是否在debug模式
    环境变量 DEBUG = 1
    :return: 是否在debug模式
    """
    return '1' == get_env('DEBUG')
