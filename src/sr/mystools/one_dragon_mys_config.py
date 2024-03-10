import asyncio
import time
from typing import Optional, List

from basic.config import ConfigHolder
from basic.log_utils import log
from sr.mystools import PluginDataManager, get_validate, CreateMobileCaptchaStatus, UserData, UserAccount, \
    BaseGameSign, StarRailSign, plugin_config, get_missions_state, BaseMission, StarRailMission
from sr.mystools.api.common import create_mmt, create_mobile_captcha, get_login_ticket_by_captcha, get_device_fp, \
    get_multi_token_by_login_ticket, get_stoken_v2_by_v1, get_ltoken_by_stoken, get_cookie_token_by_stoken, \
    starrail_note, get_game_record
from sr.mystools.model.common import StarRailNoteExpedition, MissionStatus


class MysConfig(ConfigHolder):

    def __init__(self, account_idx: Optional[int] = None):
        super().__init__('mys', account_idx=account_idx, sample=False)
        self._user_id: str = '%02d' % account_idx if account_idx is not None else '00'
        self._mys_conf = PluginDataManager.plugin_data
        self._login_expired: bool = False

    def try_captcha(self, phone_number: str) -> bool:
        _tmp_device_id, captcha_result = asyncio.run(self.get_device_id_and_try_captcha(phone_number))
        self.device_id = _tmp_device_id
        return captcha_result

    def login(self, phone_number: str, captcha: str) -> bool:
        if asyncio.run(self.do_login(phone_number, self.device_id, captcha)):
            self.phone_number = phone_number
            return True
        else:
            return False

    def logout(self):
        self.phone_number = ''
        self._login_expired = True

    async def get_device_id_and_try_captcha(self, phone: str):
        user = self._mys_conf.users.get(self._user_id)
        if user:
            account_filter = filter(lambda x: x.phone_number == phone, user.accounts.values())
            account = next(account_filter, None)
            device_id = account.phone_number if account else None
        else:
            device_id = None
        mmt_status, mmt_data, device_id, _ = await create_mmt(device_id=device_id, retry=False)
        if mmt_status:
            if not mmt_data.gt:
                captcha_status, _ = await create_mobile_captcha(phone_number=phone, mmt_data=mmt_data,
                                                                device_id=device_id)
                if captcha_status:
                    log.info("检测到无需进行人机验证，已发送短信验证码，请查收")
                    return device_id, True
            else:
                captcha_status = CreateMobileCaptchaStatus()
            if captcha_status.invalid_phone_number:
                log.info("⚠️手机号无效，请重新发送手机号")
            elif captcha_status.not_registered:
                log.info("⚠️手机号未注册，请注册后重新发送手机号")

        log.info('2.前往米哈游官方登录页，获取验证码（不要登录！）')
        return device_id, False

    async def do_login(self, phone_number: str, device_id: str, captcha: str) -> bool:
        self._mys_conf.users.setdefault(self._user_id, UserData())
        user = self._mys_conf.users[self._user_id]
        # 1. 通过短信验证码获取 login_ticket / 使用已有 login_ticket
        login_status, cookies = await get_login_ticket_by_captcha(phone_number, int(captcha), device_id)
        if login_status:
            log.info(f"用户 {cookies.bbs_uid} 成功获取 login_ticket: {cookies.login_ticket}")
            account = self._mys_conf.users[self._user_id].accounts.get(cookies.bbs_uid)
            """当前的账户数据对象"""
            if not account or not account.cookies:
                user.accounts.update({
                    cookies.bbs_uid: UserAccount(phone_number=phone_number, cookies=cookies, device_id_ios=device_id,
                                                 mission_games=[StarRailMission.__name__])
                })
                account = user.accounts[cookies.bbs_uid]
            else:
                account.cookies.update(cookies)
            fp_status, account.device_fp = await get_device_fp(device_id)
            if fp_status:
                log.info(f"用户 {cookies.bbs_uid} 成功获取 device_fp: {account.device_fp}")
            PluginDataManager.write_plugin_data()

            # 2. 通过 login_ticket 获取 stoken 和 ltoken
            if login_status or account:
                login_status, cookies = await get_multi_token_by_login_ticket(account.cookies)
                if login_status:
                    log.info(f"用户 {phone_number} 成功获取 stoken: {cookies.stoken}")
                    account.cookies.update(cookies)
                    PluginDataManager.write_plugin_data()

                    # 3. 通过 stoken_v1 获取 stoken_v2 和 mid
                    login_status, cookies = await get_stoken_v2_by_v1(account.cookies, device_id)
                    if login_status:
                        log.info(f"用户 {phone_number} 成功获取 stoken_v2: {cookies.stoken_v2}")
                        account.cookies.update(cookies)
                        PluginDataManager.write_plugin_data()

                        # 4. 通过 stoken_v2 获取 ltoken
                        login_status, cookies = await get_ltoken_by_stoken(account.cookies, device_id)
                        if login_status:
                            log.info(f"用户 {phone_number} 成功获取 ltoken: {cookies.ltoken}")
                            account.cookies.update(cookies)
                            PluginDataManager.write_plugin_data()

                            # 5. 通过 stoken_v2 获取 cookie_token
                            login_status, cookies = await get_cookie_token_by_stoken(account.cookies, device_id)
                            if login_status:
                                log.info(f"用户 {phone_number} 成功获取 cookie_token: {cookies.cookie_token}")
                                account.cookies.update(cookies)
                                PluginDataManager.write_plugin_data()

                                log.info(f"米游社账户 {phone_number} 绑定成功")
                                return True
        return False

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
        return self.get('refresh_time', 0)

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
    def expeditions(self) -> List[StarRailNoteExpedition]:
        e_arr = self.get('expeditions', [])
        expeditions: List[StarRailNoteExpedition] = []
        for e in e_arr:
            expeditions.append(StarRailNoteExpedition.model_validate(e))

        return expeditions

    @property
    def auto_game_sign(self) -> bool:
        """
        是否自动进行米游社的游戏板块签到
        :return:
        """
        return self.get('auto_game_sign', False)

    @auto_game_sign.setter
    def auto_game_sign(self, new_value: bool):
        """
        是否自动进行米游社的游戏板块签到
        :return:
        """
        self.update('auto_game_sign', new_value)

    @property
    def auto_bbs_sign(self) -> bool:
        """
        是否自动进行米游社的米游币任务
        :return:
        """
        return self.get('auto_bbs_sign', False)

    @auto_bbs_sign.setter
    def auto_bbs_sign(self, new_value: bool):
        """
        是否自动进行米游社的米游币任务
        :return:
        """
        self.update('auto_bbs_sign', new_value)

    async def perform_game_sign(self) -> bool:
        """
        进行游戏签到
        :return:
        """
        account = self.user_account
        if account is None:
            log.error('未登录米游社账号')
            return False

        signed = False
        """是否已经完成过签到"""
        game_record_status, records = await get_game_record(account)
        if not game_record_status:
            log.error(f"账户 {account.display_name} 获取游戏账号信息失败，请重新尝试")
            return False

        games_has_record = []
        for class_type in BaseGameSign.available_game_signs:
            if class_type != StarRailSign:  # 只进行星铁的签到
                continue
            signer = class_type(account, records)
            if not signer.has_record:
                continue
            else:
                games_has_record.append(signer)
            get_info_status, info = await signer.get_info(account.platform)
            if not get_info_status:
                log.error(f"账户 {account.display_name} 获取签到记录失败")
            else:
                signed = info.is_sign

            # 若没签到，则进行签到功能；若获取今日签到情况失败，仍可继续
            if (get_info_status and not info.is_sign) or not get_info_status:
                sign_status, mmt_data = await signer.sign(account.platform)
                if sign_status.need_verify:
                    if plugin_config.preference.geetest_url:
                        log.info("正在尝试完成人机验证，请稍后...")
                        geetest_result = await get_validate(mmt_data.gt, mmt_data.challenge)
                        sign_status, _ = await signer.sign(account.platform, mmt_data, geetest_result)

                if not sign_status:
                    if sign_status.login_expired:
                        message = f"账户 {account.display_name} 签到时服务器返回登录失效，请尝试重新登录绑定账户"
                    elif sign_status.need_verify:
                        message = (f"账户 {account.display_name} 签到时可能遇到验证码拦截，"
                                   "请手动前往米游社签到")
                    else:
                        message = f"账户 {account.display_name} 签到失败，请稍后再试"
                    log.error(message)
                else:
                    log.info(f"账户 {account.display_name} 签到成功！")
                    return True
            elif signed:
                log.info(f"账户 {account.display_name} 已经签到过了！")
                return True

            await asyncio.sleep(plugin_config.preference.sleep_time)

        if len(games_has_record) == 0:
            log.error(f"您的米游社账户 {account.display_name} 下不存在星铁游戏账号，已跳过签到")

        return False

    async def perform_bbs_sign(self) -> bool:
        """
        执行米游币任务函数
        """
        account = self.user_account
        if account is None:
            log.error('未登录米游社账号')
            return False

        missions_state_status, missions_state = await get_missions_state(account)
        if not missions_state_status:
            if missions_state_status.login_expired:
                log.error(f'账户 {account.display_name} 登录失效，请重新登录')
            log.error(f'账户 {account.display_name} 获取任务完成情况请求失败，你可以手动前往App查看')
            return False

        # 在此处进行判断。因为如果在多个分区执行任务，会在完成之前就已经达成米游币任务目标，导致其他分区任务不会执行。
        finished = all(current == mission.threshold for mission, current in missions_state.state_dict.values())
        if not finished:
            for class_name in account.mission_games:
                class_type = BaseMission.available_games.get(class_name)
                mission_obj = class_type(account)
                log.info(f'账户 {account.display_name} 开始在分区『{class_type.name}』执行米游币任务...')
                log.info('可能需要几十秒时间，请耐心等待')

                # 执行任务
                sign_status, read_status, like_status, share_status = (
                    MissionStatus(),
                    MissionStatus(),
                    MissionStatus(),
                    MissionStatus()
                )
                sign_points: Optional[int] = None
                for key_name in missions_state.state_dict:
                    if key_name == BaseMission.SIGN:
                        sign_status, sign_points = await mission_obj.sign()
                        log.info(f"签到：{'✓' if sign_status else '✕'} +{sign_points or '0'} 米游币")
                    elif key_name == BaseMission.VIEW:
                        read_status = await mission_obj.read()
                        log.info(f"阅读：{'✓' if read_status else '✕'}")
                    elif key_name == BaseMission.LIKE:
                        like_status = await mission_obj.like()
                        log.info(f"点赞：{'✓' if like_status else '✕'}")
                    elif key_name == BaseMission.SHARE:
                        share_status = await mission_obj.share()
                        log.info(f"分享：{'✓' if share_status else '✕'}")

                if sign_status and read_status and like_status and share_status:
                    return True
        else:
            log.info(f'账户 {account.display_name} 之前已完成米游币任务')
            return True

        return False