import asyncio
from typing import List, Optional, Tuple, Type, Dict

import httpx
import tenacity

from basic.log_utils import log
from ..api.common import ApiResultHandler, is_incorrect_return, create_verification, \
    verify_verification
from ..model import BaseApiStatus, MissionStatus, MissionData, \
    MissionState, UserAccount, plugin_config, plugin_env
from ..utils import generate_ds, \
    get_async_retry, get_validate

URL_SIGN = "https://bbs-api.mihoyo.com/apihub/app/api/signIn"
URL_GET_POST = "https://bbs-api.miyoushe.com/post/api/feeds/posts?fresh_action=1&gids={}&is_first_initialize=false" \
               "&last_id="
URL_READ = "https://bbs-api.miyoushe.com/post/api/getPostFull?post_id={}"
URL_LIKE = "https://bbs-api.miyoushe.com/apihub/sapi/upvotePost"
URL_SHARE = "https://bbs-api.miyoushe.com/apihub/api/getShareConf?entity_id={}&entity_type=1"
URL_MISSION = "https://api-takumi.mihoyo.com/apihub/wapi/getMissions?point_sn=myb"
URL_MISSION_STATE = "https://api-takumi.mihoyo.com/apihub/wapi/getUserMissionsState?point_sn=myb"
HEADERS_BASE = {
    "Host": "bbs-api.miyoushe.com",
    "Referer": "https://app.mihoyo.com",
    'User-Agent': plugin_env.device_config.USER_AGENT_ANDROID_OTHER,
    "x-rpc-app_version": plugin_env.device_config.X_RPC_APP_VERSION,
    "x-rpc-channel": plugin_env.device_config.X_RPC_CHANNEL_ANDROID,
    "x-rpc-client_type": "2",
    "x-rpc-device_id": None,
    "x-rpc-device_model": plugin_env.device_config.X_RPC_DEVICE_MODEL_ANDROID,
    "x-rpc-device_name": plugin_env.device_config.X_RPC_DEVICE_NAME_ANDROID,
    "x-rpc-sys_version": plugin_env.device_config.X_RPC_SYS_VERSION_ANDROID,
    "Accept-Encoding": "gzip",
    "Connection": "Keep-Alive",
    "DS": None
}
HEADERS_MISSION = {
    "Host": "api-takumi.mihoyo.com",
    "Origin": "https://webstatic.mihoyo.com",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": plugin_env.device_config.USER_AGENT_MOBILE,
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Referer": "https://webstatic.mihoyo.com/",
    "Accept-Encoding": "gzip, deflate, br"
}
HEADERS_GET_POSTS = {
    "Host": "bbs-api.miyoushe.com",
    "Accept": "*/*",
    "x-rpc-client_type": "1",
    "x-rpc-device_id": None,
    "x-rpc-channel": plugin_env.device_config.X_RPC_CHANNEL,
    "Accept-Language": "zh-CN,zh-Hans;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "x-rpc-sys_version": plugin_env.device_config.X_RPC_SYS_VERSION,
    "Referer": "https://app.mihoyo.com",
    "x-rpc-device_name": plugin_env.device_config.X_RPC_DEVICE_NAME_MOBILE,
    "x-rpc-app_version": plugin_env.device_config.X_RPC_APP_VERSION,
    "User-Agent": plugin_env.device_config.USER_AGENT_OTHER,
    "Connection": "keep-alive"
}

# 旧的API
HEADERS_OLD = {
    "Host": "bbs-api.mihoyo.com",
    "Referer": "https://app.mihoyo.com",
    'User-Agent': plugin_env.device_config.USER_AGENT_ANDROID_OTHER,
    "x-rpc-app_version": plugin_env.device_config.X_RPC_APP_VERSION,
    "x-rpc-channel": plugin_env.device_config.X_RPC_CHANNEL_ANDROID,
    "x-rpc-client_type": "2",
    "x-rpc-device_id": None,
    "x-rpc-device_model": plugin_env.device_config.X_RPC_DEVICE_MODEL_ANDROID,
    "x-rpc-device_name": plugin_env.device_config.X_RPC_DEVICE_NAME_ANDROID,
    "x-rpc-sys_version": plugin_env.device_config.X_RPC_SYS_VERSION_ANDROID,
    "Accept-Encoding": "gzip",
    "Connection": "Keep-Alive",
    "DS": None
}


class BaseMission:
    """
    米游币任务基类
    """
    name = ""
    """米游社分区名字"""
    gids = 0
    fid = 0

    SIGN = "continuous_sign"
    '''签到任务的 mission_key'''
    VIEW = "view_post_0"
    '''阅读任务的 mission_key'''
    LIKE = "post_up_0"
    '''点赞任务的 mission_key'''
    SHARE = "share_post_0"
    '''分享任务的 mission_key'''

    available_games: Dict[str, Type["BaseMission"]] = {}
    """可用的子类"""

    def __init__(self, account: UserAccount) -> None:
        """
        米游币任务相关

        :param account: 账号对象
        """
        self.account = account
        self.headers = HEADERS_BASE.copy()
        self.headers["x-rpc-device_id"] = account.device_id_android

    async def sign(self, retry: bool = True) -> Tuple[MissionStatus, Optional[int]]:
        """
        签到

        :param retry: 是否允许重试
        :return: (BaseApiStatus, 签到获得的米游币数量)
        """
        content = {"gids": self.gids}
        try:
            async for attempt in get_async_retry(retry):
                with attempt:
                    headers = HEADERS_OLD.copy()
                    headers["x-rpc-device_id"] = self.account.device_id_android
                    headers["DS"] = generate_ds(data=content)
                    async with httpx.AsyncClient() as client:
                        res = await client.post(
                            URL_SIGN,
                            headers=headers,
                            json=content,
                            timeout=plugin_config.preference.timeout,
                            cookies=self.account.cookies.dict(v2_stoken=True, cookie_type=True)
                        )
                    api_result = ApiResultHandler(res.json())
                    if api_result.login_expired:
                        log.error(
                            f"米游币任务 - 讨论区签到: 用户 {self.account.display_name} 登录失效")
                        log.debug(f"网络请求返回: {res.text}")
                        return MissionStatus(login_expired=True), None
                    elif api_result.invalid_ds:
                        log.error(
                            f"米游币任务 - 讨论区签到: 用户 {self.account.display_name} DS 校验失败")
                        log.debug(f"网络请求返回: {res.text}")
                        return MissionStatus(invalid_ds=True), None
                    elif api_result.retcode == 1034:
                        log.error(
                            f"米游币任务 - 讨论区签到: 用户 {self.account.display_name} 需要完成人机验证")
                        log.debug(f"网络请求返回: {res.text}")
                        if plugin_config.preference.geetest_url:
                            create_status, mmt_data = await create_verification(self.account)
                            if create_status:
                                if geetest_result := await get_validate(mmt_data.gt, mmt_data.challenge):
                                    if await verify_verification(mmt_data, geetest_result, self.account):
                                        log.info(
                                            f"米游币任务 - 讨论区签到: 用户 {self.account.display_name} 人机验证通过")
                                        continue
                        else:
                            log.info(
                                f"米游币任务 - 讨论区签到: 用户 {self.account.display_name} 未配置极验人机验证打码平台")
                        return MissionStatus(need_verify=True), None
                    elif api_result.retcode == 1008:
                        log.warning(
                            f"米游币任务 - 讨论区签到: 用户 {self.account.display_name} 今日已经签到过了")
                        log.debug(f"网络请求返回: {res.text}")
                        return MissionStatus(success=True, already_signed=True), 0
                    return MissionStatus(success=True), api_result.data["points"]
        except tenacity.RetryError as e:
            if is_incorrect_return(e):
                log.exception(f"米游币任务 - 讨论区签到: 服务器没有正确返回")
                log.debug(f"网络请求返回: {res.text}")
                return MissionStatus(incorrect_return=True), None
            else:
                log.exception("米游币任务 - 讨论区签到: 请求失败")
                return MissionStatus(network_error=True), None

    async def get_posts(self, retry: bool = True) -> Tuple[BaseApiStatus, Optional[List[str]]]:
        """
        获取文章ID列表，若失败返回 `None`

        :param retry: 是否允许重试
        :return: (BaseApiStatus, 文章ID列表)
        """
        post_id_list = []
        try:
            async for attempt in get_async_retry(retry):
                with attempt:
                    headers = HEADERS_GET_POSTS.copy()
                    headers["x-rpc-device_id"] = self.account.device_id_ios
                    async with httpx.AsyncClient() as client:
                        res = await client.get(
                            URL_GET_POST.format(self.gids),
                            headers=headers,
                            timeout=plugin_config.preference.timeout
                        )
                    api_result = ApiResultHandler(res.json())
                    for post in api_result.data["list"]:
                        if post["self_operation"]["attitude"] == 0:
                            post_id_list.append(post['post']['post_id'])
                    break
            return BaseApiStatus(success=True), post_id_list
        except tenacity.RetryError as e:
            if is_incorrect_return(e):
                log.exception(f"米游币任务 - 获取文章列表: 服务器没有正确返回")
                log.debug(f"网络请求返回: {res.text}")
                return BaseApiStatus(incorrect_return=True), None
            else:
                log.exception(f"米游币任务 - 获取文章列表: 请求失败")
                return BaseApiStatus(network_error=True), None

    async def read(self, read_times: int = 5, retry: bool = True) -> MissionStatus:
        """
        阅读

        :param read_times: 阅读文章数
        :param retry: 是否允许重试
        """
        count = 0
        get_post_status, posts = await self.get_posts(retry)
        if not get_post_status:
            return MissionStatus(failed_getting_post=True)
        while count < read_times:
            for post_id in posts:
                if count == read_times:
                    break
                try:
                    async for attempt in get_async_retry(retry):
                        with attempt:
                            self.headers["DS"] = generate_ds(platform="android")
                            async with httpx.AsyncClient() as client:
                                res = await client.get(
                                    URL_READ.format(post_id),
                                    headers=self.headers,
                                    timeout=plugin_config.preference.timeout,
                                    cookies=self.account.cookies.dict(v2_stoken=True, cookie_type=True)
                                )
                            api_result = ApiResultHandler(res.json())
                            if api_result.login_expired:
                                log.info(
                                    f"米游币任务 - 阅读: 用户 {self.account.display_name} 登录失效")
                                log.debug(f"网络请求返回: {res.text}")
                                return MissionStatus(login_expired=True)
                            if api_result.invalid_ds:
                                log.info(
                                    f"米游币任务 - 阅读: 用户 {self.account.display_name} DS 校验失败")
                                log.debug(f"网络请求返回: {res.text}")
                                return MissionStatus(invalid_ds=True)
                            if api_result.message == "帖子不存在":
                                continue
                            temp = api_result.data.get("post")
                            if temp is not None and "self_operation" not in temp:
                                raise ValueError
                            count += 1
                except tenacity.RetryError as e:
                    if is_incorrect_return(e, ValueError):
                        log.exception(f"米游币任务 - 阅读: 服务器没有正确返回")
                        log.debug(f"网络请求返回: {res.text}")
                        return MissionStatus(incorrect_return=True)
                    else:
                        log.exception(f"米游币任务 - 阅读: 请求失败")
                        return MissionStatus(network_error=True)
                if count != read_times:
                    await asyncio.sleep(plugin_config.preference.sleep_time)
            get_post_status, posts = await self.get_posts(retry)
            if not get_post_status:
                return MissionStatus(failed_getting_post=True)

        return MissionStatus(success=True)

    async def like(self, like_times: int = 10, retry: bool = True) -> MissionStatus:
        """
        点赞文章

        :param like_times: 点赞次数
        :param retry: 是否允许重试
        """
        count = 0
        get_post_status, posts = await self.get_posts(retry)
        if not get_post_status:
            return MissionStatus(failed_getting_post=True)
        while count < like_times:
            for post_id in posts:
                if count == like_times:
                    break
                try:
                    async for attempt in get_async_retry(retry):
                        with attempt:
                            headers = HEADERS_OLD.copy()
                            headers["x-rpc-device_id"] = self.account.device_id_android
                            headers["DS"] = generate_ds(platform="android")
                            async with httpx.AsyncClient() as client:
                                res = await client.post(
                                    URL_LIKE, headers=headers,
                                    json={'is_cancel': False, 'post_id': post_id},
                                    timeout=plugin_config.preference.timeout,
                                    cookies=self.account.cookies.dict(v2_stoken=True, cookie_type=True)
                                )
                            api_result = ApiResultHandler(res.json())
                            if api_result.login_expired:
                                log.info(
                                    f"米游币任务 - 点赞: 用户 {self.account.display_name} 登录失效")
                                log.debug(f"网络请求返回: {res.text}")
                                return MissionStatus(login_expired=True)
                            if api_result.invalid_ds:
                                log.info(
                                    f"米游币任务 - 点赞: 用户 {self.account.display_name} DS 校验失败")
                                log.debug(f"网络请求返回: {res.text}")
                                return MissionStatus(invalid_ds=True)
                            if api_result.message == "帖子不存在":
                                continue
                            if api_result.message != "OK":
                                raise ValueError
                            count += 1
                except tenacity.RetryError as e:
                    if is_incorrect_return(e, ValueError):
                        log.exception(f"米游币任务 - 点赞: 服务器没有正确返回")
                        log.debug(f"网络请求返回: {res.text}")
                        return MissionStatus(incorrect_return=True)
                    else:
                        log.exception(f"米游币任务 - 点赞: 请求失败")
                        return MissionStatus(network_error=True)
                if count != like_times:
                    await asyncio.sleep(plugin_config.preference.sleep_time)
            get_post_status, posts = await self.get_posts(retry)
            if not get_post_status:
                return MissionStatus(failed_getting_post=True)

        return MissionStatus(success=True)

    async def share(self, retry: bool = True):
        """
        分享文章

        :param retry: 是否允许重试
        """
        get_post_status, posts = await self.get_posts(retry)
        if not get_post_status or not posts:
            return MissionStatus(failed_getting_post=True)
        try:
            async for attempt in get_async_retry(retry):
                with attempt:
                    headers = HEADERS_OLD.copy()
                    headers["x-rpc-device_id"] = self.account.device_id_android
                    headers["DS"] = generate_ds(platform="android")
                    async with httpx.AsyncClient() as client:
                        res = await client.get(
                            URL_SHARE.format(posts[0]),
                            headers=headers,
                            timeout=plugin_config.preference.timeout,
                            cookies=self.account.cookies.dict(v2_stoken=True, cookie_type=True)
                        )
                    api_result = ApiResultHandler(res.json())
                    if api_result.login_expired:
                        log.info(
                            f"米游币任务 - 分享: 用户 {self.account.display_name} 登录失效")
                        log.debug(f"网络请求返回: {res.text}")
                        return MissionStatus(login_expired=True)
                    if api_result.invalid_ds:
                        log.info(
                            f"米游币任务 - 分享: 用户 {self.account.display_name} DS 校验失败")
                        log.debug(f"网络请求返回: {res.text}")
                        return MissionStatus(invalid_ds=True)
                    if api_result.message == "帖子不存在":
                        continue
                    if api_result.message != "OK":
                        raise ValueError
        except tenacity.RetryError as e:
            if is_incorrect_return(e, ValueError):
                log.exception(f"米游币任务 - 分享: 服务器没有正确返回")
                log.debug(f"网络请求返回: {res.text}")
                return MissionStatus(incorrect_return=True)
            else:
                log.exception(f"米游币任务 - 分享: 请求失败")
                return MissionStatus(network_error=True)
        return MissionStatus(success=True)


class GenshinImpactMission(BaseMission):
    """
    原神 米游币任务
    """
    name = "原神"
    gids = 2
    fid = 26


class HonkaiImpact3Mission(BaseMission):
    """
    崩坏3 米游币任务
    """
    name = "崩坏3"
    gids = 1
    fid = 1


class HoukaiGakuen2Mission(BaseMission):
    """
    崩坏学园2 米游币任务
    """
    name = "崩坏学园2"
    gids = 3
    fid = 30


class TearsOfThemisMission(BaseMission):
    """
    未定事件簿 米游币任务
    """
    name = "未定事件簿"
    gids = 4
    fid = 37


class StarRailMission(BaseMission):
    """
    崩坏：星穹铁道 米游币任务
    """
    name = "崩坏：星穹铁道"
    gids = 6
    fid = 52


class BBSMission(BaseMission):
    """
    大别野 米游币任务
    """
    name = "综合"
    gids = 5
    # TODO: bbs fid暂时未知


class ZenlessZoneZero(BaseMission):
    """
    绝区零 米游币任务
    """
    name = "绝区零"
    gids = 8
    # TODO: fid暂时未知


for subclass in [
    GenshinImpactMission,
    HonkaiImpact3Mission,
    HoukaiGakuen2Mission,
    TearsOfThemisMission,
    StarRailMission,
    BBSMission,
    ZenlessZoneZero
]:
    BaseMission.available_games[subclass.__name__] = subclass


async def get_missions(account: UserAccount, retry: bool = True) -> Tuple[BaseApiStatus, Optional[List[MissionData]]]:
    """
    获取米游币任务信息

    :param account: 用户账号
    :param retry: 是否允许重试
    """
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_MISSION, headers=HEADERS_MISSION,
                                           cookies=account.cookies.dict(v2_stoken=True, cookie_type=True),
                                           timeout=plugin_config.preference.timeout)
                api_result = ApiResultHandler(res.json())
                if api_result.login_expired:
                    log.info(
                        f"获取米游币任务列表: 用户 {account.display_name} 登录失效")
                    log.debug(f"网络请求返回: {res.text}")
                    return BaseApiStatus(login_expired=True), None
                mission_list: List[MissionData] = []
                for mission in api_result.data["missions"]:
                    mission_list.append(MissionData.parse_obj(mission))
                return BaseApiStatus(success=True), mission_list
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            log.exception(f"获取米游币任务列表: 服务器没有正确返回")
            log.debug(f"网络请求返回: {res.text}")
            return BaseApiStatus(incorrect_return=True), None
        else:
            log.exception("获取米游币任务列表: 请求失败")
            return BaseApiStatus(network_error=True), None


async def get_missions_state(account: UserAccount, retry: bool = True) -> Tuple[BaseApiStatus, Optional[MissionState]]:
    """
    获取米游币任务完成情况

    :param account: 用户账号
    :param retry: 是否允许重试
    """
    get_missions_status, missions = await get_missions(account)
    if not get_missions_status:
        return get_missions_status, None
    try:
        async for attempt in get_async_retry(retry):
            with attempt:
                async with httpx.AsyncClient() as client:
                    res = await client.get(URL_MISSION_STATE, headers=HEADERS_MISSION,
                                           cookies=account.cookies.dict(v2_stoken=True, cookie_type=True),
                                           timeout=plugin_config.preference.timeout)
                api_result = ApiResultHandler(res.json())
                if api_result.login_expired:
                    log.info(
                        f"获取米游币任务完成情况: 用户 {account.display_name} 登录失效")
                    log.debug(f"网络请求返回: {res.text}")
                    return BaseApiStatus(login_expired=True), None
                state_dict = {}
                for mission in missions:
                    try:
                        current = list(filter(lambda state: state["mission_key"] == mission.mission_key,
                                              api_result.data["states"]))[0]["happened_times"]
                        state_dict.setdefault(mission.mission_key, (mission, current))
                    except IndexError:
                        state_dict.setdefault(mission.mission_key, (mission, 0))
                return BaseApiStatus(success=True), MissionState(state_dict=state_dict,
                                                                 current_myb=api_result.data["total_points"])
    except tenacity.RetryError as e:
        if is_incorrect_return(e):
            log.exception("获取米游币任务完成情况: 服务器没有正确返回")
            log.debug(f"网络请求返回: {res.text}")
            return BaseApiStatus(incorrect_return=True), None
        else:
            log.exception("获取米游币任务完成情况: 请求失败")
            return BaseApiStatus(network_error=True), None
