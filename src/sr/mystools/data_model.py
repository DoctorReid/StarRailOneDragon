"""
### 米游社API的客户端调用所用的数据模型
"""
import inspect
import time
from abc import abstractmethod
from datetime import datetime
from typing import Optional, Literal, NamedTuple, no_type_check, Union, Dict, Any, TypeVar, Tuple, List

from pydantic import BaseModel


class BaseModelWithSetter(BaseModel):
    """
    可以使用@property.setter的BaseModel

    目前pydantic 1.10.7 无法使用@property.setter
    issue: https://github.com/pydantic/pydantic/issues/1577#issuecomment-790506164
    """

    @no_type_check
    def __setattr__(self, name, value):
        try:
            super().__setattr__(name, value)
        except ValueError as e:
            setters = inspect.getmembers(
                self.__class__,
                predicate=lambda x: isinstance(x, property) and x.fset is not None
            )
            for setter_name, func in setters:
                if setter_name == name:
                    object.__setattr__(self, name, value)
                    break
            else:
                raise e


class BaseModelWithUpdate(BaseModel):
    """
    可以使用update方法的BaseModel
    """
    _T = TypeVar("_T", bound=BaseModel)

    @abstractmethod
    def update(self, obj: Union[_T, Dict[str, Any]]) -> _T:
        """
        更新数据对象

        :param obj: 新的数据对象或属性字典
        :raise TypeError
        """
        if isinstance(obj, type(self)):
            obj = obj.dict()
        items = filter(lambda x: x[0] in self.__fields__, obj.items())
        for k, v in items:
            setattr(self, k, v)
        return self


class Good(BaseModelWithUpdate):
    """
    商品数据
    """
    type: int
    """为 1 时商品只有在指定时间开放兑换；为 0 时商品任何时间均可兑换"""
    next_time: Optional[int]
    """为 0 表示任何时间均可兑换或兑换已结束"""
    status: Optional[Literal["online", "not_in_sell"]]
    sale_start_time: Optional[int]
    time_by_detail: Optional[int]
    next_num: Optional[int]
    account_exchange_num: int
    """已经兑换次数"""
    account_cycle_limit: int
    """最多可兑换次数"""
    account_cycle_type: str
    """限购类型 Literal["forever", "month", "not_limit"]"""
    game_biz: Optional[str]
    """商品对应的游戏区服（如 hk4e_cn）（单独查询一个商品时）"""
    game: Optional[str]
    """商品对应的游戏"""
    unlimit: Optional[bool]
    """是否为不限量商品"""

    # 以下为实际会用到的属性

    name: Optional[str]
    """商品名称（单独查询一个商品时）"""
    goods_name: Optional[str]
    """商品名称（查询商品列表时）"""

    goods_id: str
    """商品ID(Good_ID)"""

    price: int
    """商品价格"""

    icon: str
    """商品图片链接"""

    def update(self, obj: Union["Good", Dict[str, Any]]) -> "Good":
        """
        更新商品信息

        :param obj: 新的商品数据
        :raise TypeError
        """
        return super().update(obj)

    @property
    def time(self):
        """
        兑换时间

        :return: 如果返回`None`，说明任何时间均可兑换或兑换已结束。
        """
        # "next_time" 为 0 表示任何时间均可兑换或兑换已结束
        if self.next_time == 0:
            return None
        # TODO: 暂时不知道为何 self.sale_start_time 是 str 类型而不是 int 类型
        sale_start_time = int(self.sale_start_time) if self.sale_start_time else 0
        if sale_start_time and time.time() < sale_start_time < self.next_time:
            return sale_start_time
        else:
            return self.next_time

    @property
    def stoke_text(self):
        """
        商品的库存文本
        """
        if self.time_end:
            return "无"
        elif self.time_limited:
            return str(self.num)
        else:
            return "不限"

    @property
    def time_limited(self):
        """
        是否为限时商品
        """
        # 不限量被认为是不限时商品
        return not self.unlimit

    @property
    def time_end(self):
        """
        兑换是否已经结束
        """
        return self.next_time == 0

    @property
    def num(self):
        """
        库存
        如果返回`None`，说明库存不限
        """
        if self.type != 1 and self.next_num == 0:
            return None
        else:
            return self.next_num

    @property
    def limit(self):
        """
        限购，返回元组 (已经兑换次数, 最多可兑换次数, 限购类型)
        """
        return (self.account_exchange_num,
                self.account_cycle_limit, self.account_cycle_type)

    @property
    def is_virtual(self):
        """
        是否为虚拟商品
        """
        return self.type == 2

    @property
    def general_name(self):
        return self.name or self.goods_name


class GameRecord(BaseModel):
    """
    用户游戏数据
    """
    region_name: str
    """服务器区名"""

    game_id: int
    """游戏ID"""

    level: int
    """用户游戏等级"""

    region: str
    """服务器区号"""

    game_role_id: str
    """用户游戏UID"""

    nickname: str
    """用户游戏昵称"""


class GameInfo(BaseModel):
    """
    游戏信息数据
    """
    # ABBR_TO_ID: Dict[int, Tuple[str, str]] = {}
    # '''
    # 游戏ID(game_id)与缩写和全称的对应关系
    # >>> {游戏ID, (缩写, 全称)}
    # '''
    id: int
    """游戏ID"""

    app_icon: str
    """游戏App图标链接(大)"""

    op_name: str
    """游戏代号(英文数字, 例如hk4e)"""

    en_name: str
    """游戏代号2(英文数字, 例如ys)"""

    icon: str
    """游戏图标链接(圆形, 小)"""

    name: str
    """游戏名称"""


class Address(BaseModel):
    """
    地址数据
    """
    connect_areacode: str
    """电话区号"""
    connect_mobile: str
    """电话号码"""

    # 以下为实际会用到的属性

    province_name: str
    """省"""

    city_name: str
    """市"""

    county_name: str
    """区/县"""

    addr_ext: str
    """详细地址"""

    connect_name: str
    """收货人姓名"""

    id: str
    """地址ID"""

    @property
    def phone(self) -> str:
        """
        联系电话(包含区号)
        """
        return self.connect_areacode + " " + self.connect_mobile


class MmtData(BaseModel):
    """
    短信验证码-人机验证任务申请-返回数据
    """
    challenge: Optional[str] = None
    gt: Optional[str] = None
    """验证ID，即 极验文档 中的captchaId，极验后台申请得到"""
    mmt_key: Optional[str] = None
    """验证任务"""
    new_captcha: Optional[bool] = None
    """宕机情况下使用"""
    risk_type: Optional[str] = None
    """结合风控融合，指定验证形式"""
    success: Optional[int] = None
    use_v4: Optional[bool] = None
    """是否使用极验第四代 GT4"""


class Award(BaseModel):
    """
    签到奖励数据
    """
    name: str
    """签到获得的物品名称"""
    icon: str
    """物品图片链接"""
    cnt: int
    """物品数量"""


class GameSignInfo(BaseModel):
    is_sign: bool
    """今日是否已经签到"""
    total_sign_day: int
    """已签多少天"""
    sign_cnt_missed: int
    """漏签多少天"""


class MissionData(BaseModel):
    points: int
    """任务米游币奖励"""
    name: str
    """任务名字，如 讨论区签到"""
    mission_key: str
    """任务代号，如 continuous_sign"""
    threshold: int
    """任务完成的最多次数"""


class MissionState(BaseModel):
    current_myb: int
    """用户当前米游币数量"""
    state_dict: Dict[str, Tuple[MissionData, int]]
    """所有任务对应的完成进度 {mission_key, (MissionData, 当前进度)}"""


class StarRailNoteExpedition(BaseModel):
    """
    崩铁实时便笺数据中的 委托
    """
    avatars: List[str]
    """图标"""
    status: str
    """状态"""
    remaining_time: int
    """完成剩余时间"""
    name: str
    """委托名称"""


class StarRailNote(BaseModel):
    """
    崩铁实时便笺数据 (从米游社内相关页面API的返回数据初始化)
    """
    current_stamina: Optional[int] = None
    """当前开拓力"""
    max_stamina: Optional[int] = None
    """最大开拓力"""
    stamina_recover_time: Optional[int] = None
    """剩余体力恢复时间"""
    current_train_score: Optional[int] = None
    """当前每日实训值"""
    max_train_score: Optional[int] = None
    """最大每日实训值"""
    current_rogue_score: Optional[int] = None
    """当前模拟宇宙积分"""
    max_rogue_score: Optional[int] = None
    """最大模拟宇宙积分"""
    accepted_expedition_num: Optional[int] = None
    """已接受委托数量"""
    total_expedition_num: Optional[int] = None
    """最大委托数量"""
    expeditions: Optional[List[StarRailNoteExpedition]] = None
    """委托"""
    has_signed: Optional[bool] = None
    """当天是否签到"""

    @property
    def stamina_recover_text(self):
        """
        剩余体力恢复文本
        """
        try:
            if not self.stamina_recover_time:
                return ':未获得时间数据'
            elif self.stamina_recover_time == 0:
                return '已准备就绪'
            else:
                recovery_timestamp = int(time.time()) + self.stamina_recover_time
                recovery_datetime = datetime.fromtimestamp(recovery_timestamp)
                return f"将在{recovery_datetime.strftime('%m-%d %H:%M')}回满"
        except KeyError:
            return None


class BaseApiStatus(BaseModel):
    """
    API返回结果基类
    """
    success: bool = False
    """成功"""
    network_error: bool = False
    """连接失败"""
    incorrect_return: bool = False
    """服务器返回数据不正确"""
    login_expired: bool = False
    """登录失效"""
    need_verify: bool = False
    """需要进行人机验证"""
    invalid_ds: bool = False
    """Headers DS无效"""

    def __bool__(self):
        return self.success

    @property
    def error_type(self):
        """
        返回错误类型
        """
        for key, field in self.__fields__.items():
            if field and key != "success":
                return key
        return None


class CreateMobileCaptchaStatus(BaseApiStatus):
    """
    发送短信验证码 返回结果
    """
    incorrect_geetest: bool = False
    """人机验证结果数据无效"""
    not_registered: bool = False
    """手机号码未注册"""
    invalid_phone_number: bool = False
    """手机号码无效"""
    too_many_requests: bool = False
    """发送过于频繁"""


class GetCookieStatus(BaseApiStatus):
    """
    获取Cookie 返回结果
    """
    incorrect_captcha: bool = False
    """验证码错误"""
    missing_login_ticket: bool = False
    """Cookies 缺少 login_ticket"""
    missing_bbs_uid: bool = False
    """Cookies 缺少 bbs_uid (stuid, ltuid, ...)"""
    missing_cookie_token: bool = False
    """Cookies 缺少 cookie_token"""
    missing_stoken: bool = False
    """Cookies 缺少 stoken"""
    missing_stoken_v1: bool = False
    """Cookies 缺少 stoken_v1"""
    missing_stoken_v2: bool = False
    """Cookies 缺少 stoken_v2"""
    missing_mid: bool = False
    """Cookies 缺少 mid"""


class GetGoodDetailStatus(BaseApiStatus):
    """
    获取商品详细信息 返回结果
    """
    good_not_existed: bool = False


class ExchangeStatus(BaseApiStatus):
    """
    兑换操作 返回结果
    """
    missing_stoken: bool = False
    """商品为游戏内物品，但 Cookies 缺少 stoken"""
    missing_mid: bool = False
    """商品为游戏内物品，但 stoken 为 'v2' 类型同时 Cookies 缺少 mid"""
    missing_address: bool = False
    """商品为实体物品，但未配置收货地址"""
    missing_game_uid: bool = False
    """商品为游戏内物品，但未配置对应游戏的账号UID"""
    unsupported_game: bool = False
    """暂不支持兑换对应分区/游戏的商品"""
    failed_getting_game_record: bool = False
    """获取用户 GameRecord 失败"""
    init_required: bool = False
    """未进行兑换任务初始化"""
    account_not_found: bool = False
    """账号不存在"""


class MissionStatus(BaseApiStatus):
    """
    米游币任务 返回结果
    """
    failed_getting_post: bool = False
    """获取文章失败"""
    already_signed: bool = False
    """已经完成过签到"""


class GetFpStatus(BaseApiStatus):
    """
    兑换操作 返回结果
    """
    invalid_arguments: bool = False
    """参数错误"""


class BoardStatus(BaseApiStatus):
    """
    实时便笺 返回结果
    """
    game_record_failed: bool = False
    """获取用户游戏数据失败"""
    game_list_failed: bool = False
    """获取游戏列表失败"""


class StarRailNoteStatus(BoardStatus):
    """
    星铁实时便笺 返回结果
    """
    no_starrail_account: bool = False
    """用户没有任何星铁账户"""


GeetestResult = NamedTuple("GeetestResult", validate=str, seccode=str)
"""人机验证结果数据"""


class GeetestResultV4(BaseModel):
    """
    GEETEST GT4 人机验证结果数据
    """
    captcha_id: str
    lot_number: str
    pass_token: str
    gen_time: str
    captcha_output: str


if __name__ == '__main__':
    StarRailNote.model_validate({"current_stamina":16,"max_stamina":240,"stamina_recover_time":80566,"accepted_expedition_num":4,"total_expedition_num":4,"expeditions":[{"avatars":["https://act-webstatic.mihoyo.com/darkmatter/hkrpg/prod_gf_cn/item_icon_734174/dc7c8e4af484f0d3e49ea2f4b14dfeda.png","https://act-webstatic.mihoyo.com/darkmatter/hkrpg/prod_gf_cn/item_icon_734174/71e75b9fe581b35d2528a1525b310e1b.png"],"status":"Ongoing","remaining_time":27286,"name":"无名之地，无名之人"},{"avatars":["https://act-webstatic.mihoyo.com/darkmatter/hkrpg/prod_gf_cn/item_icon_734174/adce7db9f95d5df79da302b38c40a2bb.png","https://act-webstatic.mihoyo.com/darkmatter/hkrpg/prod_gf_cn/item_icon_734174/33d50607c0e02b18ea296d53aa2b07d9.png"],"status":"Ongoing","remaining_time":27290,"name":"阿卡夏记录"},{"avatars":["https://act-webstatic.mihoyo.com/darkmatter/hkrpg/prod_gf_cn/item_icon_734174/e772e00f591debbf185933a5e12daa4e.png","https://act-webstatic.mihoyo.com/darkmatter/hkrpg/prod_gf_cn/item_icon_734174/f9dacefa3a370c56dee1cc57588509d8.png"],"status":"Ongoing","remaining_time":27294,"name":"看不见的手"},{"avatars":["https://act-webstatic.mihoyo.com/darkmatter/hkrpg/prod_gf_cn/item_icon_734174/c9b70366adf96bfbe52768c0a3c88cbb.png","https://act-webstatic.mihoyo.com/darkmatter/hkrpg/prod_gf_cn/item_icon_734174/ef95b2d01e5598c520469d774a5fa223.png"],"status":"Ongoing","remaining_time":27299,"name":"被废弃与损害的"}],"current_train_score":100,"max_train_score":500,"current_rogue_score":14000,"max_rogue_score":14000,"has_signed":False,"sign_url":"https://webstatic.mihoyo.com/bbs/event/signin/hkrpg/index.html?bbs_auth_required=true\u0026act_id=e202304121516551\u0026bbs_auth_required=true\u0026bbs_presentation_style=fullscreen","current_reserve_stamina":0,"is_reserve_stamina_full":False,"home_url":"https://webstatic.mihoyo.com/app/community-game-records/rpg/index.html?mhy_presentation_style=fullscreen\u0026game_id=6","note_url":"https://webstatic.mihoyo.com/app/community-game-records/rpg/index.html?mhy_presentation_style=fullscreen\u0026game_id=6"}, strict=False)