from enum import Enum

from basic import Rect
from sr.screen_area import ScreenArea


class ScreenLogin(Enum):

    LOGOUT = ScreenArea(pc_rect=Rect(1803, 290, 1851, 316), text='登出')
    LOGOUT_CONFIRM = ScreenArea(pc_rect=Rect(970, 542, 1185, 599), text='确定')

    ACCOUNT_INPUT = ScreenArea(pc_rect=Rect(688, 414, 1226, 467), text='输入手机号/邮箱', lcs_percent=0.5)
    PASSWORD_INPUT = ScreenArea(pc_rect=Rect(699, 509, 1221, 545), text='输入密码', lcs_percent=0.5)
    APPROVE = ScreenArea(pc_rect=Rect(683, 579, 707, 599))  # 同意条款

    SWITCH_PASSWORD = ScreenArea(pc_rect=Rect(853, 737, 984, 769), text='账号密码', lcs_percent=0.5)

    LOGIN_BTN = ScreenArea(pc_rect=Rect(688, 641, 1226, 693), text='进入游戏', lcs_percent=0.5)

    SERVER_START_GAME = ScreenArea(pc_rect=Rect(863, 808, 1078, 866), text='开始游戏', lcs_percent=0.5)  # 选择服务器画面
    CONFIRM_START_GAME = ScreenArea(pc_rect=Rect(900, 993, 1017, 1030), text='点击进入', lcs_percent=0.5)  # 确认进入游戏
