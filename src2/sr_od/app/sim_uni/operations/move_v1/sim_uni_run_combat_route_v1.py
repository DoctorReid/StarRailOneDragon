class SimUniRunCombatRoute(SimUniRunRouteBase):

    def __init__(self, ctx: Context, world_num: int, level_type: SimUniLevelType, route: SimUniRoute,
                 config: Optional[SimUniChallengeConfig] = None,
                 ):
        super().__init__(ctx, world_num, level_type, route, config=config)

    def _before_route(self) -> OperationOneRoundResult:
        """
        如果是秘技开怪 且是上buff类的 就在路线运行前上buff
        :return:
        """
        if not self.config.technique_fight or not self.ctx.team_info.is_buff_technique or self.ctx.technique_used:
            return self.round_success()
        else:
            op = UseTechnique(self.ctx,
                              max_consumable_cnt=0 if self.config is None else self.config.max_consumable_cnt,
                              need_check_point=True,  # 检查秘技点是否足够 可以在没有或者不能用药的情况加快判断
                              trick_snack=self.ctx.game_config.use_quirky_snacks
                              )
            return self.round_by_op(op.execute())