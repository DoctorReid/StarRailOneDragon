import os
from datetime import time, timedelta, datetime
from pathlib import Path
from typing import Union, Optional, Tuple, Any, Dict, TYPE_CHECKING

from pydantic import BaseModel, BaseSettings, validator

from ..model.common import data_path

if TYPE_CHECKING:
    IntStr = Union[int, str]

__all__ = ["plugin_config_path", "Preference",
           "GoodListImageConfig", "SaltConfig", "DeviceConfig", "PluginConfig", "PluginEnv", "plugin_config",
           "plugin_env"]

plugin_config_path = data_path / "configV2.json"


class Preference(BaseModel):
    """
    偏好设置
    """
    github_proxy: Optional[str] = "https://mirror.ghproxy.com/"
    """GitHub加速代理 最终会拼接在原GitHub链接前面"""
    enable_connection_test: bool = True
    """是否开启连接测试"""
    connection_test_interval: Optional[float] = 30
    """连接测试间隔（单位：秒）"""
    timeout: float = 10
    """网络请求超时时间（单位：秒）"""
    max_retry_times: Optional[int] = 3
    """最大网络请求重试次数"""
    retry_interval: float = 2
    """网络请求重试间隔（单位：秒）（除兑换请求外）"""
    timezone: Optional[str] = "Asia/Shanghai"
    """兑换时所用的时区"""
    exchange_thread_count: int = 2
    """兑换线程数"""
    exchange_latency: Tuple[float, float] = (0, 0.5)
    """同一线程下，每个兑换请求之间的间隔时间"""
    exchange_duration: float = 5
    """兑换持续时间随机范围（单位：秒）"""
    enable_log_output: bool = True
    """是否保存日志"""
    log_head: str = ""
    '''日志开头字符串(只有把插件放进plugins目录手动加载时才需要设置)'''
    log_path: Optional[Path] = data_path / "mystool.log"
    """日志保存路径"""
    log_rotation: Union[str, int, time, timedelta] = "1 week"
    '''日志保留时长(需要按照格式设置)'''
    plugin_name: str = "nonebot_plugin_mystool"
    '''插件名(为模块名字，或于plugins目录手动加载时的目录名)'''
    encoding: str = "utf-8"
    '''文件读写编码'''
    max_user: int = 0
    '''支持最多用户数'''
    add_friend_accept: bool = True
    '''是否自动同意好友申请'''
    add_friend_welcome: bool = True
    '''用户添加机器人为好友以后，是否发送使用指引信息'''
    command_start: str = ""
    '''插件内部命令头(若为""空字符串则不启用)'''
    sleep_time: float = 2
    '''任务操作冷却时间(如米游币任务)'''
    plan_time: str = "00:30"
    '''每日自动签到和米游社任务的定时任务执行时间，格式为HH:MM'''
    resin_interval: int = 60
    '''每次检查原神便笺间隔，单位为分钟'''
    global_geetest: bool = True
    '''是否开启使用全局极验Geetest，默认开启'''
    geetest_url: Optional[str]
    '''极验Geetest人机验证打码接口URL'''
    geetest_params: Optional[Dict[str, Any]] = None
    '''极验Geetest人机验证打码API发送的参数（除gt，challenge外）'''
    geetest_json: Optional[Dict[str, Any]] = {
        "gt": "{gt}",
        "challenge": "{challenge}"
    }
    '''极验Geetest人机验证打码API发送的JSON数据 `{gt}`, `{challenge}` 为占位符'''
    override_device_and_salt: bool = False
    """是否读取插件数据文件中的 device_config 设备配置 和 salt_config 配置而不是默认配置（一般情况不建议开启）"""
    enable_blacklist: bool = False
    """是否启用用户黑名单"""
    blacklist_path: Optional[Path] = data_path / "blacklist.txt"
    """用户黑名单文件路径"""
    enable_whitelist: bool = False
    """是否启用用户白名单"""
    whitelist_path: Optional[Path] = data_path / "whitelist.txt"
    """用户白名单文件路径"""
    enable_admin_list: bool = False
    """是否启用管理员名单"""
    admin_list_path: Optional[Path] = data_path / "admin_list.txt"
    """管理员名单文件路径"""
    game_token_app_id: str = "1"
    """米游社二维码登录的应用标识符（可用的任何值都没有区别，但是必须传递此参数）"""
    qrcode_query_interval: float = 1
    """检查米游社登录二维码扫描情况的请求间隔（单位：秒）"""
    qrcode_wait_time: float = 120
    """等待米游社登录二维码扫描的最长时间（单位：秒）"""

    @validator("log_path", allow_reuse=True)
    def _(cls, v: Optional[Path]):
        absolute_path = v.absolute()
        if not os.path.exists(absolute_path) or not os.path.isfile(absolute_path):
            absolute_parent = absolute_path.parent
            try:
                os.makedirs(absolute_parent, exist_ok=True)
            except PermissionError:
                logger.warning(f"程序没有创建日志目录 {absolute_parent} 的权限")
        elif not os.access(absolute_path, os.W_OK):
            logger.warning(f"程序没有写入日志文件 {absolute_path} 的权限")
        return v

    @property
    def notice_time(self) -> bool:
        now_hour = datetime.now().hour
        now_minute = datetime.now().minute
        set_time = "20:00"
        notice_time = int(set_time[:2]) * 60 + int(set_time[3:])
        start_time = notice_time - self.resin_interval
        end_time = notice_time + self.resin_interval
        return start_time <= (now_hour * 60 + now_minute) % (24 * 60) <= end_time


class GoodListImageConfig(BaseModel):
    """
    商品列表输出图片设置
    """
    ICON_SIZE: Tuple[int, int] = (600, 600)
    '''商品预览图在最终结果图中的大小'''
    WIDTH: int = 2000
    '''最终结果图宽度'''
    PADDING_ICON: int = 0
    '''展示图与展示图之间的间隙 高'''
    PADDING_TEXT_AND_ICON_Y: int = 125
    '''文字顶部与展示图顶部之间的距离 高'''
    PADDING_TEXT_AND_ICON_X: int = 10
    '''文字与展示图之间的横向距离 宽'''
    FONT_PATH: Union[Path, str, None] = None
    '''
    字体文件路径(若使用计算机已经安装的字体，直接填入字体名称，若为None则自动下载字体)

    开源字体 Source Han Sans 思源黑体
    https://github.com/adobe-fonts/source-han-sans
    '''
    FONT_SIZE: int = 50
    '''字体大小'''
    SAVE_PATH: Path = data_path
    '''商品列表图片缓存目录'''
    MULTI_PROCESS: bool = True
    '''是否使用多进程生成图片（如果生成图片时崩溃，可尝试关闭此选项）'''


class SaltConfig(BaseModel):
    """
    生成Headers - DS所用salt值，非必要请勿修改
    """
    SALT_IOS: str = "9ttJY72HxbjwWRNHJvn0n2AYue47nYsK"
    '''LK2 - 生成Headers iOS DS所需的salt'''
    SALT_ANDROID: str = "BIPaooxbWZW02fGHZL1If26mYCljPgst"
    '''K2 - 生成Headers Android DS所需的salt'''
    SALT_DATA: str = "t0qEgfub6cvueAPgR5m9aQWWVciEer7v"
    '''6X - Android 设备传入content生成 DS 所需的 salt'''
    SALT_PARAMS: str = "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs"
    '''4X - Android 设备传入url参数生成 DS 所需的 salt'''
    SALT_PROD: str = "JwYDpKvLj6MrMqqYU6jTKF17KNO2PXoS"
    '''PROD - 账号相关'''

    class Config(Preference.Config):
        pass


class DeviceConfig(BaseModel):
    """
    设备信息
    Headers所用的各种数据，非必要请勿修改
    """
    USER_AGENT_MOBILE: str = ("Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) "
                              "AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.55.1")
    '''移动端 User-Agent(Mozilla UA)'''
    USER_AGENT_PC: str = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) "
                          "Version/16.0 Safari/605.1.15")
    '''桌面端 User-Agent(Mozilla UA)'''
    USER_AGENT_OTHER: str = "Hyperion/275 CFNetwork/1402.0.8 Darwin/22.2.0"
    '''获取用户 ActionTicket 时Headers所用的 User-Agent'''
    USER_AGENT_ANDROID: str = ("Mozilla/5.0 (Linux; Android 11; MI 8 SE Build/RQ3A.211001.001; wv) AppleWebKit/537.36 "
                               "(KHTML, like Gecko) Version/4.0 Chrome/104.0.5112.97 Mobile Safari/537.36 "
                               "miHoYoBBS/2.55.1")
    '''安卓端 User-Agent(Mozilla UA)'''
    USER_AGENT_ANDROID_OTHER: str = "okhttp/4.9.3"
    '''安卓端 User-Agent(专用于米游币任务等)'''
    USER_AGENT_WIDGET: str = "WidgetExtension/231 CFNetwork/1390 Darwin/22.0.0"
    '''iOS 小组件 User-Agent(原神实时便笺)'''

    X_RPC_DEVICE_MODEL_MOBILE: str = "iPhone10,2"
    '''移动端 x-rpc-device_model'''
    X_RPC_DEVICE_MODEL_PC: str = "OS X 10.15.7"
    '''桌面端 x-rpc-device_model'''
    X_RPC_DEVICE_MODEL_ANDROID: str = "MI 8 SE"
    '''安卓端 x-rpc-device_model'''

    X_RPC_DEVICE_NAME_MOBILE: str = "iPhone"
    '''移动端 x-rpc-device_name'''
    X_RPC_DEVICE_NAME_PC: str = "Microsoft Edge 103.0.1264.62"
    '''桌面端 x-rpc-device_name'''
    X_RPC_DEVICE_NAME_ANDROID: str = "Xiaomi MI 8 SE"
    '''安卓端 x-rpc-device_name'''

    X_RPC_SYS_VERSION: str = "16.2"
    '''Headers所用的 x-rpc-sys_version'''
    X_RPC_SYS_VERSION_ANDROID: str = "11"
    '''安卓端 x-rpc-sys_version'''

    X_RPC_CHANNEL: str = "appstore"
    '''Headers所用的 x-rpc-channel'''
    X_RPC_CHANNEL_ANDROID: str = "miyousheluodi"
    '''安卓端 x-rpc-channel'''

    X_RPC_APP_VERSION: str = "2.63.1"
    '''Headers所用的 x-rpc-app_version'''
    X_RPC_PLATFORM: str = "ios"
    '''Headers所用的 x-rpc-platform'''
    UA: str = "\".Not/A)Brand\";v=\"99\", \"Microsoft Edge\";v=\"103\", \"Chromium\";v=\"103\""
    '''Headers所用的 sec-ch-ua'''
    UA_PLATFORM: str = "\"macOS\""
    '''Headers所用的 sec-ch-ua-platform'''

    class Config(Preference.Config):
        pass


class PluginConfig(BaseSettings):
    preference = Preference()
    good_list_image_config = GoodListImageConfig()


class PluginEnv(BaseSettings):
    salt_config = SaltConfig()
    device_config = DeviceConfig()

    class Config(BaseSettings.Config):
        env_prefix = "mystool_"
        env_file = '.env'


if plugin_config_path.exists() and plugin_config_path.is_file():
    plugin_config = PluginConfig.parse_file(plugin_config_path)
else:
    plugin_config = PluginConfig()
    try:
        str_data = plugin_config.json(indent=4)
        plugin_config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(plugin_config_path, "w", encoding="utf-8") as f:
            f.write(str_data)
    except (AttributeError, TypeError, ValueError, PermissionError):
        logger.exception(f"创建插件配置文件失败，请检查是否有权限读取和写入 {plugin_config_path}")
        raise
    else:
        logger.info(f"插件配置文件 {plugin_config_path} 不存在，已创建默认插件配置文件。")

# TODO: 可能产生 #271 的问题 https://github.com/Ljzd-PRO/nonebot-plugin-mystool/issues/271
# @_driver.on_startup
# def _():
#     """将 ``PluginMetadata.config`` 设为定义的插件配置对象 ``plugin_config``"""
#     plugin = nonebot.plugin.get_plugin(plugin_config.preference.plugin_name)
#     plugin.metadata.config = plugin_config


plugin_env = PluginEnv()
