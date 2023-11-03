import os
import subprocess
import urllib.request
import zipfile
from functools import lru_cache

import requests
import yaml

from basic import os_utils
from basic.log_utils import log
from sr import const


@lru_cache
def get_current_version() -> str:
    temp_dir = os_utils.get_path_under_work_dir('.temp')
    old_version_path = os.path.join(temp_dir, 'version.yml')
    if not os.path.exists(old_version_path):
        return ''
    with open(old_version_path, 'r') as file:
        old_version = yaml.safe_load(file)
        return old_version['version'] if 'version' in old_version else ''


def get_latest_release_info():
    # 仓库信息
    log.info('正在获取最新版本信息')
    owner = "DoctorReid"  # 替换为仓库所有者的用户名或组织名
    repo = "StarRailAutoProxy"  # 替换为仓库名称

    # 发起API请求获取最新release信息
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    response = requests.get(url)
    return response.json()


def check_new_version() -> bool:
    release = get_latest_release_info()
    asset_ready: bool = False
    for asset in release["assets"]:
        if asset['name'] == 'version.yml':  # 打包上传流程的最后一个文件 用来判断上传是否结束
            asset_ready = True
    return asset_ready and release['tag_name'] != const.SCRIPT_VERSION


def update_scripts():
    release = get_latest_release_info()

    name_2_url = {}

    for asset in release["assets"]:
        name_2_url[asset['name']] = asset["browser_download_url"]

    if 'version.yml' not in name_2_url:
        log.error('新版本文件还没准备好')  # 理论逻辑不应该进入这里
        return

    download_file('version.yml', name_2_url['version.yml'])  # 第一步必选先下载新版本信息

    old_version_path = os.path.join(os_utils.get_work_dir(), 'version.yml')
    if not os.path.exists(old_version_path):
        do_update(name_2_url)
        return

    temp_dir = os_utils.get_path_under_work_dir('.temp')
    new_version_path = os.path.join(temp_dir, 'new_version.yml')

    to_update = set()

    with open(old_version_path, 'r') as file:
        old_version = yaml.safe_load(file)

    with open(new_version_path, 'r') as file:
        new_version = yaml.safe_load(file)

    for key in new_version:
        if key not in old_version or new_version[key] != old_version[key]:
            to_update.add(key)

    do_update(name_2_url, to_update)


def download_file(filename, url):
    log.info('开始下载 %s', filename)
    temp_dir = os_utils.get_path_under_work_dir('.temp')
    file_path = os.path.join(temp_dir, filename)
    def log_download_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        progress = downloaded / total_size * 100
        log.info(f"正在下载 {filename}: {downloaded}/{total_size} bytes ({progress:.2f}%)")

    urllib.request.urlretrieve(url, file_path, log_download_progress)
    log.info('下载完成 %s', filename)


def unzip(filename):
    log.info('开始解压文件 %s', filename)
    temp_dir = os_utils.get_path_under_work_dir('.temp')
    zip_path = os.path.join(temp_dir, filename)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    log.info('解压完成 %s', filename)


def do_update(name_2_url: dict[str, str], to_update: set[str] = None):
    if to_update is None or 'requirements' in to_update:
        filename, url = None, None
        for i in name_2_url.keys():
            if i.startswith('StarRailAutoProxy') and i.endswith('.zip'):
                filename = i
                url = name_2_url[i]
        download_file(filename, url)
        unzip(filename)
    else:
        for module in to_update:
            filename = module + '.zip'
            if filename not in name_2_url:
                continue
            url = name_2_url[filename]
            download_file(filename, url)
            unzip(filename)

    bat_file = os.path.join(os_utils.get_work_dir(), 'update.bat')


if __name__ == '__main__':
    update_scripts()