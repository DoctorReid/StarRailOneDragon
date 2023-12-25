import os
import shutil
import time
import urllib.request
import zipfile
from functools import lru_cache
from typing import Optional

import requests
import subprocess
import yaml

from basic import os_utils
from basic.log_utils import log
from sr.const.game_config_const import GH_PROXY_URL


@lru_cache
def get_current_version() -> str:
    """
    获取当前版本
    :return:
    """
    old_version_path = os.path.join(os_utils.get_work_dir(), 'version.yml')
    if not os.path.exists(old_version_path):
        return ''
    with open(old_version_path, 'r') as file:
        old_version = yaml.safe_load(file)
        return old_version['version'] if 'version' in old_version else ''


def get_latest_release_info(proxy: Optional[str] = None, pre_release: bool = False):
    """
    获取github上最新的release信息
    :param proxy: 请求时使用的代理地址
    :param pre_release: 是否使用 pre_release 版本
    :return:
    """
    log.info('正在获取最新版本信息')

    proxy_to_use = None if proxy == GH_PROXY_URL else proxy
    proxies = {'http': proxy_to_use, 'https': proxy_to_use} if proxy_to_use is not None else None

    if pre_release:  # 获取pre-release
        url = 'https://api.github.com/repos/DoctorReid/StarRailAutoProxy/releases'
        response = requests.get(url, proxies=proxies)
        if response.status_code != 200:
            log.error('获取最新版本信息失败 %s', response.content)
            return None
        else:
            return response.json()[0]
    else:  # 获取最新release信息
        url = 'https://api.github.com/repos/DoctorReid/StarRailAutoProxy/releases/latest'
        response = requests.get(url, proxies=proxies)
        if response.status_code != 200:
            log.error('获取最新版本信息失败 %s', response.content)
            return None
        else:
            return response.json()


def check_new_version(proxy: Optional[str] = None, pre_release: bool = False) -> int:
    """
    检查是否有新版本
    :param proxy: 请求时使用的代理地址
    :param pre_release: 是否使用 pre_release 版本
    :return: 0 - 已是最新版本；1 - 有新版本；2 - 检查更新失败
    """
    release = get_latest_release_info(proxy=proxy, pre_release=pre_release)
    if release is None:
        return 2
    asset_ready: bool = False
    for asset in release["assets"]:
        if asset['name'] == 'version.yml':  # 打包上传流程的最后一个文件 用来判断上传是否结束
            asset_ready = True
            break

    if not asset_ready:  # 资源还没有上传完
        return 0

    if pre_release and not release['prerelease']:
        return 0

    if release['tag_name'] != get_current_version():
        return 1

    return 0


def do_update(proxy: Optional[str] = None, pre_release: bool = False):
    """
    执行更新
    1. 比较本地和最新的 version.yml
    2. 找出需要更新的zip包，下载解压到 .temp 文件夹
    3. 关闭当前脚本
    4. 复制 .temp 中的内容到当前脚本目录
    :param proxy: 下载时使用的代理地址
    :param pre_release: 是否使用 pre_release 版本
    :return:
    """
    release = get_latest_release_info(proxy=proxy, pre_release=pre_release)

    name_2_url = {}

    for asset in release["assets"]:
        name_2_url[asset['name']] = asset["browser_download_url"]

    if 'version.yml' not in name_2_url:
        log.error('新版本文件还没准备好')  # 理论逻辑不应该进入这里
        return

    download_file('version.yml', name_2_url['version.yml'], proxy=proxy)  # 第一步必选先下载新版本信息

    old_version_path = os.path.join(os_utils.get_work_dir(), 'version.yml')
    if not os.path.exists(old_version_path):
        download_and_unzip(name_2_url, proxy=proxy)
        return

    temp_dir = os_utils.get_path_under_work_dir('.temp')
    new_version_path = os.path.join(temp_dir, 'version.yml')

    to_update = set()

    with open(old_version_path, 'r') as file:
        old_version = yaml.safe_load(file)

    with open(new_version_path, 'r') as file:
        new_version = yaml.safe_load(file)

    for key in new_version:
        if key not in old_version or new_version[key] != old_version[key]:
            to_update.add(key)

    download_and_unzip(name_2_url, to_update, proxy=proxy)
    move_temp_and_restart()


def download_file(filename, url,
                  proxy: Optional[str] = None,):
    """
    下载文件到 .temp 文件夹中
    :param filename: 保存的文件名
    :param url: 下载地址
    :param proxy: 下载使用的代理地址
    :return:
    """
    if proxy is not None:
        proxy_handler = urllib.request.ProxyHandler(
            {'http': proxy, 'https': proxy})
        opener = urllib.request.build_opener(proxy_handler)
        urllib.request.install_opener(opener)
    log.info('开始下载 %s %s', filename, url)
    temp_dir = os_utils.get_path_under_work_dir('.temp')
    file_path = os.path.join(temp_dir, filename)
    last_log_time = time.time()

    def log_download_progress(block_num, block_size, total_size):
        nonlocal last_log_time
        if time.time() - last_log_time < 1:
            return
        last_log_time = time.time()
        downloaded = block_num * block_size / 1024.0 / 1024.0
        total_size_mb = total_size / 1024.0 / 1024.0
        progress = downloaded / total_size * 100
        log.info(f"正在下载 {filename}: {downloaded:.2f}/{total_size_mb:.2f} MB ({progress:.2f}%)")

    urllib.request.urlretrieve(url, file_path, log_download_progress)
    log.info('下载完成 %s', filename)


def unzip(filename):
    """
    解压文件
    :param filename:
    :return:
    """
    log.info('开始解压文件 %s', filename)
    temp_dir = os_utils.get_path_under_work_dir('.temp')
    zip_path = os.path.join(temp_dir, filename)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    log.info('解压完成 %s', filename)


def delete_old_files():
    """
    正式下载更新前 删除旧的文件夹内容
    :return:
    """
    shutil.rmtree(os_utils.get_path_under_work_dir('.temp', 'StarRailAutoProxy'))


def download_and_unzip(name_2_url: dict[str, str], to_update: set[str] = None,
                       proxy: Optional[str] = None):
    """
    下载所需的文件到 .temp 并解压
    :param name_2_url: 文件名对应的下载路径
    :param to_update: 需要更新的模块
    :param proxy: 下载使用的代理地址
    :return:
    """
    delete_old_files()
    if to_update is None or 'requirements' in to_update:
        filename, url = None, None
        for i in name_2_url.keys():
            if i.startswith('StarRailAutoProxy') and i.endswith('.zip'):
                filename = i
                url = name_2_url[i]
        download_file(filename, url, proxy)
        unzip(filename)
    else:
        for module in to_update:
            filename = module + '.zip'
            if filename not in name_2_url:
                continue
            url = name_2_url[filename]
            download_file(filename, url, proxy)
            unzip(filename)


def move_temp_and_restart():
    """
    复制 .temp 目录下文件 并重启应用
    :return:
    """
    bat_file = os.path.join(os_utils.get_work_dir(), 'update_by_temp.bat')
    # 执行批处理文件
    subprocess.Popen(bat_file, shell=True)
