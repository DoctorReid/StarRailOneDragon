class PhoneMenuItem:

    def __init__(self, template_id: str, cn: str):
        self.template_id: str = template_id
        self.cn: str = cn


STORE = PhoneMenuItem('phone_menu_item_01_store', '商店')
FRIENDS = PhoneMenuItem('phone_menu_item_02_friends', '好友')
ASSIGNMENTS = PhoneMenuItem('phone_menu_item_03_assignments', '委托')
TRAVEL_LOG = PhoneMenuItem('phone_menu_item_04_travel_log', '旅情事记')
SYNTHESIZE = PhoneMenuItem('phone_menu_item_05_synthesize', '合成')
ACHIEVED = PhoneMenuItem('phone_menu_item_06_achieved', '成就')
MESSAGES = PhoneMenuItem('phone_menu_item_07_messages', '短信')
NAMELESS_HONOR = PhoneMenuItem('phone_menu_item_08_nameless_honor', '无名勋礼')
WARP = PhoneMenuItem('phone_menu_item_09_warp', '跃迁')
CHARACTERS = PhoneMenuItem('phone_menu_item_10_characters', '角色')
INTERASTRAL_GUIDE = PhoneMenuItem('phone_menu_item_11_interastral_guide', '指南')
DATA_BANK = PhoneMenuItem('phone_menu_item_12_data_bank', '智库')
BOOKSHELF = PhoneMenuItem('phone_menu_item_13_bookshelf', '书架')
TUTORIALS = PhoneMenuItem('phone_menu_item_14_tutorials', '教学目录')
TEAM_SETUP = PhoneMenuItem('phone_menu_item_15_team_setup', '编队')
INVENTORY = PhoneMenuItem('phone_menu_item_16_inventory', '背包')
MISSIONS = PhoneMenuItem('phone_menu_item_17_missions', '任务')
NAVIGATION = PhoneMenuItem('phone_menu_item_18_navigation', '导航')
BUG_REPORT = PhoneMenuItem('phone_menu_item_19_bug_report', '问题反馈')
OFFICIAL_COMMUNITIES = PhoneMenuItem('phone_menu_item_20_official_communities', '官方社区')
SPECIAL_EVENTS = PhoneMenuItem('phone_menu_item_21_special_events', '特别活动')
VERSION_INFO = PhoneMenuItem('phone_menu_item_22_version_info', '版本热点')
ACCOUNT_SETTINGS = PhoneMenuItem('phone_menu_item_23_account_settings', '账户设置')
EMAILS = PhoneMenuItem('phone_menu_item_24_email', '邮件')
ANNOUNCEMENT = PhoneMenuItem('phone_menu_item_25_announcement', '公告')
SETTINGS = PhoneMenuItem('phone_menu_item_26_settings', '设置')
PHOTO = PhoneMenuItem('phone_menu_item_27_photo', '拍照')
