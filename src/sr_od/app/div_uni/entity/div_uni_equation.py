from sr_od.app.div_uni.entity.div_uni_reward import DivUniReward


class DivUniEquation(DivUniReward):

    def __init__(
            self,
            category: str,
            level: int,
            name: str,
            path_list: list[str],
            path_cnt_list: list[int]
    ):
        DivUniReward.__init__(
            self,
            category=category,
            level=level,
            name=name
        )

        self.path_list: list[str] = path_list  # 所需命途
        self.path_cnt_list: list[int] = path_cnt_list  # 所需命途祝福的数量

    def to_dict(self) -> dict:
        result = DivUniReward.to_dict(self)
        result['path_list'] = self.path_list
        result['path_cnt_list'] = self.path_cnt_list
        return result
