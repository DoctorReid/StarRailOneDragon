from one_dragon.base.geometry.rectangle import Rect
from sr_od.app.div_uni.entity.div_uni_reward import DivUniReward


class DivUniRewardPos:

    def __init__(self, reward: DivUniReward, rect: Rect):
        """
        差分宇宙中 出现的奖励未知
        """
        self.reward: DivUniReward = reward
        self.rect: Rect = rect
        self.is_new: bool = False
