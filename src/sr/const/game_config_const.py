# 游戏区服
# 各区服重置时间与UTC的偏移

SERVER_REGION_CN = "CN"  #国服
SERVER_REGION_OS_ASIA = "Asia"  #国际服亚服
SERVER_REGION_OS_AMERICA = "America"  #国际服美服
SERVER_REGION_OS_EUROPE = "Europe"  #国际服欧服
SERVER_REGION_OS_TW_HK_MO = "TW,HK,MO" #国际服台港澳服
SERVER_TIME_OFFSET = {
    SERVER_REGION_CN: 4,
    SERVER_REGION_OS_ASIA: 4,
    SERVER_REGION_OS_TW_HK_MO: 4,
    SERVER_REGION_OS_AMERICA: -9,
    SERVER_REGION_OS_EUROPE: -3,
}

# 疾跑模式
RUN_MODE_OFF = 0  # 不使用疾跑
RUN_MODE_BTN = 1  # 通过按键进入疾跑
RUN_MODE_AUTO = 2  # 长按进入疾跑

RUN_MODE = {
    '不启用': RUN_MODE_OFF,
    '通过按钮切换': RUN_MODE_BTN,
    '长按进入疾跑状态': RUN_MODE_AUTO
}

# 语言
LANG_CN = 'cn'
LANG_EN = 'en'

LANG_OPTS = {
    '简体中文': LANG_CN,
    'English': LANG_EN
}
