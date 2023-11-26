"""
### 工具函数
"""
import hashlib
import json
import random
import string
import time
import uuid
from copy import deepcopy
from typing import (Literal,
                    Union, Optional)
from urllib.parse import urlencode

import httpx
import tenacity

from basic.log_utils import log
from .data_model import GeetestResult
from .plugin_data import PluginDataManager, Preference

_conf = PluginDataManager.plugin_data


def generate_device_id() -> str:
    """
    生成随机的x-rpc-device_id
    """
    return str(uuid.uuid4()).upper()


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
            salt is not None and salt != _conf.salt_config.SALT_PROD:
        if platform == "ios":
            salt = salt or _conf.salt_config.SALT_IOS
        else:
            salt = salt or _conf.salt_config.SALT_ANDROID
        t = str(int(time.time()))
        a = "".join(random.sample(
            string.ascii_lowercase + string.digits, 6))
        re = hashlib.md5(
            f"salt={salt}&t={t}&r={a}".encode()).hexdigest()
        return f"{t},{a},{re}"
    else:
        if params:
            salt = _conf.salt_config.SALT_PARAMS if not salt else salt
        else:
            salt = _conf.salt_config.SALT_DATA if not salt else salt

        if not data:
            if salt == _conf.salt_config.SALT_PROD:
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


def custom_attempt_times(retry: bool):
    """
    自定义的重试机制停止条件\n
    根据是否要重试的bool值，给出相应的`tenacity.stop_after_attempt`对象

    :param retry True - 重试次数达到配置中 MAX_RETRY_TIMES 时停止; False - 执行次数达到1时停止，即不进行重试
    """
    if retry:
        return tenacity.stop_after_attempt(_conf.preference.max_retry_times + 1)
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
        wait=tenacity.wait_fixed(_conf.preference.retry_interval),
    )


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


async def get_validate(gt: str = None, challenge: str = None, retry: bool = True):
    """
    使用打码平台获取人机验证validate

    :param gt: 验证码gt
    :param challenge: challenge
    :param retry: 是否允许重试
    :return: 如果配置了平台URL，且 gt, challenge 不为空，返回 GeetestResult
    """
    if not (gt and challenge) or not _conf.preference.geetest_url:
        return GeetestResult("", "")
    params = {"gt": gt, "challenge": challenge}
    params.update(_conf.preference.geetest_params)
    content = deepcopy(_conf.preference.geetest_json or Preference().geetest_json)
    for key, value in content.items():
        if isinstance(value, str):
            content[key] = value.format(gt=gt, challenge=challenge)
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.post(
                        _conf.preference.geetest_url,
                        params=params,
                        json=content,
                        timeout=60
                    )
                geetest_data = res.json()
                validate = geetest_data['data']['validate']
                seccode = geetest_data['data'].get('seccode') or f"{validate}|jordan"
                log.debug(f"{_conf.preference.log_head}人机验证结果：{geetest_data}")
                return GeetestResult(validate=validate, seccode=seccode)
    except tenacity.RetryError:
        log.exception(f"{_conf.preference.log_head}获取人机验证validate失败")