class DailyTrainingMission:

    def __init__(self, id_cn: str, desc_cn: str, able: bool):
        """
        实训任务
        :param id_cn: 类型名称
        :param desc_cn: 任务描述
        :param able: 是否可以执行
        """

        self.id_cn: str = id_cn
        """类型名称"""

        self.desc_cn: str = desc_cn
        """任务描述"""

        self.able: bool = able
        """是否可以执行"""


MISSION_DAILY_MISSION = DailyTrainingMission(id_cn='日常任务', desc_cn='完成1个日常任务', able=False)
MISSION_PATH = DailyTrainingMission(id_cn='侵蚀隧洞', desc_cn='完成1次侵蚀隧洞', able=False)
MISSION_BUD1 = DailyTrainingMission(id_cn='拟造花萼金', desc_cn='完成1次拟造花萼金', able=False)
MISSION_BUD2 = DailyTrainingMission(id_cn='拟造花萼赤', desc_cn='完成1次拟造花萼赤', able=False)
MISSION_FORGOTTEN_HALL = DailyTrainingMission(id_cn='忘却之庭', desc_cn='完成1次忘却之庭', able=False)
MISSION_SYNTHESIZE_CONSUMABLE = DailyTrainingMission(id_cn='合成消耗品', desc_cn='合成1次消耗品', able=True)
MISSION_USE_CONSUMABLE = DailyTrainingMission(id_cn='使用消耗品', desc_cn='使用1件消耗品', able=False)
MISSION_SALVAGE_RELIC = DailyTrainingMission(id_cn='分解遗器', desc_cn='分解任意1件遗器', able=True)
MISSION_WEAKNESS_BREAK = DailyTrainingMission(id_cn='触发弱点', desc_cn='单场战斗中，触发3种不同属性的弱点击破', able=False)
MISSION_DEFEAT_ENEMY = DailyTrainingMission(id_cn='消灭敌人', desc_cn='累计消灭20个敌人', able=False)
MISSION_DESTRUCTIBLE_OBJECTS = DailyTrainingMission(id_cn='可破坏物', desc_cn='累计击碎3个可破坏物', able=True)
MISSION_USE_TECHNIQUE = DailyTrainingMission(id_cn='施放秘技', desc_cn='累计施放2次秘技', able=True)
MISSION_TAKE_PHOTO = DailyTrainingMission(id_cn='拍照', desc_cn='拍照1次', able=True)


ALL_MISSION_LIST = [
    MISSION_DAILY_MISSION,
    MISSION_PATH,
    MISSION_BUD1,
    MISSION_BUD2,
    MISSION_FORGOTTEN_HALL,
    MISSION_USE_CONSUMABLE,
    MISSION_SALVAGE_RELIC,
    MISSION_WEAKNESS_BREAK,
    MISSION_DEFEAT_ENEMY,
    MISSION_DESTRUCTIBLE_OBJECTS,
    MISSION_USE_TECHNIQUE,
    MISSION_TAKE_PHOTO,
]
