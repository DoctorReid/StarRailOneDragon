import asyncio
import threading
from typing import Union, Optional, Iterable, Dict

from nonebot import on_command, get_adapters
from nonebot.adapters.onebot.v11 import MessageSegment as OneBotV11MessageSegment, Adapter as OneBotV11Adapter, \
    MessageEvent as OneBotV11MessageEvent
from nonebot.adapters.qq import MessageSegment as QQGuildMessageSegment, Adapter as QQGuildAdapter, \
    MessageEvent as QQGuildMessageEvent
from nonebot.adapters.qq.exception import AuditException
from nonebot.exception import ActionFailed
from nonebot.internal.matcher import Matcher
from nonebot.params import CommandArg
from nonebot_plugin_apscheduler import scheduler
from nonebot_plugin_saa import Image
from pydantic import BaseModel

from ..api import BaseGameSign
from ..api import BaseMission, get_missions_state
from ..api.common import genshin_note, get_game_record, starrail_note
from ..api.weibo import WeiboCode
from ..command.common import CommandRegistry
from ..command.exchange import generate_image
from ..model import (MissionStatus, PluginDataManager, plugin_config, UserData, CommandUsage, GenshinNoteNotice,
                     StarRailNoteNotice)
from ..utils import get_file, logger, COMMAND_BEGIN, GeneralMessageEvent, GeneralGroupMessageEvent, \
    send_private_msg, get_all_bind, \
    get_unique_users, get_validate, read_admin_list

__all__ = [
    "manually_game_sign", "manually_bbs_sign", "manually_genshin_note_check",
    "manually_starrail_note_check", "manually_weibo_check"
]

manually_game_sign = on_command(plugin_config.preference.command_start + '签到', priority=5, block=True)

CommandRegistry.set_usage(
    manually_game_sign,
    CommandUsage(
        name="签到",
        description="手动进行游戏签到，查看本次签到奖励及本月签到天数"
    )
)


@manually_game_sign.handle()
async def _(event: Union[GeneralMessageEvent], matcher: Matcher, command_arg=CommandArg()):
    """
    手动游戏签到函数
    """
    user_id = event.get_user_id()
    user = PluginDataManager.plugin_data.users.get(user_id)
    if not user or not user.accounts:
        await manually_game_sign.finish(f"⚠️你尚未绑定米游社账户，请先使用『{COMMAND_BEGIN}登录』进行登录")
    if command_arg:
        if (specified_user_id := str(command_arg)) == "*" or specified_user_id.isdigit():
            if user_id not in read_admin_list():
                await manually_game_sign.finish("⚠️你暂无权限执行此操作，只有管理员名单中的用户可以执行此操作")
            else:
                if specified_user_id == "*":
                    await manually_game_sign.send("⏳开始为所有用户执行游戏签到...")
                    for user_id_, user_ in get_unique_users():
                        await manually_game_sign.send(f"⏳开始为用户 {user_id_} 执行游戏签到...")
                        await perform_game_sign(
                            user=user_,
                            user_ids=[],
                            matcher=matcher,
                            event=event
                        )
                else:
                    specified_user = PluginDataManager.plugin_data.users.get(specified_user_id)
                    if not specified_user:
                        await manually_game_sign.finish(f"⚠️未找到用户 {specified_user_id}")
                    await manually_game_sign.send(f"⏳开始为用户 {specified_user_id} 执行游戏签到...")
                    await perform_game_sign(
                        user=specified_user,
                        user_ids=[],
                        matcher=matcher,
                        event=event
                    )
    else:
        await manually_game_sign.send("⏳开始游戏签到...")
        await perform_game_sign(user=user, user_ids=[user_id], matcher=matcher, event=event)


manually_bbs_sign = on_command(plugin_config.preference.command_start + '任务', priority=5, block=True)

CommandRegistry.set_usage(
    manually_bbs_sign,
    CommandUsage(
        name="任务",
        description="手动执行米游币每日任务，可以查看米游币任务完成情况"
    )
)


@manually_bbs_sign.handle()
async def _(event: Union[GeneralMessageEvent], matcher: Matcher, command_arg=CommandArg()):
    """
    手动米游币任务函数
    """
    user_id = event.get_user_id()
    user = PluginDataManager.plugin_data.users.get(user_id)
    if not user or not user.accounts:
        await manually_bbs_sign.finish(f"⚠️你尚未绑定米游社账户，请先使用『{COMMAND_BEGIN}登录』进行登录")
    if command_arg:
        if (specified_user_id := str(command_arg)) == "*" or specified_user_id.isdigit():
            if user_id not in read_admin_list():
                await manually_bbs_sign.finish("⚠️你暂无权限执行此操作，只有管理员名单中的用户可以执行此操作")
            else:
                if specified_user_id == "*":
                    await manually_bbs_sign.send("⏳开始为所有用户执行米游币任务...")
                    for user_id_, user_ in get_unique_users():
                        await manually_bbs_sign.send(f"⏳开始为用户 {user_id_} 执行米游币任务...")
                        await perform_bbs_sign(
                            user=user_,
                            user_ids=[],
                            matcher=matcher
                        )
                else:
                    specified_user = PluginDataManager.plugin_data.users.get(specified_user_id)
                    if not specified_user:
                        await manually_bbs_sign.finish(f"⚠️未找到用户 {specified_user_id}")
                    await manually_bbs_sign.send(f"⏳开始为用户 {specified_user_id} 执行米游币任务...")
                    await perform_bbs_sign(
                        user=specified_user,
                        user_ids=[],
                        matcher=matcher
                    )
    else:
        await manually_bbs_sign.send("⏳开始执行米游币任务...")
        await perform_bbs_sign(user=user, user_ids=[user_id], matcher=matcher)


class NoteNoticeStatus(BaseModel):
    """
    账号便笺通知状态
    """
    genshin = GenshinNoteNotice()
    starrail = StarRailNoteNotice()


note_notice_status: Dict[str, NoteNoticeStatus] = {}
"""记录账号对应的便笺通知状态"""

manually_genshin_note_check = on_command(
    plugin_config.preference.command_start + '原神便笺',
    aliases={
        plugin_config.preference.command_start + '便笺',
        plugin_config.preference.command_start + '便签',
        plugin_config.preference.command_start + '原神便签',
    },
    priority=5,
    block=True
)

CommandRegistry.set_usage(
    manually_genshin_note_check,
    CommandUsage(
        name="原神便笺",
        description="手动查看原神实时便笺，即原神树脂、洞天财瓮等信息"
    )
)


@manually_genshin_note_check.handle()
async def _(event: Union[GeneralMessageEvent], matcher: Matcher):
    """
    手动查看原神便笺
    """
    user_id = event.get_user_id()
    user = PluginDataManager.plugin_data.users.get(user_id)
    if not user or not user.accounts:
        await manually_game_sign.finish(f"⚠️你尚未绑定米游社账户，请先使用『{COMMAND_BEGIN}登录』进行登录")
    await genshin_note_check(user=user, user_ids=[user_id], matcher=matcher)


manually_starrail_note_check = on_command(
    plugin_config.preference.command_start + '星穹铁道便笺',
    aliases={
        plugin_config.preference.command_start + '铁道便笺',
        plugin_config.preference.command_start + '铁道便签',
    },
    priority=5,
    block=True
)

CommandRegistry.set_usage(
    manually_starrail_note_check,
    CommandUsage(
        name="星穹铁道便笺",
        description="手动查看星穹铁道实时便笺，即开拓力、每日实训、每周模拟宇宙积分等信息"
    )
)


@manually_starrail_note_check.handle()
async def _(event: Union[GeneralMessageEvent], matcher: Matcher):
    """
    手动查看星穹铁道便笺（sr）
    """
    user_id = event.get_user_id()
    user = PluginDataManager.plugin_data.users.get(user_id)
    if not user or not user.accounts:
        await manually_game_sign.finish(f"⚠️你尚未绑定米游社账户，请先使用『{COMMAND_BEGIN}登录』进行登录")
    await starrail_note_check(user=user, user_ids=[user_id], matcher=matcher)


async def perform_game_sign(
        user: UserData,
        user_ids: Iterable[str],
        matcher: Matcher = None,
        event: Union[GeneralMessageEvent] = None
):
    """
    执行游戏签到函数，并发送给用户签到消息。

    :param user: 用户数据
    :param user_ids: 发送通知的所有用户ID
    :param matcher: 事件响应器
    :param event: 事件
    """
    failed_accounts = []
    for account in user.accounts.values():
        # 自动签到时，要求用户打开了签到功能；手动签到时都可以调用执行。
        if not matcher and not account.enable_game_sign:
            continue
        signed = False
        """是否已经完成过签到"""
        game_record_status, records = await get_game_record(account)
        if not game_record_status:
            if matcher:
                await matcher.send(f"⚠️账户 {account.display_name} 获取游戏账号信息失败，请重新尝试")
            else:
                for user_id in user_ids:
                    await send_private_msg(
                        user_id=user_id,
                        message=f"⚠️账户 {account.display_name} 获取游戏账号信息失败，请重新尝试"
                    )
            continue
        games_has_record = []
        for class_type in BaseGameSign.available_game_signs:
            signer = class_type(account, records)
            if not signer.has_record:
                continue
            else:
                games_has_record.append(signer)
            get_info_status, info = await signer.get_info(account.platform)
            if not get_info_status:
                if matcher:
                    await matcher.send(f"⚠️账户 {account.display_name} 获取签到记录失败")
                else:
                    for user_id in user_ids:
                        await send_private_msg(
                            user_id=user_id,
                            message=f"⚠️账户 {account.display_name} 获取签到记录失败"
                        )
            else:
                signed = info.is_sign

            # 若没签到，则进行签到功能；若获取今日签到情况失败，仍可继续
            if (get_info_status and not info.is_sign) or not get_info_status:
                sign_status, mmt_data = await signer.sign(account.platform)
                if sign_status.need_verify:
                    if plugin_config.preference.geetest_url or user.geetest_url:
                        if matcher:
                            await matcher.send("⏳正在尝试完成人机验证，请稍后...")
                        geetest_result = await get_validate(user, mmt_data.gt, mmt_data.challenge)
                        sign_status, _ = await signer.sign(account.platform, mmt_data, geetest_result)

                if not sign_status and (user.enable_notice or matcher):
                    if sign_status.login_expired:
                        message = f"⚠️账户 {account.display_name} 🎮『{signer.name}』签到时服务器返回登录失效，请尝试重新登录绑定账户"
                    elif sign_status.need_verify:
                        message = (f"⚠️账户 {account.display_name} 🎮『{signer.name}』签到时可能遇到验证码拦截，"
                                   "请尝试使用命令『/账号设置』更改设备平台，若仍失败请手动前往米游社签到")
                    else:
                        message = f"⚠️账户 {account.display_name} 🎮『{signer.name}』签到失败，请稍后再试"
                    if matcher:
                        await matcher.send(message)
                    elif user.enable_notice:
                        for user_id in user_ids:
                            await send_private_msg(user_id=user_id, message=message)
                    await asyncio.sleep(plugin_config.preference.sleep_time)
                    continue

                await asyncio.sleep(plugin_config.preference.sleep_time)

            # 用户打开通知或手动签到时，进行通知
            if user.enable_notice or matcher:
                onebot_img_msg, saa_img, qq_guild_img_msg = "", "", ""
                get_info_status, info = await signer.get_info(account.platform)
                get_award_status, awards = await signer.get_rewards()
                if not get_info_status or not get_award_status:
                    msg = f"⚠️账户 {account.display_name} 🎮『{signer.name}』获取签到结果失败！请手动前往米游社查看"
                else:
                    award = awards[info.total_sign_day - 1]
                    if info.is_sign:
                        status = "签到成功！" if not signed else "已经签到过了"
                        msg = f"🪪账户 {account.display_name}" \
                              f"\n🎮『{signer.name}』" \
                              f"\n🎮状态: {status}" \
                              f"\n{signer.record.nickname}·{signer.record.level}" \
                              "\n\n🎁今日签到奖励：" \
                              f"\n{award.name} * {award.cnt}" \
                              f"\n\n📅本月签到次数：{info.total_sign_day}"
                        img_file = await get_file(award.icon)
                        onebot_img_msg = OneBotV11MessageSegment.image(img_file)
                        saa_img = Image(img_file)
                        qq_guild_img_msg = QQGuildMessageSegment.file_image(img_file)
                    else:
                        msg = (f"⚠️账户 {account.display_name} 🎮『{signer.name}』签到失败！请尝试重新签到，"
                               "若多次失败请尝试重新登录绑定账户")
                if matcher:
                    try:
                        if isinstance(event, OneBotV11MessageEvent):
                            await matcher.send(msg + onebot_img_msg)
                        elif isinstance(event, QQGuildMessageEvent):
                            await matcher.send(msg)
                            await matcher.send(qq_guild_img_msg)
                    except (ActionFailed, AuditException):
                        pass
                else:
                    for adapter in get_adapters().values():
                        if isinstance(adapter, OneBotV11Adapter):
                            for user_id in user_ids:
                                await send_private_msg(use=adapter, user_id=user_id, message=msg + saa_img)
                        elif isinstance(adapter, QQGuildAdapter):
                            for user_id in user_ids:
                                await send_private_msg(use=adapter, user_id=user_id, message=msg)
                                await send_private_msg(use=adapter, user_id=user_id, message=qq_guild_img_msg)
            await asyncio.sleep(plugin_config.preference.sleep_time)

        if not games_has_record:
            if matcher:
                await matcher.send(f"⚠️您的米游社账户 {account.display_name} 下不存在任何游戏账号，已跳过签到")
            else:
                for user_id in user_ids:
                    await send_private_msg(
                        user_id=user_id,
                        message=f"⚠️您的米游社账户 {account.display_name} 下不存在任何游戏账号，已跳过签到"
                    )

    # 如果全部登录失效，则关闭通知
    if len(failed_accounts) == len(user.accounts):
        user.enable_notice = False
        PluginDataManager.write_plugin_data()


async def perform_bbs_sign(user: UserData, user_ids: Iterable[str], matcher: Matcher = None):
    """
    执行米游币任务函数，并发送给用户任务执行消息。

    :param user: 用户数据
    :param user_ids: 发送通知的所有用户ID
    :param matcher: 事件响应器
    """
    failed_accounts = []
    for account in user.accounts.values():
        # 自动执行米游币任务时，要求用户打开了米游币任务功能；手动执行米游币任务时都可以调用执行。
        if not matcher and not account.enable_mission:
            continue

        missions_state_status, missions_state = await get_missions_state(account)
        if not missions_state_status:
            if missions_state_status.login_expired:
                if matcher:
                    await matcher.send(f'⚠️账户 {account.display_name} 登录失效，请重新登录')
                else:
                    for user_id in user_ids:
                        await send_private_msg(
                            user_id=user_id,
                            message=f'⚠️账户 {account.display_name} 登录失效，请重新登录'
                        )
            if matcher:
                await matcher.send(f'⚠️账户 {account.display_name} 获取任务完成情况请求失败，你可以手动前往App查看')
            else:
                for user_id in user_ids:
                    await send_private_msg(
                        user_id=user_id,
                        message=f'⚠️账户 {account.display_name} 获取任务完成情况请求失败，你可以手动前往App查看'
                    )
            continue
        myb_before_mission = missions_state.current_myb

        # 在此处进行判断。因为如果在多个分区执行任务，会在完成之前就已经达成米游币任务目标，导致其他分区任务不会执行。
        finished = all(current == mission.threshold for mission, current in missions_state.state_dict.values())
        if not finished:
            if not account.mission_games:
                await matcher.send(
                    f'⚠️🆔账户 {account.display_name} 未设置米游币任务目标分区，将跳过执行')
            for class_name in account.mission_games:
                class_type = BaseMission.available_games.get(class_name)
                if not class_type:
                    if matcher:
                        await matcher.send(
                            f'⚠️🆔账户 {account.display_name} 米游币任务目标分区『{class_name}』未找到，将跳过该分区')
                    continue
                mission_obj = class_type(account)
                if matcher:
                    await matcher.send(f'🆔账户 {account.display_name} ⏳开始在分区『{class_type.name}』执行米游币任务...')

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
                        sign_status, sign_points = await mission_obj.sign(user)
                    elif key_name == BaseMission.VIEW:
                        read_status = await mission_obj.read()
                    elif key_name == BaseMission.LIKE:
                        like_status = await mission_obj.like()
                    elif key_name == BaseMission.SHARE:
                        share_status = await mission_obj.share()

                if matcher:
                    await matcher.send(
                        f"🆔账户 {account.display_name} 🎮『{class_type.name}』米游币任务执行情况：\n"
                        f"📅签到：{'✓' if sign_status else '✕'} +{sign_points or '0'} 米游币🪙\n"
                        f"📰阅读：{'✓' if read_status else '✕'}\n"
                        f"❤️点赞：{'✓' if like_status else '✕'}\n"
                        f"↗️分享：{'✓' if share_status else '✕'}"
                    )

        # 用户打开通知或手动任务时，进行通知
        if user.enable_notice or matcher:
            missions_state_status, missions_state = await get_missions_state(account)
            if not missions_state_status:
                if missions_state_status.login_expired:
                    if matcher:
                        await matcher.send(f'⚠️账户 {account.display_name} 登录失效，请重新登录')
                    else:
                        for user_id in user_ids:
                            await send_private_msg(
                                user_id=user_id,
                                message=f'⚠️账户 {account.display_name} 登录失效，请重新登录'
                            )
                    continue
                if matcher:
                    await matcher.send(
                        f'⚠️账户 {account.display_name} 获取任务完成情况请求失败，你可以手动前往App查看')
                else:
                    for user_id in user_ids:
                        await send_private_msg(
                            user_id=user_id,
                            message=f'⚠️账户 {account.display_name} 获取任务完成情况请求失败，你可以手动前往App查看'
                        )
                continue
            if all(current == mission.threshold for mission, current in missions_state.state_dict.values()):
                notice_string = "🎉已完成今日米游币任务"
            else:
                notice_string = "⚠️今日米游币任务未全部完成"

            msg = f"{notice_string}" \
                  f"\n🆔账户 {account.display_name}"
            for key_name, (mission, current) in missions_state.state_dict.items():
                if key_name == BaseMission.SIGN:
                    mission_name = "📅签到"
                elif key_name == BaseMission.VIEW:
                    mission_name = "📰阅读"
                elif key_name == BaseMission.LIKE:
                    mission_name = "❤️点赞"
                elif key_name == BaseMission.SHARE:
                    mission_name = "↗️分享"
                else:
                    mission_name = mission.mission_key
                msg += f"\n{mission_name}：{'✓' if current >= mission.threshold else '✕'}"
            msg += f"\n🪙获得米游币: {missions_state.current_myb - myb_before_mission}" \
                   f"\n💰当前米游币: {missions_state.current_myb}"

            if matcher:
                await matcher.send(msg)
            else:
                for user_id in user_ids:
                    await send_private_msg(user_id=user_id, message=msg)

    # 如果全部登录失效，则关闭通知
    if len(failed_accounts) == len(user.accounts):
        user.enable_notice = False
        PluginDataManager.write_plugin_data()


async def genshin_note_check(user: UserData, user_ids: Iterable[str], matcher: Matcher = None):
    """
    查看原神实时便笺函数，并发送给用户任务执行消息。

    :param user: 用户对象
    :param user_ids: 发送通知的所有用户ID
    :param matcher: 事件响应器
    """
    for account in user.accounts.values():
        note_notice_status.setdefault(account.bbs_uid, NoteNoticeStatus())
        genshin_notice = note_notice_status[account.bbs_uid].genshin
        if account.enable_resin or matcher:
            genshin_board_status, note = await genshin_note(account)
            if not genshin_board_status:
                if matcher:
                    if genshin_board_status.login_expired:
                        await matcher.send(f'⚠️账户 {account.display_name} 登录失效，请重新登录')
                    elif genshin_board_status.no_genshin_account:
                        await matcher.send(f'⚠️账户 {account.display_name} 没有绑定任何原神账户，请绑定后再重试')
                    elif genshin_board_status.need_verify:
                        await matcher.send(f'⚠️账户 {account.display_name} 获取实时便笺时被人机验证阻拦')
                    await matcher.send(f'⚠️账户 {account.display_name} 获取实时便笺请求失败，你可以手动前往App查看')
                continue

            msg = ''
            # 手动查询体力时，无需判断是否溢出
            if not matcher:
                do_notice = False
                """记录是否需要提醒"""
                # 体力溢出提醒
                if note.current_resin >= account.user_resin_threshold:
                    # 防止重复提醒
                    if not genshin_notice.current_resin_full:
                        if note.current_resin == 160:
                            genshin_notice.current_resin_full = True
                            msg += '❕您的树脂已经满啦\n'
                            do_notice = True
                        elif not genshin_notice.current_resin:
                            genshin_notice.current_resin_full = False
                            genshin_notice.current_resin = True
                            msg += '❕您的树脂已达到提醒阈值\n'
                            do_notice = True
                else:
                    genshin_notice.current_resin = False
                    genshin_notice.current_resin_full = False

                # 洞天财瓮溢出提醒
                if note.current_home_coin == note.max_home_coin:
                    # 防止重复提醒
                    if not genshin_notice.current_home_coin:
                        genshin_notice.current_home_coin = True
                        msg += '❕您的洞天财瓮已经满啦\n'
                        do_notice = True
                else:
                    genshin_notice.current_home_coin = False

                # 参量质变仪就绪提醒
                if note.transformer:
                    if note.transformer_text == '已准备就绪':
                        # 防止重复提醒
                        if not genshin_notice.transformer:
                            genshin_notice.transformer = True
                            msg += '❕您的参量质变仪已准备就绪\n\n'
                            do_notice = True
                    else:
                        genshin_notice.transformer = False
                else:
                    genshin_notice.transformer = True

                if not do_notice:
                    logger.info(f"原神实时便笺：账户 {account.display_name} 树脂:{note.current_resin},未满足推送条件")
                    return

            msg += "❖原神·实时便笺❖" \
                   f"\n🆔账户 {account.display_name}" \
                   f"\n⏳树脂数量：{note.current_resin} / 160" \
                   f"\n⏱️树脂{note.resin_recovery_text}" \
                   f"\n🕰️探索派遣：{note.current_expedition_num} / {note.max_expedition_num}" \
                   f"\n📅每日委托：{4 - note.finished_task_num} 个任务未完成" \
                   f"\n💰洞天财瓮：{note.current_home_coin} / {note.max_home_coin}" \
                   f"\n🎰参量质变仪：{note.transformer_text if note.transformer else 'N/A'}"
            if matcher:
                await matcher.send(msg)
            else:
                for user_id in user_ids:
                    await send_private_msg(user_id=user_id, message=msg)


async def starrail_note_check(user: UserData, user_ids: Iterable[str], matcher: Matcher = None):
    """
    查看星铁实时便笺函数，并发送给用户任务执行消息。

    :param user: 用户对象
    :param user_ids: 发送通知的所有用户ID
    :param matcher: 事件响应器
    """
    for account in user.accounts.values():
        note_notice_status.setdefault(account.bbs_uid, NoteNoticeStatus())
        starrail_notice = note_notice_status[account.bbs_uid].starrail
        if account.enable_resin or matcher:
            starrail_board_status, note = await starrail_note(account)
            if not starrail_board_status:
                if matcher:
                    if starrail_board_status.login_expired:
                        await matcher.send(f'⚠️账户 {account.display_name} 登录失效，请重新登录')
                    elif starrail_board_status.no_starrail_account:
                        await matcher.send(f'⚠️账户 {account.display_name} 没有绑定任何星铁账户，请绑定后再重试')
                    elif starrail_board_status.need_verify:
                        await matcher.send(f'⚠️账户 {account.display_name} 获取实时便笺时被人机验证阻拦')
                    await matcher.send(f'⚠️账户 {account.display_name} 获取实时便笺请求失败，你可以手动前往App查看')
                continue

            msg = ''
            # 手动查询体力时，无需判断是否溢出
            if not matcher:
                do_notice = False
                """记录是否需要提醒"""
                # 体力溢出提醒
                if note.current_stamina >= account.user_stamina_threshold:
                    # 防止重复提醒
                    if not starrail_notice.current_stamina_full:
                        if note.current_stamina >= note.max_stamina:
                            starrail_notice.current_stamina_full = True
                            msg += '❕您的开拓力已经溢出\n'
                            if note.current_train_score != note.max_train_score:
                                msg += '❕您的每日实训未完成\n'
                            do_notice = True
                        elif not starrail_notice.current_stamina:
                            starrail_notice.current_stamina_full = False
                            starrail_notice.current_stamina = True
                            msg += '❕您的开拓力已达到提醒阈值\n'
                            if note.current_train_score != note.max_train_score:
                                msg += '❕您的每日实训未完成\n'
                            do_notice = True
                else:
                    starrail_notice.current_stamina = False
                    starrail_notice.current_stamina_full = False

                # 每周模拟宇宙积分提醒
                if note.current_rogue_score != note.max_rogue_score:
                    if plugin_config.preference.notice_time:
                        msg += '❕您的模拟宇宙积分还没打满\n\n'
                        do_notice = True

                if not do_notice:
                    logger.info(
                        f"崩铁实时便笺：账户 {account.display_name} 开拓力:{note.current_stamina},未满足推送条件")
                    return

            msg += "❖星穹铁道·实时便笺❖" \
                   f"\n🆔账户 {account.display_name}" \
                   f"\n⏳开拓力数量：{note.current_stamina} / {note.max_stamina}" \
                   f"\n⏱开拓力{note.stamina_recover_text}" \
                   f"\n📒每日实训：{note.current_train_score} / {note.max_train_score}" \
                   f"\n📅每日委托：{note.accepted_expedition_num} / 4" \
                   f"\n🌌模拟宇宙：{note.current_rogue_score} / {note.max_rogue_score}"

            if matcher:
                await matcher.send(msg)
            else:
                for user_id in user_ids:
                    await send_private_msg(user_id=user_id, message=msg)


async def weibo_code_check(user: UserData, user_ids: Iterable[str], matcher: Matcher = None):
    """
    是否开启微博兑换码功能的函数，并发送给用户任务执行消息。

    :param user: 用户对象
    :param user_ids: 发送通知的所有用户ID
    :param matcher: nonebot ``Matcher``
    """
    msg, img = None, None
    if user.enable_weibo:
        # account = UserAccount(account) 
        weibo = WeiboCode(user)
        result = await weibo.get_code_list()
        try:
            if isinstance(result, tuple):
                msg, img = result
            else:
                msg = result
        except Exception:
            pass
        if matcher:
            if img:
                onebot_img_msg = OneBotV11MessageSegment.image(await get_file(img))
                messages = msg + onebot_img_msg
            else:
                messages = msg
            await matcher.send(messages)
        else:
            if img and '无' not in msg:
                saa_img = Image(await get_file(img))
                messages = msg + saa_img
                for user_id in user_ids:
                    await send_private_msg(user_id=user_id, message=messages)
    else:
        message = "未开启微博功能"
        if matcher:
            await matcher.send(message)


@scheduler.scheduled_job("cron", hour='0', minute='0', id="daily_goodImg_update")
def daily_update():
    """
    每日图片生成函数
    """
    logger.info(f"{plugin_config.preference.log_head}后台开始生成每日商品图片")
    threading.Thread(target=generate_image).start()


@scheduler.scheduled_job("cron",
                         hour=plugin_config.preference.plan_time.split(':')[0],
                         minute=plugin_config.preference.plan_time.split(':')[1],
                         id="daily_schedule")
async def daily_schedule():
    """
    自动米游币任务、游戏签到函数
    """
    logger.info(f"{plugin_config.preference.log_head}开始执行每日自动任务")
    for user_id, user in get_unique_users():
        user_ids = [user_id] + list(get_all_bind(user_id))
        await perform_game_sign(user=user, user_ids=user_ids)
        await perform_bbs_sign(user=user, user_ids=user_ids)
    logger.info(f"{plugin_config.preference.log_head}每日自动任务执行完成")


@scheduler.scheduled_job("interval",
                         minutes=plugin_config.preference.resin_interval,
                         id="resin_check")
async def auto_note_check():
    """
    自动查看实时便笺
    """
    logger.info(f"{plugin_config.preference.log_head}开始执行自动便笺检查")
    for user_id, user in get_unique_users():
        user_ids = [user_id] + list(get_all_bind(user_id))
        await genshin_note_check(user=user, user_ids=user_ids)
        await starrail_note_check(user=user, user_ids=user_ids)
    logger.info(f"{plugin_config.preference.log_head}自动便笺检查执行完成")


@scheduler.scheduled_job("cron",
                         hour=str(int(plugin_config.preference.plan_time.split(':')[0]) + 1),
                         minute=plugin_config.preference.plan_time.split(':')[1],
                         id="weibo_schedule")
async def auto_weibo_check():
    """
    每日检查微博活动签到兑换码函数
    """
    logger.info(f"{plugin_config.preference.log_head}开始执行微博自动任务")
    for user_id, user in get_unique_users():
        user_ids = [user_id] + list(get_all_bind(user_id))
        await weibo_code_check(user=user, user_ids=user_ids)
    logger.info(f"{plugin_config.preference.log_head}微博自动任务执行完成")


manually_weibo_check = on_command(plugin_config.preference.command_start + 'wb兑换', priority=5, block=True)


@manually_weibo_check.handle()
async def weibo_schedule(event: Union[GeneralMessageEvent], matcher: Matcher):
    if isinstance(event, GeneralGroupMessageEvent):
        await matcher.send("⚠️为了保护您的隐私，请私聊进行查询。")
    else:
        user_id = event.get_user_id()
        user = PluginDataManager.plugin_data.users.get(user_id)
        await weibo_code_check(user=user, user_ids=[user_id], matcher=matcher)
