from enum import Enum


class ScreenState(Enum):

    # 大世界部分
    NORMAL_IN_WORLD: str = '大世界'
    """大世界主界面 右上角有角色的图标"""

    PHONE_MENU: str = '菜单'
    """菜单 有显示开拓等级"""

    # 二级页面 - 指南
    GUIDE: str = '星际和平指南'
    """星际和平指南"""

    GUIDE_OPERATION_BRIEFING: str = '行动摘要'
    """星际和平指南 - 行动摘要"""

    GUIDE_DAILY_TRAINING: str = '每日实训'
    """星际和平指南 - 每日实训"""

    GUIDE_SURVIVAL_INDEX: str = '生存索引'
    """星际和平指南 - 生存索引"""

    GUIDE_SIM_UNI: str = '模拟宇宙'
    """星际和平指南 - 模拟宇宙"""

    GUIDE_TREASURES_LIGHTWARD: str = '逐光捡金'
    """星际和平指南 - 逐光捡金"""

    GUIDE_STRATEGIC_TRAINING: str = '战术训练'
    """星际和平指南 - 战术训练"""

    FORGOTTEN_HALL: str = '忘却之庭'
    """忘却之庭"""

    MEMORY_OF_CHAOS: str = '混沌回忆'
    """忘却之庭 - 混沌回忆"""

    PURE_FICTION: str = '虚构叙事'
    """虚构叙事"""

    NAMELESS_HONOR: str = '无名勋礼'
    """无名勋礼"""

    NH_REWARDS: str = '奖励'
    """无名勋礼 - 奖励"""

    NH_MISSIONS: str = '任务'
    """无名勋礼 - 任务"""

    NH_TREASURE: str = '星海宝藏'
    """无名勋礼 - 星海宝藏"""

    INVENTORY: str = '背包'
    """背包"""

    SYNTHESIZE: str = '合成'
    """合成"""

    TEAM: str = '队伍'
    """队伍"""

    SIM_TYPE_NORMAL: str = '模拟宇宙'
    """模拟宇宙 - 普通"""

    SIM_TYPE_EXTEND: str = '扩展装置'
    """模拟宇宙 - 拓展装置"""

    SIM_TYPE_GOLD: str = '黄金与机械'
    """模拟宇宙 - 黄金与机械"""

    SIM_PATH: str = '命途'
    """模拟宇宙 - 命途"""

    SIM_BLESS: str = '选择祝福'
    """模拟宇宙 - 选择祝福"""

    SIM_DROP_BLESS: str = '丢弃祝福'
    """模拟宇宙 - 丢弃祝福"""

    SIM_UPGRADE_BLESS: str = '祝福强化'
    """模拟宇宙 - 祝福强化"""

    SIM_CURIOS: str = '选择奇物'
    """模拟宇宙 - 选择奇物"""

    SIM_DROP_CURIOS: str = '丢弃奇物'
    """模拟宇宙 - 丢弃奇物"""

    SIM_EVENT: str = '事件'
    """模拟宇宙 - 事件"""

    SIM_REWARD: str = '沉浸奖励'
    """模拟宇宙 - 沉浸奖励"""

    SIM_UNI_REGION: str = '模拟宇宙-区域'
    """模拟宇宙 - 区域"""

    BATTLE: str = '战斗'
    """所有战斗画面通用 - 右上角有暂停符号"""

    BATTLE_FAIL: str = '战斗失败'
    """所有战斗画面通用 - 右上角有暂停符号"""

    EMPTY_TO_CLOSE: str = '点击空白处关闭'
    """所有画面通用 - 下方有 点击空白处关闭"""

    TP_BATTLE_SUCCESS: str = '挑战成功'
    """开拓力副本 - 挑战成功"""

    TP_BATTLE_FAIL: str = '战斗失败'
    """开拓力副本 - 战斗失败"""
