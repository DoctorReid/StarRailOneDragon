"""
### 插件数据相关
"""
import json
import os
from datetime import time, timedelta
from json import JSONDecodeError
from pathlib import Path
from typing import Union, Optional, Tuple, Any, Dict, TYPE_CHECKING, AbstractSet, \
    Mapping

from pydantic import BaseModel, ValidationError, validator, Extra
from pydantic_settings import BaseSettings  # 升级到2.5需要的改造

from basic import os_utils
from basic.log_utils import log
from . import user_data
from .user_data import UserData, UserAccount

VERSION = "v1.4.0"
"""程序当前版本"""

ROOT_PATH = Path(os_utils.get_path_under_work_dir('config', 'mystool'))
'''NoneBot2 机器人根目录'''

DATA_PATH = ROOT_PATH / "data" / "nonebot-plugin-mystool"
'''插件数据保存目录'''

PLUGIN_DATA_PATH = DATA_PATH / "plugin_data.json"
"""插件数据文件默认路径"""

DELETED_USERS_PATH = DATA_PATH / "deletedUsers"
"""已删除用户数据文件默认备份目录"""

if TYPE_CHECKING:
    IntStr = Union[int, str]
    DictStrAny = Dict[str, Any]
    AbstractSetIntStr = AbstractSet[IntStr]
    MappingIntStrAny = Mapping[IntStr, Any]


class Preference(BaseSettings, extra=Extra.ignore):
    """
    偏好设置
    """
    github_proxy: Optional[str] = "https://ghproxy.com/"
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
    log_path: Optional[Path] = DATA_PATH / "mystool.log"
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
    geetest_url: Optional[str] = None
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
    blacklist_path: Optional[Path] = DATA_PATH / "blacklist.txt"
    """用户黑名单文件路径"""
    enable_whitelist: bool = False
    """是否启用用户白名单"""
    whitelist_path: Optional[Path] = DATA_PATH / "whitelist.txt"
    """用户白名单文件路径"""

    @validator("log_path", allow_reuse=True)
    def _(cls, v: Optional[Path]):
        absolute_path = v.absolute()
        if not os.path.exists(absolute_path) or not os.path.isfile(absolute_path):
            absolute_parent = absolute_path.parent
            try:
                os.makedirs(absolute_parent, exist_ok=True)
            except PermissionError:
                log.warning(f"程序没有创建日志目录 {absolute_parent} 的权限")
        elif not os.access(absolute_path, os.W_OK):
            log.warning(f"程序没有写入日志文件 {absolute_path} 的权限")
        return v


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
    SAVE_PATH: Path = DATA_PATH
    '''商品列表图片缓存目录'''
    MULTI_PROCESS: bool = True
    '''是否使用多进程生成图片（如果生成图片时崩溃，可尝试关闭此选项）'''


class SaltConfig(BaseSettings):
    """
    生成Headers - DS所用salt值，非必要请勿修改
    """
    SALT_IOS: str = "F6tsiCZEIcL9Mor64OXVJEKRRQ6BpOZa"
    '''LK2 - 生成Headers iOS DS所需的salt'''
    SALT_ANDROID: str = "xc1lzZFOBGU0lz8ZkPgcrWZArZzEVMbA"
    '''K2 - 生成Headers Android DS所需的salt'''
    SALT_DATA: str = "t0qEgfub6cvueAPgR5m9aQWWVciEer7v"
    '''6X - Android 设备传入content生成 DS 所需的 salt'''
    SALT_PARAMS: str = "xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs"
    '''4X - Android 设备传入url参数生成 DS 所需的 salt'''
    SALT_PROD: str = "JwYDpKvLj6MrMqqYU6jTKF17KNO2PXoS"
    '''PROD - 账号相关'''


class DeviceConfig(BaseSettings):
    """
    设备信息
    Headers所用的各种数据，非必要请勿修改
    """
    USER_AGENT_MOBILE: str = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) miHoYoBBS/2.55.1"
    '''移动端 User-Agent(Mozilla UA)'''
    USER_AGENT_PC: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15"
    '''桌面端 User-Agent(Mozilla UA)'''
    USER_AGENT_OTHER: str = "Hyperion/275 CFNetwork/1402.0.8 Darwin/22.2.0"
    '''获取用户 ActionTicket 时Headers所用的 User-Agent'''
    USER_AGENT_ANDROID: str = "Mozilla/5.0 (Linux; Android 11; MI 8 SE Build/RQ3A.211001.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/104.0.5112.97 Mobile Safari/537.36 miHoYoBBS/2.55.1"
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

    X_RPC_APP_VERSION: str = "2.55.1"
    '''Headers所用的 x-rpc-app_version'''
    X_RPC_PLATFORM: str = "ios"
    '''Headers所用的 x-rpc-platform'''
    UA: str = "\".Not/A)Brand\";v=\"99\", \"Microsoft Edge\";v=\"103\", \"Chromium\";v=\"103\""
    '''Headers所用的 sec-ch-ua'''
    UA_PLATFORM: str = "\"macOS\""
    '''Headers所用的 sec-ch-ua-platform'''


class PluginData(BaseModel):
    version: str = VERSION
    """创建插件数据文件时的版本号"""
    preference: Preference = Preference()
    """偏好设置"""
    salt_config: SaltConfig = SaltConfig()
    """生成Headers - DS所用salt值"""
    device_config: DeviceConfig = DeviceConfig()
    """设备信息"""
    good_list_image_config: GoodListImageConfig = GoodListImageConfig()
    """商品列表输出图片设置"""
    user_bind: Optional[Dict[str, str]] = {}
    '''不同NoneBot适配器平台的用户数据绑定关系（如QQ聊天和QQ频道）(空用户数据:被绑定用户数据)'''
    users: Dict[str, UserData] = {}
    '''所有用户数据'''

    def do_user_bind(self, src: str = None, dst: str = None, write: bool = False):
        """
        执行用户数据绑定同步，将src指向dst的用户数据，即src处的数据将会被dst处的数据对象替换

        :param src: 源用户数据，为空则读取 self.user_bind 并执行全部绑定
        :param dst: 目标用户数据，为空则读取 self.user_bind 并执行全部绑定
        :param write: 是否写入插件数据文件
        """
        if None in [src, dst]:
            for x, y in self.user_bind.items():
                try:
                    self.users[x] = self.users[y]
                except KeyError:
                    log.error(f"用户数据绑定失败，目标用户 {y} 不存在")
        else:
            try:
                self.user_bind[src] = dst
                self.users[src] = self.users[dst]
            except KeyError:
                log.error(f"用户数据绑定失败，目标用户 {dst} 不存在")
            else:
                if write:
                    write_plugin_data()

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.do_user_bind(write=True)

    class Config:
        json_encoders = UserAccount.Config.json_encoders


class PluginDataManager:
    plugin_data = PluginData()
    """加载出的插件数据对象"""
    device_config: DeviceConfig
    """加载出的设备信息数据对象"""

    @classmethod
    def load_plugin_data(cls):
        """
        加载插件数据文件
        """
        if os.path.exists(PLUGIN_DATA_PATH) and os.path.isfile(PLUGIN_DATA_PATH):
            try:
                with open(PLUGIN_DATA_PATH, "r") as f:
                    plugin_data_dict = json.load(f)
                    override_device_and_salt = plugin_data_dict["preference"].get("override_device_and_salt")
                    # 读取 preference.override_device_and_salt 时，如果没有该配置，则默认为 False
                    override_device_and_salt = override_device_and_salt \
                        if override_device_and_salt is not None else False
                    device_config_dict = plugin_data_dict["device_config"]

                # 先读取设备信息配置，因为之后导入其他代码时部分变量如Headers将会使用到，一旦完成导入，再修改设备信息配置将不会生效
                if override_device_and_salt:
                    cls.device_config = DeviceConfig.parse_obj(device_config_dict)
                else:
                    cls.device_config = DeviceConfig()

                # 读取完整的插件数据
                plugin_data_from_file = PluginData.parse_obj(plugin_data_dict)
                for attr in plugin_data_from_file.__fields__:
                    cls.plugin_data.__setattr__(attr, plugin_data_from_file.__getattribute__(attr))
            except (ValidationError, JSONDecodeError):
                log.exception(f"读取插件数据文件失败，请检查插件数据文件 {PLUGIN_DATA_PATH} 格式是否正确")
                raise
            except:
                log.exception(
                    f"读取插件数据文件失败，请检查插件数据文件 {PLUGIN_DATA_PATH} 是否存在且有权限读取和写入")
                raise
            else:
                if not cls.plugin_data.preference.override_device_and_salt:
                    default_device_config = DeviceConfig()
                    default_salt_config = SaltConfig()
                    if cls.plugin_data.device_config != default_device_config \
                            or cls.plugin_data.salt_config != default_salt_config:
                        cls.plugin_data.device_config = default_device_config
                        cls.plugin_data.salt_config = default_salt_config
                        log.warning("检测到设备信息配置 device_config 或 salt_config 使用了非默认值，"
                                       "如果你修改过这些配置，需要设置 preference.override_device_and_salt 为 True 以覆盖默认值并生效。"
                                       "如果继续，将可能保存默认值到插件数据文件。")
                else:
                    log.info("已开启覆写 device_config 和 salt_config，将读取插件数据文件中的配置以覆写默认配置")
        else:
            plugin_data_from_file = PluginData()
            cls.device_config = DeviceConfig()
            try:
                str_data = plugin_data_from_file.model_dump_json(indent=4)
                with open(PLUGIN_DATA_PATH, "w", encoding="utf-8") as f:
                    f.write(str_data)
            except (AttributeError, TypeError, ValueError, PermissionError):
                log.exception(f"创建插件数据文件失败，请检查是否有权限读取和写入 {PLUGIN_DATA_PATH}")
                raise
            log.info(f"插件数据文件 {PLUGIN_DATA_PATH} 不存在，已创建默认插件数据文件。")


def write_plugin_data(data: PluginData = None):
    """
    写入插件数据文件

    :param data: 配置对象
    :return: 是否成功
    """
    if data is None:
        data = PluginDataManager.plugin_data
    try:
        str_data = data.model_dump_json(indent=4)
    except (AttributeError, TypeError, ValueError):
        log.exception("数据对象序列化失败，可能是数据类型错误")
        return False
    with open(PLUGIN_DATA_PATH, "w", encoding="utf-8") as f:
        f.write(str_data)
    return True


PluginDataManager.load_plugin_data()

# 如果插件数据文件加载后，发现有用户没有UUID密钥，进行了生成，则需要保存写入
if user_data._new_uuid_in_init:
    write_plugin_data()
