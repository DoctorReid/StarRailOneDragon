"""
### 用户数据相关
"""
from typing import List, Union, Optional, Any, Dict, Set, TYPE_CHECKING, AbstractSet, \
    Mapping, Literal
from uuid import uuid4, UUID

from httpx import Cookies
from pydantic import BaseModel, validator

from .data_model import BaseModelWithSetter, Good, Address, GameRecord, BaseModelWithUpdate

if TYPE_CHECKING:
    IntStr = Union[int, str]
    DictStrAny = Dict[str, Any]
    AbstractSetIntStr = AbstractSet[IntStr]
    MappingIntStrAny = Mapping[IntStr, Any]


class BBSCookies(BaseModelWithSetter, BaseModelWithUpdate):
    """
    米游社Cookies数据
    """
    stuid: Optional[str] = None
    """米游社UID"""
    ltuid: Optional[str] = None
    """米游社UID"""
    account_id: Optional[str] = None
    """米游社UID"""
    login_uid: Optional[str] = None
    """米游社UID"""

    stoken_v1: Optional[str] = None
    """保存stoken_v1，方便后续使用"""
    stoken_v2: Optional[str] = None
    """保存stoken_v2，方便后续使用"""

    cookie_token: Optional[str] = None
    login_ticket: Optional[str] = None
    ltoken: Optional[str] = None
    mid: Optional[str] = None

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
             exclude_unset: bool = False, exclude_defaults: bool = False,
             exclude_none: bool = False, v2_stoken: bool = False,
             cookie_type: bool = False) -> 'DictStrAny':
        """
        获取Cookies字典

        v2_stoken: stoken 字段是否使用 stoken_v2
        cookie_type: 是否返回符合Cookie类型的字典（没有自定义的stoken_v1、stoken_v2键）
        """
        # 保证 stuid, ltuid 等字段存在
        self.bbs_uid = self.bbs_uid
        cookies_dict = super().model_dump(include=include, exclude=exclude, by_alias=by_alias,
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

    """
    phone_number: Optional[str]
    """手机号"""
    cookies: BBSCookies
    """Cookies"""
    address: Optional[Address] = None
    """收货地址"""

    device_id_ios: Optional[str] = None
    """iOS设备用 deviceID"""
    device_id_android: Optional[str] = None
    """安卓设备用 deviceID"""
    device_fp: Optional[str] = None
    """iOS设备用 deviceFp"""

    enable_mission: bool = True
    '''是否开启米游币任务计划'''
    enable_game_sign: bool = True
    '''是否开启米游社游戏签到计划'''
    enable_resin: bool = True
    '''是否开启便笺提醒'''
    platform: Literal["ios", "android"] = "ios"
    '''设备平台'''
    mission_games: Set[type] = {}
    '''在哪些板块执行米游币任务计划'''
    user_stamina_threshold: int = 180
    '''崩铁便笺体力提醒阈值，0为一直提醒'''
    user_resin_threshold: int = 160
    '''原神便笺树脂提醒阈值，0为一直提醒'''

    def __init__(self, **data: Any):
        if not data.get("device_id_ios") or not data.get("device_id_android"):
            from .utils import generate_device_id
            if not data.get("device_id_ios"):
                data.setdefault("device_id_ios", generate_device_id())
            if not data.get("device_id_android"):
                data.setdefault("device_id_android", generate_device_id())

        from . import myb_missions_api

        mission_games_param: Union[List[str], Set[type], None] = data.pop(
            "mission_games") if "mission_games" in data else None
        super().__init__(**data)

        if isinstance(mission_games_param, list):
            self.mission_games = set(map(lambda x: getattr(myb_missions_api, x), mission_games_param))
        elif isinstance(mission_games_param, set):
            self.mission_games = mission_games_param
        elif mission_games_param is None:
            self.mission_games = {myb_missions_api.BBSMission}

    class Config:
        json_encoders = {type: lambda v: v.__name__}

    @validator("mission_games")
    def mission_games_validator(cls, v):
        from .myb_missions_api import BaseMission
        if not all(issubclass(game, BaseMission) for game in v):
            raise ValueError("UserAccount.mission_games 必须是 BaseMission 的子类")

    @property
    def bbs_uid(self):
        """
        获取米游社UID
        """
        return self.cookies.bbs_uid

    @bbs_uid.setter
    def bbs_uid(self, value: str):
        self.cookies.bbs_uid = value


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
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
    ) -> 'DictStrAny':
        """
        重写 dict 方法，使其返回的 dict 可以被 hash
        """
        normal_dict = super().model_dump(include=include, exclude=exclude, by_alias=by_alias,
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


_uuid_set: Set[str] = set()
"""已使用的用户UUID密钥集合"""
_new_uuid_in_init = False
"""插件反序列化用户数据时，是否生成了新的UUID密钥"""


def uuid4_validate(v):
    """
    验证UUID是否为合法的UUIDv4

    :param v: UUID
    """
    try:
        UUID(v, version=4)
    except:
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
    uuid: Optional[str] = None
    """用户UUID密钥，用于不同NoneBot适配器平台之间的数据同步，因此不可泄露"""
    qq_guilds: Optional[Dict[str, Set[int]]] = {}
    """储存用户所在的QQ频道ID {用户ID : [频道ID]}"""
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

    def __hash__(self):
        return hash(self.uuid)
