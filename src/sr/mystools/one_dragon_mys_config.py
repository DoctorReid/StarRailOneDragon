import asyncio
import time
from typing import Optional, List

from basic.config import ConfigHolder
from basic.log_utils import log
from sr.mystools import PluginDataManager, get_validate, UserData, UserAccount, \
    BaseGameSign, StarRailSign, plugin_config, get_missions_state, BaseMission, generate_device_id, \
    generate_qr_img, BBSCookies
from sr.mystools.api.common import get_device_fp, \
    get_ltoken_by_stoken, get_cookie_token_by_stoken, \
    starrail_note, get_game_record, fetch_game_token_qrcode, query_game_token_qrcode, get_token_by_game_token, \
    get_cookie_token_by_game_token
from sr.mystools.model.common import StarRailNoteExpedition, MissionStatus


class MysConfig(ConfigHolder):

    def __init__(self, account_idx: Optional[int] = None):
        super().__init__('mys', account_idx=account_idx, sample=False)
        self._user_id: str = '%02d' % account_idx if account_idx is not None else '00'
        self._login_expired: bool = False

    def get_device_id_and_qrcode(self) -> Optional[str]:
        """
        获取二维码
        :return:
        """
        # 获取用户数据对象
        user_id = self._user_id
        PluginDataManager.plugin_data.users.setdefault(user_id, UserData())

        # 1. 获取 GameToken 登录二维码
        self.device_id = generate_device_id()
        login_status, fetch_qrcode_ret = asyncio.run(
            fetch_game_token_qrcode(self.device_id, plugin_config.preference.game_token_app_id)
        )
        if fetch_qrcode_ret:
            qrcode_url, self.qrcode_ticket = fetch_qrcode_ret
            return generate_qr_img(qrcode_url)
        else:
            return None

    def logout(self):
        self._login_expired = True

    def wait_qrcode_login(self) -> bool:
        """
        等待二维码登录
        :return:
        """
        user_id = self._user_id
        device_id = self.device_id
        qrcode_ticket = self.qrcode_ticket
        PluginDataManager.plugin_data.users.setdefault(user_id, UserData())
        user = PluginDataManager.plugin_data.users[user_id]

        # 2. 从二维码登录获取 GameToken
        qrcode_query_times = round(
            plugin_config.preference.qrcode_wait_time / plugin_config.preference.qrcode_query_interval
        )
        bbs_uid, game_token = None, None
        for _ in range(qrcode_query_times):
            log.info('等待二维码登录中')
            login_status, query_qrcode_ret = asyncio.run(
                query_game_token_qrcode(qrcode_ticket, device_id, plugin_config.preference.game_token_app_id)
            )
            if query_qrcode_ret:
                bbs_uid, game_token = query_qrcode_ret
                log.info(f"用户 {bbs_uid} 成功获取 game_token: {game_token}")
                break
            elif login_status.qrcode_expired:
                log.error('二维码已过期，登录失败')
            elif not login_status:
                time.sleep(plugin_config.preference.qrcode_query_interval)

        if bbs_uid and game_token:
            cookies = BBSCookies()
            cookies.bbs_uid = bbs_uid
            account = PluginDataManager.plugin_data.users[user_id].accounts.get(bbs_uid)
            """当前的账户数据对象"""
            if not account or not account.cookies:
                user.accounts.update({
                    bbs_uid: UserAccount(
                        phone_number=None,
                        cookies=cookies,
                        device_id_ios=device_id,
                        device_id_android=generate_device_id())
                })
                account = user.accounts[bbs_uid]
            else:
                account.cookies.update(cookies)

            fp_status, account.device_fp = asyncio.run(get_device_fp(device_id))
            if fp_status:
                log.info(f"用户 {bbs_uid} 成功获取 device_fp: {account.device_fp}")
            PluginDataManager.write_plugin_data()

            if login_status:
                # 3. 通过 GameToken 获取 stoken_v2
                login_status, cookies = asyncio.run(get_token_by_game_token(bbs_uid, game_token))
                if login_status:
                    log.info(f"用户 {bbs_uid} 成功获取 stoken_v2: {cookies.stoken_v2}")
                    account.cookies.update(cookies)
                    PluginDataManager.write_plugin_data()

                    if account.cookies.stoken_v2:
                        # 5. 通过 stoken_v2 获取 ltoken
                        login_status, cookies = asyncio.run(get_ltoken_by_stoken(account.cookies, device_id))
                        if login_status:
                            log.info(f"用户 {bbs_uid} 成功获取 ltoken: {cookies.ltoken}")
                            account.cookies.update(cookies)
                            PluginDataManager.write_plugin_data()

                        # 6.1. 通过 stoken_v2 获取 cookie_token
                        login_status, cookies = asyncio.run(get_cookie_token_by_stoken(account.cookies, device_id))
                        if login_status:
                            log.info(f"用户 {bbs_uid} 成功获取 cookie_token: {cookies.cookie_token}")
                            account.cookies.update(cookies)
                            PluginDataManager.write_plugin_data()

                            log.info(f"{plugin_config.preference.log_head}米游社账户 {bbs_uid} 绑定成功")
                    else:
                        # 6.2. 通过 GameToken 获取 cookie_token
                        login_status, cookies = asyncio.run(get_cookie_token_by_game_token(bbs_uid, game_token))
                        if login_status:
                            log.info(f"用户 {bbs_uid} 成功获取 cookie_token: {cookies.cookie_token}")
                            account.cookies.update(cookies)
                            PluginDataManager.write_plugin_data()
        else:
            log.error("️获取二维码扫描状态超时，请尝试重新登录")

        success = login_status is not None
        if success:
            self.phone_number = account.phone_number
        return success

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
                expeditions.append(e.dict())
            self.update('expeditions', expeditions, False)

            self.save()
            return True

        return False

    @property
    def user_account(self) -> Optional[UserAccount]:
        if self._user_id not in PluginDataManager.plugin_data.users:
            return None

        user = PluginDataManager.plugin_data.users[self._user_id]
        for account in user.accounts.values():
            if account.phone_number == self.phone_number:
                return account

        return None

    @property
    def user_data(self) -> Optional[UserData]:
        if self._user_id not in PluginDataManager.plugin_data.users:
            return None

        return PluginDataManager.plugin_data.users[self._user_id]


    @property
    def phone_number(self) -> str:
        return self.get('phone_number', '')

    @phone_number.setter
    def phone_number(self, new_value: str):
        self.update('phone_number', new_value)

    @property
    def device_id(self) -> str:
        return self.get('device_id', '')

    @device_id.setter
    def device_id(self, new_value: str):
        self.update('device_id', new_value)

    @property
    def qrcode_ticket(self) -> str:
        return self.get('qrcode_ticket', '')

    @qrcode_ticket.setter
    def qrcode_ticket(self, new_value: str):
        self.update('qrcode_ticket', new_value)

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
            expeditions.append(StarRailNoteExpedition.parse_obj(e))

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
                        sign_status, sign_points = await mission_obj.sign(self.user_data)
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