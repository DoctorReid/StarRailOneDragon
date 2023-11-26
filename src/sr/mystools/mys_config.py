import asyncio
import time
from typing import Optional, List

from basic.log_utils import log
from sr.config import ConfigHolder
from sr.mystools import login
from sr.mystools.data_model import StarRailNoteExpedition
from sr.mystools.plugin_data import PluginDataManager
from sr.mystools.simple_api import starrail_note
from sr.mystools.user_data import UserAccount


class MysConfig(ConfigHolder):

    def __init__(self):
        super().__init__('mys', sub_dir=['mystool'], sample=False)
        self._user_id: str = 'fix'
        self._mys_conf = PluginDataManager.plugin_data
        self._login_expired: bool = False

    def try_captcha(self, phone_number: str) -> bool:
        _tmp_device_id, captcha_result = asyncio.run(login.get_device_id_and_try_captcha(self._user_id, phone_number))
        self.device_id = _tmp_device_id
        return captcha_result

    def login(self, phone_number: str, captcha: str) -> bool:
        if asyncio.run(login.do_login(self._user_id, phone_number, self.device_id, captcha)):
            self.phone_number = phone_number
            return True
        else:
            return False

    def logout(self):
        self.phone_number = ''
        self._login_expired = True

    def update_note(self) -> bool:
        """
        更新便签
        :return:
        """
        account = self.user_account
        if account is None:
            return False
        if not self.is_login:
            return False
        if time.time() - self.refresh_time < 300:
            log.info('距离上一次刷新不到5分钟 不需要刷新啦')
            return False
        starrail_board_status, note = asyncio.run(starrail_note(account))
        if not starrail_board_status:
            if starrail_board_status.login_expired:
                self._login_expired = True
                log.info(f'账户 {account.bbs_uid} 登录失效，请重新登录')
            elif starrail_board_status.no_starrail_account:
                log.info(f'账户 {account.bbs_uid} 没有绑定任何星铁账户，请绑定后再重试')
            elif starrail_board_status.need_verify:
                log.info(f'账户 {account.bbs_uid} 获取实时便笺时被人机验证阻拦')
            log.info(f'账户 {account.bbs_uid} 获取实时便笺请求失败，你可以手动前往App查看')
            return False

        if note is not None:
            self.update('refresh_time', time.time(), False)
            self.update('current_stamina', note.current_stamina, False)
            self.update('max_stamina', note.max_stamina, False)
            self.update('stamina_recover_time', note.stamina_recover_time, False)
            self.update('current_train_score', note.current_train_score, False)
            self.update('max_train_score', note.max_train_score, False)
            self.update('current_rogue_score', note.current_rogue_score, False)
            self.update('max_rogue_score', note.max_rogue_score, False)
            self.update('accepted_expedition_num', note.accepted_expedition_num, False)
            self.update('total_expedition_num', note.total_expedition_num, False)
            self.update('has_signed', note.has_signed, False)

            expeditions = []
            for e in note.expeditions:
                expeditions.append(e.model_dump())
            self.update('expeditions', expeditions, False)

            self.save()
            return True

        return False

    @property
    def user_account(self) -> Optional[UserAccount]:
        if self._user_id not in self._mys_conf.users:
            return None

        user = self._mys_conf.users[self._user_id]
        for account in user.accounts.values():
            if account.phone_number == self.phone_number:
                return account

        return None

    @property
    def device_id(self) -> str:
        return self.get('device_id', '')

    @device_id.setter
    def device_id(self, new_value: str):
        self.update('device_id', new_value)

    @property
    def phone_number(self) -> str:
        return self.get('phone_num', '')

    @phone_number.setter
    def phone_number(self, new_value):
        """
        当前使用的手机号
        :param new_value:
        :return:
        """
        self.update('phone_num', new_value)

    @property
    def is_login(self) -> bool:
        """
        是否已经登录
        :return:
        """
        account = self.user_account
        if account is None:
            return False
        if self._login_expired:
            return False
        return account.cookies.cookie_token is not None

    @property
    def refresh_time(self) -> float:
        """
        便签更新时间 时间戳
        :return:
        """
        return self.get('refresh_time', time.time())

    @property
    def refresh_time_str(self) -> str:
        """
        便签更新时间 用于显示
        :return:
        """
        time_tuple = time.localtime(self.refresh_time)
        return time.strftime('%m-%d %H:%M', time_tuple)

    @property
    def current_stamina(self) -> int:
        """
        当前开拓力
        :return:
        """
        return self.get('current_stamina', 0)

    @property
    def max_stamina(self) -> int:
        """
        最大开拓力
        :return:
        """
        return self.get('max_stamina', 0)

    @property
    def stamina_recover_time(self) -> int:
        """
        开拓力完全恢复剩余时间 单位=秒
        :return:
        """
        return self.get('stamina_recover_time', 86400)

    @property
    def current_train_score(self) -> int:
        """
        当前实训值
        :return:
        """
        return self.get('current_train_score', 0)

    @property
    def max_train_score(self) -> int:
        """
        最大实训值
        :return:
        """
        return self.get('max_train_score', 500)

    @property
    def current_rogue_score(self) -> int:
        """
        当前模拟宇宙积分
        :return:
        """
        return self.get('current_rogue_score', 0)

    @property
    def max_rogue_score(self) -> int:
        """
        当前模拟宇宙积分
        :return:
        """
        return self.get('max_rogue_score', 14000)

    @property
    def expeditions(self) -> List:
        return self.get('expeditions', [])


_mys_config: Optional[MysConfig] = None


def get() -> MysConfig:
    global _mys_config
    if _mys_config is None:
        _mys_config = MysConfig()
    return _mys_config
