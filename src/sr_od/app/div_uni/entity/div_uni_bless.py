from sr_od.app.div_uni.entity.div_uni_reward import DivUniReward


class DivUniBless(DivUniReward):

    def __init__(
            self,
            category: str,
            level: int,
            name: str,
    ):
        DivUniReward.__init__(
            self,
            category=category,
            level=level,
            name=name
        )
