"""
### 米游社登录获取Cookie相关
"""

from basic.log_utils import log
from .data_model import CreateMobileCaptchaStatus
from .plugin_data import PluginDataManager, write_plugin_data
from .simple_api import get_login_ticket_by_captcha, get_multi_token_by_login_ticket, get_stoken_v2_by_v1, \
    get_ltoken_by_stoken, get_cookie_token_by_stoken, get_device_fp, create_mmt, create_mobile_captcha
from .user_data import UserAccount, UserData
from .utils import get_validate

_conf = PluginDataManager.plugin_data


async def get_device_id_and_try_captcha(user_id: str, phone: str):
    user = _conf.users.get(user_id)
    if user:
        account_filter = filter(lambda x: x.phone_number == phone, user.accounts.values())
        account = next(account_filter, None)
        device_id = account.phone_number if account else None
    else:
        device_id = None
    mmt_status, mmt_data, device_id, _ = await create_mmt(device_id=device_id, retry=False)
    if mmt_status:
        if not mmt_data.gt:
            captcha_status, _ = await create_mobile_captcha(phone_number=phone, mmt_data=mmt_data, device_id=device_id)
            if captcha_status:
                log.info("检测到无需进行人机验证，已发送短信验证码，请查收")
                return device_id, True
        elif _conf.preference.geetest_url:
            log.info("⏳正在尝试完成人机验证，请稍后...")
            # TODO: 人机验证待支持 GT4
            geetest_result = await get_validate(gt=mmt_data.gt)
            captcha_status, _ = await create_mobile_captcha(
                phone_number=phone,
                mmt_data=mmt_data,
                geetest_result=geetest_result,
                use_v4=False,
                device_id=device_id
            )
            if captcha_status:
                log.info("已发送短信验证码，请查收")
                return device_id, True
            elif captcha_status.incorrect_geetest:
                log.info("⚠️尝试进行人机验证失败，请手动获取短信验证码")
        else:
            captcha_status = CreateMobileCaptchaStatus()
        if captcha_status.invalid_phone_number:
            log.info("⚠️手机号无效，请重新发送手机号")
        elif captcha_status.not_registered:
            log.info("⚠️手机号未注册，请注册后重新发送手机号")

    log.info('2.前往米哈游官方登录页，获取验证码（不要登录！）')
    return device_id, False


async def do_login(user_id: str, phone_number: str, device_id: str, captcha: str) -> bool:
    _conf.users.setdefault(user_id, UserData())
    user = _conf.users[user_id]
    # 1. 通过短信验证码获取 login_ticket / 使用已有 login_ticket
    login_status, cookies = await get_login_ticket_by_captcha(phone_number, int(captcha), device_id)
    if login_status:
        log.info(f"用户 {cookies.bbs_uid} 成功获取 login_ticket: {cookies.login_ticket}")
        account = _conf.users[user_id].accounts.get(cookies.bbs_uid)
        """当前的账户数据对象"""
        if not account or not account.cookies:
            user.accounts.update({
                cookies.bbs_uid: UserAccount(phone_number=phone_number, cookies=cookies, device_id_ios=device_id)
            })
            account = user.accounts[cookies.bbs_uid]
        else:
            account.cookies.update(cookies)
        fp_status, account.device_fp = await get_device_fp(device_id)
        if fp_status:
            log.info(f"用户 {cookies.bbs_uid} 成功获取 device_fp: {account.device_fp}")
        write_plugin_data()

        # 2. 通过 login_ticket 获取 stoken 和 ltoken
        if login_status or account:
            login_status, cookies = await get_multi_token_by_login_ticket(account.cookies)
            if login_status:
                log.info(f"用户 {phone_number} 成功获取 stoken: {cookies.stoken}")
                account.cookies.update(cookies)
                write_plugin_data()

                # 3. 通过 stoken_v1 获取 stoken_v2 和 mid
                login_status, cookies = await get_stoken_v2_by_v1(account.cookies, device_id)
                if login_status:
                    log.info(f"用户 {phone_number} 成功获取 stoken_v2: {cookies.stoken_v2}")
                    account.cookies.update(cookies)
                    write_plugin_data()

                    # 4. 通过 stoken_v2 获取 ltoken
                    login_status, cookies = await get_ltoken_by_stoken(account.cookies, device_id)
                    if login_status:
                        log.info(f"用户 {phone_number} 成功获取 ltoken: {cookies.ltoken}")
                        account.cookies.update(cookies)
                        write_plugin_data()

                        # 5. 通过 stoken_v2 获取 cookie_token
                        login_status, cookies = await get_cookie_token_by_stoken(account.cookies, device_id)
                        if login_status:
                            log.info(f"用户 {phone_number} 成功获取 cookie_token: {cookies.cookie_token}")
                            account.cookies.update(cookies)
                            write_plugin_data()

                            log.info(f"{_conf.preference.log_head}米游社账户 {phone_number} 绑定成功")
                            return True
    return False