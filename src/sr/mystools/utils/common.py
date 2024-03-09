import hashlib
import io
import json
import os
import random
import string
import time
import uuid
from copy import deepcopy
from pathlib import Path
from typing import (Dict, Literal,
                    Union, Optional, Tuple, Iterable, List)
from urllib.parse import urlencode

import httpx
import tenacity
from qrcode import QRCode

from basic.log_utils import log
from ..model import GeetestResult, PluginDataManager, Preference, plugin_config, plugin_env, UserData

__all__ = ["custom_attempt_times",
           "get_async_retry", "generate_device_id", "cookie_str_to_dict", "cookie_dict_to_str", "generate_ds",
           "get_validate", "generate_seed_id", "generate_fp_locally", "get_file", "blur_phone", "generate_qr_img",
           "get_unique_users", "get_all_bind", "read_blacklist", "read_whitelist",
           "read_admin_list"]


def custom_attempt_times(retry: bool):
    """
    自定义的重试机制停止条件\n
    根据是否要重试的bool值，给出相应的`tenacity.stop_after_attempt`对象

    :param retry True - 重试次数达到配置中 MAX_RETRY_TIMES 时停止; False - 执行次数达到1时停止，即不进行重试
    """
    if retry:
        return tenacity.stop_after_attempt(plugin_config.preference.max_retry_times + 1)
    else:
        return tenacity.stop_after_attempt(1)


def get_async_retry(retry: bool):
    """
    获取异步重试装饰器

    :param retry: True - 重试次数达到偏好设置中 max_retry_times 时停止; False - 执行次数达到1时停止，即不进行重试
    """
    return tenacity.AsyncRetrying(
        stop=custom_attempt_times(retry),
        retry=tenacity.retry_if_exception_type(BaseException),
        wait=tenacity.wait_fixed(plugin_config.preference.retry_interval),
    )


def generate_device_id() -> str:
    """
    生成随机的x-rpc-device_id
    """
    return str(uuid.uuid4()).upper()


def cookie_str_to_dict(cookie_str: str) -> Dict[str, str]:
    """
    将字符串Cookie转换为字典Cookie
    """
    cookie_str = cookie_str.replace(" ", "")
    # Cookie末尾缺少 ; 的情况
    if cookie_str[-1] != ";":
        cookie_str += ";"

    cookie_dict = {}
    start = 0
    while start != len(cookie_str):
        mid = cookie_str.find("=", start)
        end = cookie_str.find(";", mid)
        cookie_dict.setdefault(cookie_str[start:mid], cookie_str[mid + 1:end])
        start = end + 1
    return cookie_dict


def cookie_dict_to_str(cookie_dict: Dict[str, str]) -> str:
    """
    将字符串Cookie转换为字典Cookie
    """
    cookie_str = ""
    for key in cookie_dict:
        cookie_str += (key + "=" + cookie_dict[key] + ";")
    return cookie_str


def generate_ds(data: Union[str, dict, list, None] = None, params: Union[str, dict, None] = None,
                platform: Literal["ios", "android"] = "ios", salt: Optional[str] = None):
    """
    获取Headers中所需DS

    :param data: 可选，网络请求中需要发送的数据
    :param params: 可选，URL参数
    :param platform: 可选，平台，ios或android
    :param salt: 可选，自定义salt
    """
    if data is None and params is None or \
            salt is not None and salt != plugin_env.salt_config.SALT_PROD:
        if platform == "ios":
            salt = salt or plugin_env.salt_config.SALT_IOS
        else:
            salt = salt or plugin_env.salt_config.SALT_ANDROID
        t = str(int(time.time()))
        a = "".join(random.sample(
            string.ascii_lowercase + string.digits, 6))
        re = hashlib.md5(
            f"salt={salt}&t={t}&r={a}".encode()).hexdigest()
        return f"{t},{a},{re}"
    else:
        if params:
            salt = plugin_env.salt_config.SALT_PARAMS if not salt else salt
        else:
            salt = plugin_env.salt_config.SALT_DATA if not salt else salt

        if not data:
            if salt == plugin_env.salt_config.SALT_PROD:
                data = {}
            else:
                data = ""
        if not params:
            params = ""

        if not isinstance(data, str):
            data = json.dumps(data)
        if not isinstance(params, str):
            params = urlencode(params)

        t = str(int(time.time()))
        r = str(random.randint(100000, 200000))
        c = hashlib.md5(
            f"salt={salt}&t={t}&r={r}&b={data}&q={params}".encode()).hexdigest()
        return f"{t},{r},{c}"


async def get_validate(gt: str = None, challenge: str = None, retry: bool = True):
    """
    使用打码平台获取人机验证validate

    :param gt: 验证码gt
    :param challenge: challenge
    :param retry: 是否允许重试
    :return: 如果配置了平台URL，且 gt, challenge 不为空，返回 GeetestResult
    """
    if not (gt and challenge) or not plugin_config.preference.geetest_url:
        return GeetestResult("", "")
    params = {"gt": gt, "challenge": challenge}
    params.update(plugin_config.preference.geetest_params)
    content = deepcopy(plugin_config.preference.geetest_json or Preference().geetest_json)
    for key, value in content.items():
        if isinstance(value, str):
            content[key] = value.format(gt=gt, challenge=challenge)
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.post(
                        plugin_config.preference.geetest_url,
                        params=params,
                        json=content,
                        timeout=60
                    )
                geetest_data = res.json()
                validate = geetest_data['data']['validate']
                seccode = geetest_data['data'].get('seccode') or f"{validate}|jordan"
                log.debug(f"{plugin_config.preference.log_head}人机验证结果：{geetest_data}")
                return GeetestResult(validate=validate, seccode=seccode)
    except tenacity.RetryError:
        log.exception(f"{plugin_config.preference.log_head}获取人机验证validate失败")


def generate_seed_id(length: int = 8) -> str:
    """
    生成随机的 seed_id（即长度为8的十六进制数）

    :param length: 16进制数长度
    """
    max_num = int("FF" * length, 16)
    return hex(random.randint(0, max_num))[2:]


def generate_fp_locally(length: int = 13):
    """
    于本地生成 device_fp

    :param length: device_fp 长度
    """
    characters = string.digits + "abcdef"
    return ''.join(random.choices(characters, k=length))


async def get_file(url: str, retry: bool = True):
    """
    下载文件

    :param url: 文件URL
    :param retry: 是否允许重试
    :return: 文件数据
    """
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(url, timeout=plugin_config.preference.timeout, follow_redirects=True)
                return res.content
    except tenacity.RetryError:
        log.exception(f"{plugin_config.preference.log_head}下载文件 - {url} 失败")


def blur_phone(phone: Union[str, int]) -> str:
    """
    模糊手机号

    :param phone: 手机号
    :return: 模糊后的手机号
    """
    if isinstance(phone, int):
        phone = str(phone)
    return f"{phone[-4:]}"


def generate_qr_img(data: str):
    """
    生成二维码图片

    :param data: 二维码数据

    >>> b = generate_qr_img("https://github.com/Ljzd-PRO/nonebot-plugin-mystool")
    >>> isinstance(b, bytes)
    """
    qr_code = QRCode(border=2)
    qr_code.add_data(data)
    qr_code.make()
    image = qr_code.make_image()
    image_bytes = io.BytesIO()
    image.save(image_bytes)
    return image_bytes.getvalue()


def get_unique_users() -> Iterable[Tuple[str, UserData]]:
    """
    获取 不包含绑定用户数据 的所有用户数据以及对应的ID，即不会出现值重复项

    :return: dict_items[用户ID, 用户数据]
    """
    return filter(lambda x: x[0] not in PluginDataManager.plugin_data.user_bind,
                  PluginDataManager.plugin_data.users.items())


def get_all_bind(user_id: str) -> Iterable[str]:
    """
    获取绑定该用户的所有用户ID

    :return: 绑定该用户的所有用户ID
    """
    user_id_filter = filter(lambda x: PluginDataManager.plugin_data.user_bind.get(x) == user_id,
                            PluginDataManager.plugin_data.user_bind)
    return user_id_filter


def _read_user_list(path: Path) -> List[str]:
    """
    从TEXT读取用户名单

    :return: 名单中的所有用户ID
    """
    if not path:
        return []
    if os.path.isfile(path):
        with open(path, "r", encoding=plugin_config.preference.encoding) as f:
            lines = f.readlines()
        lines = map(lambda x: x.strip(), lines)
        line_filter = filter(lambda x: x and x != "\n", lines)
        return list(line_filter)
    else:
        log.error(f"{plugin_config.preference.log_head}黑/白名单文件 {path} 不存在")
        return []


def read_blacklist() -> List[str]:
    """
    读取黑名单

    :return: 黑名单中的所有用户ID
    """
    return _read_user_list(plugin_config.preference.blacklist_path) if plugin_config.preference.enable_blacklist else []


def read_whitelist() -> List[str]:
    """
    读取白名单

    :return: 白名单中的所有用户ID
    """
    return _read_user_list(plugin_config.preference.whitelist_path) if plugin_config.preference.enable_whitelist else []


def read_admin_list() -> List[str]:
    """
    读取白名单

    :return: 管理员名单中的所有用户ID
    """
    return _read_user_list(
        plugin_config.preference.admin_list_path) if plugin_config.preference.enable_admin_list else []
