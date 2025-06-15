class DivUniReward:

    def __init__(self, category: str, level: int, name: str):
        """
        差分宇宙中 可能出现的奖励的基类
        - 奇物
        - 祝福
        - 方程
        - 金血祝颂
        """
        self.category: str = category
        self.level: int = level
        self.name: str = name

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "level": self.level,
            "name": self.name
        }

    @property
    def display_name(self) -> str:
        """
        游戏中显示的完整名称
        """
        return self.name
