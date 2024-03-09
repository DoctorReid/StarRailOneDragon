from typing import List, Optional, Tuple, Literal, Set, Type
from urllib.parse import urlencode

import httpx
import tenacity

from basic.log_utils import log
from ..api.common import ApiResultHandler, HEADERS_API_TAKUMI_MOBILE, is_incorrect_return, \
    device_login, device_save
from ..model import GameRecord, BaseApiStatus, Award, GameSignInfo, GeetestResult, MmtData, plugin_config, plugin_env, \
    UserAccount
from ..utils import generate_ds, \
    get_async_retry

__all__ = ["BaseGameSign", "GenshinImpactSign", "HonkaiImpact3Sign", "HoukaiGakuen2Sign", "TearsOfThemisSign",
           "StarRailSign"]


class BaseGameSign:
    """
    游戏签到基类
    """
    name = ""
    """游戏名字"""

    act_id = ""
    url_reward = "https://api-takumi.mihoyo.com/event/luna/home"
    url_info = "https://api-takumi.mihoyo.com/event/luna/info"
    url_sign = "https://api-takumi.mihoyo.com/event/luna/sign"
    headers_general = HEADERS_API_TAKUMI_MOBILE.copy()
    headers_reward = {
        "Host": "api-takumi.mihoyo.com",
        "Origin": "https://webstatic.mihoyo.com",
        "Connection": "keep-alive",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": plugin_env.device_config.USER_AGENT_MOBILE,
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Referer": "https://webstatic.mihoyo.com/",
        "Accept-Encoding": "gzip, deflate, br"
    }
    game_id = 0

    available_game_signs: Set[Type["BaseGameSign"]] = set()
    """可用的子类"""

    def __init__(self, account: UserAccount, records: List[GameRecord]):
        self.account = account
        self.record = next(filter(lambda x: x.game_id == self.game_id, records), None)
        reward_params = {
            "lang": "zh-cn",
            "act_id": self.act_id
        }
        self.url_reward = f"{self.url_reward}?{urlencode(reward_params)}"
        info_params = {
            "lang": "zh-cn",
            "act_id": self.act_id,
            "region": self.record.region if self.record else None,
            "uid": self.record.game_role_id if self.record else None
        }
        self.url_info = f"{self.url_info}?{urlencode(info_params)}"

    @property
    def has_record(self) -> bool:
        """
        是否有游戏账号
        """
        return self.record is not None

    async def get_rewards(self, retry: bool = True) -> Tuple[BaseApiStatus, Optional[List[Award]]]:
        """
        获取签到奖励信息

        :param retry: 是否允许重试
        """
        try:
            async for attempt in get_async_retry(retry):
                with attempt:
                    async with httpx.AsyncClient() as client:
                        res = await client.get(self.url_reward, headers=self.headers_reward,
                                               timeout=plugin_config.preference.timeout)
                    award_list = []
                    for award in res.json()["data"]["awards"]:
                        award_list.append(Award.parse_obj(award))
                    return BaseApiStatus(success=True), award_list
        except tenacity.RetryError as e:
            if is_incorrect_return(e):
                log.exception(f"获取签到奖励信息 - 服务器没有正确返回")
                log.debug(f"网络请求返回: {res.text}")
                return BaseApiStatus(incorrect_return=True), None
            else:
                log.exception(f"获取签到奖励信息 - 请求失败")
                return BaseApiStatus(network_error=True), None

    async def get_info(
            self,
            platform: Literal["ios", "android"] = "ios",
            retry: bool = True
    ) -> Tuple[BaseApiStatus, Optional[GameSignInfo]]:
        """
        获取签到记录

        :param platform: 使用的设备平台
        :param retry: 是否允许重试
        """
        headers = self.headers_general.copy()
        headers["x-rpc-device_id"] = self.account.device_id_ios if platform == "ios" else self.account.device_id_android

        try:
            async for attempt in get_async_retry(retry):
                with attempt:
                    headers["DS"] = generate_ds() if platform == "ios" else generate_ds(platform="android")
                    async with httpx.AsyncClient() as client:
                        res = await client.get(self.url_info, headers=headers,
                                               cookies=self.account.cookies.dict(),
                                               timeout=plugin_config.preference.timeout)
                    api_result = ApiResultHandler(res.json())
                    if api_result.login_expired:
                        log.info(
                            f"获取签到数据 - 用户 {self.account.display_name} 登录失效")
                        log.debug(f"网络请求返回: {res.text}")
                        return BaseApiStatus(login_expired=True), None
                    if api_result.invalid_ds:
                        log.info(
                            f"获取签到数据 - 用户 {self.account.display_name} DS 校验失败")
                        log.debug(f"网络请求返回: {res.text}")
                        return BaseApiStatus(invalid_ds=True), None
                    return BaseApiStatus(success=True), GameSignInfo.parse_obj(api_result.data)
        except tenacity.RetryError as e:
            if is_incorrect_return(e):
                log.exception(f"获取签到数据 - 服务器没有正确返回")
                log.debug(f"网络请求返回: {res.text}")
                return BaseApiStatus(incorrect_return=True), None
            else:
                log.exception(f"获取签到数据 - 请求失败")
                return BaseApiStatus(network_error=True), None

    async def sign(self,
                   platform: Literal["ios", "android"] = "ios",
                   mmt_data: MmtData = None,
                   geetest_result: GeetestResult = None,
                   retry: bool = True) -> Tuple[BaseApiStatus, Optional[MmtData]]:
        """
        签到

        :param platform: 设备平台
        :param mmt_data: 人机验证任务
        :param geetest_result: 用于执行签到的人机验证结果
        :param retry: 是否允许重试
        """
        if not self.record:
            return BaseApiStatus(success=True), None
        content = {
            "act_id": self.act_id,
            "region": self.record.region,
            "uid": self.record.game_role_id
        }
        headers = self.headers_general.copy()
        if platform == "ios":
            headers["x-rpc-device_id"] = self.account.device_id_ios
            headers["Sec-Fetch-Dest"] = "empty"
            headers["Sec-Fetch-Site"] = "same-site"
            headers["DS"] = generate_ds()
        else:
            await device_login(self.account)
            await device_save(self.account)
            headers["x-rpc-device_id"] = self.account.device_id_android
            headers["x-rpc-device_model"] = plugin_env.device_config.X_RPC_DEVICE_MODEL_ANDROID
            headers["User-Agent"] = plugin_env.device_config.USER_AGENT_ANDROID
            headers["x-rpc-device_name"] = plugin_env.device_config.X_RPC_DEVICE_NAME_ANDROID
            headers["x-rpc-channel"] = plugin_env.device_config.X_RPC_CHANNEL_ANDROID
            headers["x-rpc-sys_version"] = plugin_env.device_config.X_RPC_SYS_VERSION_ANDROID
            headers["x-rpc-client_type"] = "2"
            headers["DS"] = generate_ds(data=content)
            headers.pop("x-rpc-platform")

        try:
            async for attempt in get_async_retry(retry):
                with attempt:
                    if geetest_result:
                        headers["x-rpc-validate"] = geetest_result.validate
                        headers["x-rpc-challenge"] = mmt_data.challenge
                        headers["x-rpc-seccode"] = geetest_result.seccode
                        log.info("游戏签到 - 尝试使用人机验证结果进行签到")

                    async with httpx.AsyncClient() as client:
                        res = await client.post(
                            self.url_sign,
                            headers=headers,
                            cookies=self.account.cookies.dict(),
                            timeout=plugin_config.preference.timeout,
                            json=content
                        )

                    api_result = ApiResultHandler(res.json())
                    if api_result.login_expired:
                        log.info(
                            f"游戏签到 - 用户 {self.account.display_name} 登录失效")
                        log.debug(f"网络请求返回: {res.text}")
                        return BaseApiStatus(login_expired=True), None
                    elif api_result.invalid_ds:
                        log.info(
                            f"游戏签到 - 用户 {self.account.display_name} DS 校验失败")
                        log.debug(f"网络请求返回: {res.text}")
                        return BaseApiStatus(invalid_ds=True), None
                    elif api_result.data.get("risk_code") != 0:
                        log.warning(
                            f"{plugin_config.preference.log_head}游戏签到 - 用户 {self.account.display_name} 可能被人机验证阻拦")
                        log.debug(f"{plugin_config.preference.log_head}网络请求返回: {res.text}")
                        return BaseApiStatus(need_verify=True), MmtData.parse_obj(api_result.data)
                    else:
                        log.success(f"游戏签到 - 用户 {self.account.display_name} 签到成功")
                        log.debug(f"网络请求返回: {res.text}")
                        return BaseApiStatus(success=True), None

        except tenacity.RetryError as e:
            if is_incorrect_return(e):
                log.exception(f"游戏签到 - 服务器没有正确返回")
                log.debug(f"网络请求返回: {res.text}")
                return BaseApiStatus(incorrect_return=True), None
            else:
                log.exception(f"游戏签到 - 请求失败")
                return BaseApiStatus(network_error=True), None


class GenshinImpactSign(BaseGameSign):
    """
    原神 游戏签到
    """
    name = "原神"
    act_id = "e202311201442471"
    game_id = 2
    headers_general = BaseGameSign.headers_general.copy()
    headers_reward = BaseGameSign.headers_reward.copy()
    for headers in headers_general, headers_reward:
        headers["x-rpc-signgame"] = "hk4e"
        headers["Origin"] = "https://act.mihoyo.com"
        headers["Referer"] = "https://act.mihoyo.com/"


class HonkaiImpact3Sign(BaseGameSign):
    """
    崩坏3 游戏签到
    """
    name = "崩坏3"
    act_id = "e202306201626331"
    game_id = 1


class HoukaiGakuen2Sign(BaseGameSign):
    """
    崩坏学园2 游戏签到
    """
    name = "崩坏学园2"
    act_id = "e202203291431091"
    game_id = 3


class TearsOfThemisSign(BaseGameSign):
    """
    未定事件簿 游戏签到
    """
    name = "未定事件簿"
    act_id = "e202202251749321"
    game_id = 4


class StarRailSign(BaseGameSign):
    """
    崩坏：星穹铁道 游戏签到
    """
    name = "崩坏：星穹铁道"
    act_id = "e202304121516551"
    game_id = 6


BaseGameSign.available_game_signs.add(GenshinImpactSign)
BaseGameSign.available_game_signs.add(HonkaiImpact3Sign)
BaseGameSign.available_game_signs.add(HoukaiGakuen2Sign)
BaseGameSign.available_game_signs.add(TearsOfThemisSign)
BaseGameSign.available_game_signs.add(StarRailSign)
