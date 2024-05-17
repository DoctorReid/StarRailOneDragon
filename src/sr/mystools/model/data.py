import json
from json import JSONDecodeError
from typing import Union, Optional, Any, Dict, TYPE_CHECKING, AbstractSet, \
    Mapping, Set, Literal, List
from uuid import UUID, uuid4

from httpx import Cookies
from pydantic import BaseModel, ValidationError, validator, Field

from basic.log_utils import log as logger
from .._version import __version__
from ..model.common import data_path, BaseModelWithSetter, Address, BaseModelWithUpdate, Good, GameRecord

if TYPE_CHECKING:
    IntStr = Union[int, str]
    DictStrAny = Dict[str, Any]
    AbstractSetIntStr = AbstractSet[IntStr]
    MappingIntStrAny = Mapping[IntStr, Any]

__all__ = ["plugin_data_path", "BBSCookies", "UserAccount", "ExchangePlan", "ExchangeResult", "uuid4_validate",
           "UserData", "PluginData", "PluginDataManager"]

plugin_data_path = data_path / "dataV2.json"
_uuid_set: Set[str] = set()
"""已使用的用户UUID密钥集合"""
_new_uuid_in_init = False
"""插件反序列化用户数据时，是否生成了新的UUID密钥"""


class BBSCookies(BaseModelWithSetter, BaseModelWithUpdate):
    """
    米游社Cookies数据

    # 测试 is_correct() 方法

    >>> assert BBSCookies().is_correct() is False
    >>> assert BBSCookies(stuid="123", stoken="123", cookie_token="123").is_correct() is True

    # 测试 bbs_uid getter

    >>> bbs_cookies = BBSCookies()
    >>> assert not bbs_cookies.bbs_uid
    >>> assert BBSCookies(stuid="123").bbs_uid == "123"

    # 测试 bbs_uid setter

    >>> bbs_cookies.bbs_uid = "123"
    >>> assert bbs_cookies.bbs_uid == "123"

    # 检查构造函数内所用的 stoken setter

    >>> bbs_cookies = BBSCookies(stoken="abcd1234")
    >>> assert bbs_cookies.stoken_v1 and not bbs_cookies.stoken_v2
    >>> bbs_cookies = BBSCookies(stoken="v2_abcd1234==")
    >>> assert bbs_cookies.stoken_v2 and not bbs_cookies.stoken_v1
    >>> assert bbs_cookies.stoken == "v2_abcd1234=="

    # 检查 stoken setter

    >>> bbs_cookies = BBSCookies(stoken="abcd1234")
    >>> bbs_cookies.stoken = "v2_abcd1234=="
    >>> assert bbs_cookies.stoken_v2 == "v2_abcd1234=="
    >>> assert bbs_cookies.stoken_v1 == "abcd1234"

    # 检查 .dict 方法能否生成包含 stoken_2 类型的 stoken 的字典

    >>> bbs_cookies = BBSCookies()
    >>> bbs_cookies.stoken_v1 = "abcd1234"
    >>> bbs_cookies.stoken_v2 = "v2_abcd1234=="
    >>> assert bbs_cookies.dict(v2_stoken=True)["stoken"] == "v2_abcd1234=="

    # 检查是否有多余的字段

    >>> bbs_cookies = BBSCookies(stuid="123")
    >>> assert all(bbs_cookies.dict())
    >>> assert all(map(lambda x: x not in bbs_cookies, ["stoken_v1", "stoken_v2"]))

    # 测试 update 方法

    >>> bbs_cookies = BBSCookies(stuid="123")
    >>> assert bbs_cookies.update({"stuid": "456", "stoken": "abc"}) is bbs_cookies
    >>> assert bbs_cookies.stuid == "456"
    >>> assert bbs_cookies.stoken == "abc"

    >>> bbs_cookies = BBSCookies(stuid="123")
    >>> new_cookies = BBSCookies(stuid="456", stoken="abc")
    >>> assert bbs_cookies.update(new_cookies) is bbs_cookies
    >>> assert bbs_cookies.stuid == "456"
    >>> assert bbs_cookies.stoken == "abc"
    """
    stuid: Optional[str]
    """米游社UID"""
    ltuid: Optional[str]
    """米游社UID"""
    account_id: Optional[str]
    """米游社UID"""
    login_uid: Optional[str]
    """米游社UID"""

    stoken_v1: Optional[str]
    """保存stoken_v1，方便后续使用"""
    stoken_v2: Optional[str]
    """保存stoken_v2，方便后续使用"""

    cookie_token: Optional[str]
    login_ticket: Optional[str]
    ltoken: Optional[str]
    mid: Optional[str]

    def __init__(self, **data: Any):
        super().__init__(**data)
        stoken = data.get("stoken")
        if stoken:
            self.stoken = stoken

    def is_correct(self) -> bool:
        """判断是否为正确的Cookies"""
        if self.bbs_uid and self.stoken and self.cookie_token:
            return True
        else:
            return False

    @property
    def bbs_uid(self):
        """
        获取米游社UID
        """
        uid = None
        for value in [self.stuid, self.ltuid, self.account_id, self.login_uid]:
            if value:
                uid = value
                break
        return uid or None

    @bbs_uid.setter
    def bbs_uid(self, value: str):
        self.stuid = value
        self.ltuid = value
        self.account_id = value
        self.login_uid = value

    @property
    def stoken(self):
        """
        获取stoken
        :return: 优先返回 self.stoken_v1
        """
        if self.stoken_v1:
            return self.stoken_v1
        elif self.stoken_v2:
            return self.stoken_v2
        else:
            return None

    @stoken.setter
    def stoken(self, value):
        if value.startswith("v2_"):
            self.stoken_v2 = value
        else:
            self.stoken_v1 = value

    def update(self, cookies: Union[Dict[str, str], Cookies, "BBSCookies"]):
        """
        更新Cookies
        """
        if not isinstance(cookies, BBSCookies):
            self.stoken = cookies.get("stoken") or self.stoken
            self.bbs_uid = cookies.get("bbs_uid") or self.bbs_uid
            cookies.pop("stoken", None)
            cookies.pop("bbs_uid", None)
        return super().update(cookies)

    def dict(self, *,
             include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']] = None,
             exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']] = None,
             by_alias: bool = False,
             skip_defaults: Optional[bool] = None, exclude_unset: bool = False, exclude_defaults: bool = False,
             exclude_none: bool = False, v2_stoken: bool = False,
             cookie_type: bool = False) -> 'DictStrAny':
        """
        获取Cookies字典

        v2_stoken: stoken 字段是否使用 stoken_v2
        cookie_type: 是否返回符合Cookie类型的字典（没有自定义的stoken_v1、stoken_v2键）
        """
        # 保证 stuid, ltuid 等字段存在
        self.bbs_uid = self.bbs_uid
        cookies_dict = super().dict(include=include, exclude=exclude, by_alias=by_alias, skip_defaults=skip_defaults,
                                    exclude_unset=exclude_unset, exclude_defaults=exclude_defaults,
                                    exclude_none=exclude_none)
        if v2_stoken and self.stoken_v2:
            cookies_dict["stoken"] = self.stoken_v2
        else:
            cookies_dict["stoken"] = self.stoken_v1

        if cookie_type:
            # 去除自定义的 stoken_v1, stoken_v2 字段
            cookies_dict.pop("stoken_v1")
            cookies_dict.pop("stoken_v2")

            # 去除空的字段
            empty_key = set()
            for key, value in cookies_dict.items():
                if not value:
                    empty_key.add(key)
            [cookies_dict.pop(key) for key in empty_key]

        return cookies_dict


class UserAccount(BaseModelWithSetter):
    """
    米游社账户数据

    >>> user_account = UserAccount(
    >>>     cookies=BBSCookies(),
    >>>     device_id_ios="DBB8886C-C88A-4E12-A407-BE295E95E084",
    >>>     device_id_android="64561CE4-5F43-41D7-B92F-41CEFABC7ABF"
    >>> )
    >>> assert isinstance(user_account, UserAccount)
    >>> user_account.bbs_uid = "123"
    >>> assert user_account.bbs_uid == "123"
    """
    phone_number: Optional[str]
    """手机号"""
    cookies: BBSCookies
    """Cookies"""
    address: Optional[Address]
    """收货地址"""

    device_id_ios: str
    """iOS设备用 deviceID"""
    device_id_android: str
    """安卓设备用 deviceID"""
    device_fp: Optional[str]
    """iOS设备用 deviceFp"""
    enable_mission: bool = True
    '''是否开启米游币任务计划'''
    enable_game_sign: bool = True
    '''是否开启米游社游戏签到计划'''
    enable_resin: bool = True
    '''是否开启便笺提醒'''
    platform: Literal["ios", "android"] = "ios"
    '''设备平台'''
    mission_games: List[str] = ["BBSMission"]
    '''在哪些板块执行米游币任务计划 为 BaseMission 子类名称'''
    user_stamina_threshold: int = 240
    '''崩铁便笺体力提醒阈值，0为一直提醒'''
    user_resin_threshold: int = 160
    '''原神便笺树脂提醒阈值，0为一直提醒'''

    def __init__(self, **data: Any):
        if not data.get("device_id_ios") or not data.get("device_id_android"):
            from ..utils import generate_device_id
            if not data.get("device_id_ios"):
                data.setdefault("device_id_ios", generate_device_id())
            if not data.get("device_id_android"):
                data.setdefault("device_id_android", generate_device_id())

        super().__init__(**data)

    @property
    def bbs_uid(self):
        """
        获取米游社UID
        """
        return self.cookies.bbs_uid

    @bbs_uid.setter
    def bbs_uid(self, value: str):
        self.cookies.bbs_uid = value

    @property
    def display_name(self):
        """
        显示名称
        """
        from ..utils.common import blur_phone
        return f"{self.bbs_uid}({blur_phone(self.phone_number)})" if self.phone_number else self.bbs_uid


class ExchangePlan(BaseModel):
    """
    兑换计划数据类
    """

    good: Good
    """商品"""
    address: Optional[Address]
    """地址ID"""
    account: UserAccount
    """米游社账号"""
    game_record: Optional[GameRecord]
    """商品对应的游戏的玩家账号"""

    def __hash__(self):
        return hash(
            (
                self.good.goods_id,
                self.good.time,
                self.address.id if self.address else None,
                self.account.bbs_uid,
                self.game_record.game_role_id if self.game_record else None
            )
        )

    class CustomDict(dict):
        _hash: int

        def __hash__(self):
            return self._hash

    def dict(
            self,
            *,
            include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']] = None,
            exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']] = None,
            by_alias: bool = False,
            skip_defaults: Optional[bool] = None,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
    ) -> 'DictStrAny':
        """
        重写 dict 方法，使其返回的 dict 可以被 hash
        """
        normal_dict = super().dict(include=include, exclude=exclude, by_alias=by_alias, skip_defaults=skip_defaults,
                                   exclude_unset=exclude_unset, exclude_defaults=exclude_defaults,
                                   exclude_none=exclude_none)
        hashable_dict = ExchangePlan.CustomDict(normal_dict)
        hashable_dict._hash = hash(self)
        return hashable_dict


class ExchangeResult(BaseModel):
    """
    兑换结果数据类
    """
    result: bool
    """兑换结果"""
    return_data: dict
    """返回数据"""
    plan: ExchangePlan
    """兑换计划"""


def uuid4_validate(v):
    """
    验证UUID是否为合法的UUIDv4

    :param v: UUID
    """
    try:
        UUID(v, version=4)
    except Exception:
        return False
    else:
        return True


class UserData(BaseModelWithSetter):
    """
    用户数据类

    >>> userdata = UserData()
    >>> hash(userdata)
    """
    enable_notice: bool = True
    """是否开启通知"""
    enable_weibo: bool = False
    '''是否开启微博兑换码功能'''
    weibo_cookie: str = ""
    '''微博查询活动签到用的 cookie'''
    weibo_params: str = ""
    '''微博查询活动签到用的 params'''
    geetest_url: Optional[str]
    '''极验Geetest人机验证打码接口URL'''
    geetest_params: Optional[Dict[str, Any]] = None
    '''极验Geetest人机验证打码API发送的参数（除gt，challenge外）'''
    uuid: Optional[str] = None
    """用户UUID密钥，用于不同NoneBot适配器平台之间的数据同步，因此不可泄露"""
    qq_guild: Optional[Dict[str, int]] = {}
    """储存用户所在的QQ频道ID {用户ID : 频道ID}"""
    qq_guilds: Optional[Dict[str, List[int]]] = Field(default={}, exclude=True)
    """旧版（v2.1.0 之前）储存用户所在的QQ频道ID {用户ID : [频道ID]}"""
    exchange_plans: Union[Set[ExchangePlan], List[ExchangePlan]] = set()
    """兑换计划列表"""
    accounts: Dict[str, UserAccount] = {}
    """储存一些已绑定的账号数据"""

    @validator("uuid")
    def uuid_validator(cls, v):
        """
        验证UUID是否为合法的UUIDv4

        :raises ValueError: UUID格式错误，不是合法的UUIDv4
        """
        if v is None and not uuid4_validate(v):
            raise ValueError("UUID格式错误，不是合法的UUIDv4")

    def __init__(self, **data: Any):
        global _new_uuid_in_init
        super().__init__(**data)

        exchange_plans = self.exchange_plans
        self.exchange_plans = set()
        for plan in exchange_plans:
            plan = ExchangePlan.parse_obj(plan)
            self.exchange_plans.add(plan)

        if self.uuid is None:
            new_uuid = uuid4()
            while str(new_uuid) in _uuid_set:
                new_uuid = uuid4()
            self.uuid = str(new_uuid)
            _new_uuid_in_init = True
        _uuid_set.add(self.uuid)

        # 读取旧版配置中的 qq_guilds 信息，对每个账号取第一个 GuildID 值以生成新的 qq_guild Dict
        if not self.qq_guild:
            self.qq_guild = {k: v[0] for k, v in filter(lambda x: x[1], self.qq_guilds.items())}

    def __hash__(self):
        return hash(self.uuid)


class PluginData(BaseModel):
    version: str = __version__
    """创建插件数据文件时的版本号"""
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
                    logger.error(f"用户数据绑定失败，目标用户 {y} 不存在")
        else:
            try:
                self.user_bind[src] = dst
                self.users[src] = self.users[dst]
            except KeyError:
                logger.error(f"用户数据绑定失败，目标用户 {dst} 不存在")
            else:
                if write:
                    PluginDataManager.write_plugin_data()

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.do_user_bind(write=True)

    class Config:
        json_encoders = UserAccount.Config.json_encoders


class PluginDataManager:
    plugin_data: Optional[PluginData] = None
    """加载出的插件数据对象"""

    @classmethod
    def load_plugin_data(cls):
        """
        加载插件数据文件
        """
        if plugin_data_path.exists() and plugin_data_path.is_file():
            try:
                with open(plugin_data_path, "r") as f:
                    plugin_data_dict = json.load(f)
                # 读取完整的插件数据
                cls.plugin_data = PluginData.parse_obj(plugin_data_dict)
            except (ValidationError, JSONDecodeError):
                logger.exception(f"读取插件数据文件失败，请检查插件数据文件 {plugin_data_path} 格式是否正确")
                raise
            except Exception:
                logger.exception(
                    f"读取插件数据文件失败，请检查插件数据文件 {plugin_data_path} 是否存在且有权限读取和写入")
                raise
        else:
            cls.plugin_data = PluginData()
            try:
                str_data = cls.plugin_data.json(indent=4)
                plugin_data_path.parent.mkdir(parents=True, exist_ok=True)
                with open(plugin_data_path, "w", encoding="utf-8") as f:
                    f.write(str_data)
            except (AttributeError, TypeError, ValueError, PermissionError):
                logger.exception(f"创建插件数据文件失败，请检查是否有权限读取和写入 {plugin_data_path}")
                raise
            else:
                logger.info(f"插件数据文件 {plugin_data_path} 不存在，已创建默认插件数据文件。")

    @classmethod
    def write_plugin_data(cls):
        """
        写入插件数据文件

        :return: 是否成功
        """
        try:
            str_data = cls.plugin_data.json(indent=4)
        except (AttributeError, TypeError, ValueError):
            logger.exception("数据对象序列化失败，可能是数据类型错误")
            return False
        else:
            with open(plugin_data_path, "w", encoding="utf-8") as f:
                f.write(str_data)
            return True


PluginDataManager.load_plugin_data()

# 如果插件数据文件加载后，发现有用户没有UUID密钥，进行了生成，则需要保存写入
if _new_uuid_in_init:
    PluginDataManager.write_plugin_data()
