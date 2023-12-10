from pydantic import BaseModel


class DailyTrainingMission(BaseModel):
    """实训任务类型"""

    id_cn: str
    """类型名称"""

    desc_cn: str
    """任务描述"""

    able: bool
    """是否可以执行"""


MISSION_DAILY_MISSION = DailyTrainingMission(id_cn='日常任务', desc_cn='完成1个日常任务', able=False)
MISSION_PATH = DailyTrainingMission(id_cn='侵蚀隧洞', desc_cn='完成1次侵蚀隧洞', able=False)
# MISSION_BUD1 = DailyTrainingMission(id_cn='拟造花萼金', desc_cn='完成1次拟造花萼金', able=False)
MISSION_BUD2 = DailyTrainingMission(id_cn='拟造花萼赤', desc_cn='完成1次拟造花萼赤', able=False)
MISSION_FORGOTTEN_HALL = DailyTrainingMission(id_cn='忘却之庭', desc_cn='使用1件消耗品', able=False)
MISSION_USE_CONSUMABLE = DailyTrainingMission(id_cn='使用消耗品', desc_cn='完成1次忘却之庭', able=False)
MISSION_SALVAGE_RELIC = DailyTrainingMission(id_cn='分解遗器', desc_cn='分解任意1件遗器', able=True)
MISSION_WEAKNESS_BREAK = DailyTrainingMission(id_cn='触发弱点', desc_cn='单场战斗中，触发3种不同属性的弱点击破', able=False)
MISSION_DEFEAT_ENEMY = DailyTrainingMission(id_cn='消灭敌人', desc_cn='累计消灭20个敌人', able=False)
MISSION_DESTRUCTIBLE_OBJECTS = DailyTrainingMission(id_cn='可破坏物', desc_cn='累计击碎3个可破坏物', able=True)


ALL_MISSION_LIST = [
    MISSION_DAILY_MISSION,
    MISSION_PATH,
    # MISSION_BUD1,
    MISSION_BUD2,
    MISSION_FORGOTTEN_HALL,
    MISSION_USE_CONSUMABLE,
    MISSION_SALVAGE_RELIC,
    MISSION_WEAKNESS_BREAK,
    MISSION_DEFEAT_ENEMY,
    MISSION_DESTRUCTIBLE_OBJECTS,
]