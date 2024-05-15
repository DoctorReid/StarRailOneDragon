import os
import shutil
import subprocess
import time
import urllib.request
import zipfile
from functools import lru_cache
from typing import Optional

import requests
import yaml

from basic import os_utils
from basic.log_utils import log
from sr.one_dragon_config import GH_PROXY_URL


SPECIFIED_VERSION_FILE_URL = 'https://github.com/DoctorReid/StarRailOneDragon/releases/download/%s/%s'


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


def get_latest_release_info(proxy: Optional[str] = None):
    """
    获取github上最新的release信息
    :param proxy: 请求时使用的代理地址
    :return:
    """
    log.info('正在获取最新版本信息')

    proxy_to_use = None if proxy == GH_PROXY_URL else proxy
    proxies = {'http': proxy_to_use, 'https': proxy_to_use} if proxy_to_use is not None else None

    url = 'https://api.github.com/repos/DoctorReid/StarRailOneDragon/releases/latest'
    response = requests.get(url, proxies=proxies)
    if response.status_code != 200:
        log.error('获取最新版本信息失败 %s', response.content)
        return None
    else:
        return response.json()


def check_new_version(proxy: Optional[str] = None) -> int:
    """
    检查是否有新版本
    :param proxy: 请求时使用的代理地址
    :return: 0 - 已是最新版本；1 - 有新版本；2 - 检查更新失败
    """
    release = get_latest_release_info(proxy=proxy)
    if release is None:
        return 2
    asset_ready: bool = False
    for asset in release["assets"]:
        if asset['name'] == 'version.yml':  # 打包上传流程的最后一个文件 用来判断上传是否结束
            asset_ready = True
            break

    if not asset_ready:  # 资源还没有上传完
        return 0

    if release['tag_name'] != get_current_version():
        return 1

    return 0


def check_specified_version(version: str, proxy: Optional[str] = None) -> int:
    """
    检查特定版本是否存在 通过下载 version.yml 判断
    :param version: 指定版本
    :param proxy: 请求时使用的代理地址
    :return: 0 - 已是最新版本；1 - 有新版本；2 - 检查更新失败
    """
    version_url = SPECIFIED_VERSION_FILE_URL % (version, 'version.yml')
    success = download_file('version.yml', version_url, proxy=proxy)  # 第一步必选先下载新版本信息

    if success:
        return 1
    else:
        return 2


def do_update(version: Optional[str] = None, proxy: Optional[str] = None):
    """
    执行更新
    1. 比较本地和最新的 version.yml
    2. 找出需要更新的zip包，下载解压到 .temp 文件夹
    3. 关闭当前脚本
    4. 复制 .temp 中的内容到当前脚本目录
    :param version:
    :param proxy: 下载时使用的代理地址
    :return:
    """
    if version is None:
        release = get_latest_release_info(proxy=proxy)
        version = release['tag_name']

        name_2_url = {}

        for asset in release["assets"]:
            name_2_url[asset['name']] = asset["browser_download_url"]

        if 'version.yml' not in name_2_url:
            log.error('新版本文件还没准备好')  # 理论逻辑不应该进入这里
            return

        download_version = download_file('version.yml', name_2_url['version.yml'], proxy=proxy)  # 第一步必选先下载新版本信息
    else:
        check = check_specified_version(version, proxy=proxy)
        download_version = check == 1

    if not download_version:
        log.error('下载新版本文件失败')
        return

    temp_dir = os_utils.get_path_under_work_dir('.temp')
    new_version_path = os.path.join(temp_dir, 'version.yml')

    with open(new_version_path, 'r') as file:
        new_version = yaml.safe_load(file)

    to_update = set()

    for key in new_version:
        if key in ['version']:
            continue
        to_update.add(key)

    old_version_path = os.path.join(os_utils.get_work_dir(), 'version.yml')
    if os.path.exists(old_version_path):
        with open(old_version_path, 'r') as file:
            old_version = yaml.safe_load(file)
            for key in old_version:
                if key in new_version \
                    and key in to_update \
                        and new_version[key] == old_version[key]:
                    to_update.remove(key)

    all_ok = download_and_unzip(version, to_update, proxy=proxy)
    if all_ok:
        move_temp_and_restart()
    else:
        log.error('部分文件下载解压失败 请重试')


def download_file(filename, url,
                  proxy: Optional[str] = None) -> bool:
    """
    下载文件到 .temp 文件夹中
    :param filename: 保存的文件名
    :param url: 下载地址
    :param proxy: 下载使用的代理地址
    :return: 是否下载成功
    """
    if proxy is not None:
        if proxy == GH_PROXY_URL:
            url = GH_PROXY_URL + url
            proxy = None
        else:
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
        progress = downloaded / total_size_mb * 100
        log.info(f"正在下载 {filename}: {downloaded:.2f}/{total_size_mb:.2f} MB ({progress:.2f}%)")

    try:
        file_name, response = urllib.request.urlretrieve(url, file_path, log_download_progress)
        log.info('下载完成 %s', filename)
        return True
    except Exception:
        log.error('下载失败', exc_info=True)
        return False


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
    shutil.rmtree(os_utils.get_path_under_work_dir('.temp', 'StarRailOneDragon'))


def download_and_unzip(version: str, to_update: set[str] = None,
                       proxy: Optional[str] = None) -> bool:
    """
    下载所需的文件到 .temp 并解压
    :param version: 版本号
    :param to_update: 需要更新的模块
    :param proxy: 下载使用的代理地址
    :return: 是否全部都下载解压成功
    """
    delete_old_files()
    all_ok = True
    if to_update is None or 'requirements' in to_update:
        filename = 'StarRailOneDragon-%s.zip' % version
        url = SPECIFIED_VERSION_FILE_URL % (version, filename)
        if download_file(filename, url, proxy):
            unzip(filename)
        else:
            all_ok = False

    else:
        for module in to_update:
            filename = module + '.zip'
            url = SPECIFIED_VERSION_FILE_URL % (version, filename)
            if download_file(filename, url, proxy):
                unzip(filename)
            else:
                all_ok = False
    return all_ok


def move_temp_and_restart():
    """
    复制 .temp 目录下文件 并重启应用
    :return:
    """
    bat_file = os.path.join(os_utils.get_work_dir(), 'update_by_temp.bat')
    # 执行批处理文件
    subprocess.Popen(bat_file, shell=True)
