from sr_od.operations.sr_operation import SrOperation


class SimUniRunRouteBase(SrOperation):

    def __init__(self, ctx: Context,
                 world_num: int,
                 level_type: SimUniLevelType,
                 route: SimUniRoute,
                 config: Optional[SimUniChallengeConfig] = None
                 ):
        """
        模拟宇宙 按照路线执行的基类
        """
        self.world_num: int = world_num
        self.level_type: SimUniLevelType = level_type
        self.route: Optional[SimUniRoute] = route
        self.current_pos: Optional[Point] = None
        self.config: Optional[SimUniChallengeConfig] = config

        before_route = StateOperationNode('指令前初始化', self._before_route)
        run_route = StateOperationNode('执行路线指令', self._run_route)
        after_route = StateOperationNode('区域特殊指令', self._after_route)
        go_next = StateOperationNode('下一层', self._go_next)

        super().__init__(ctx,
                         op_name='%s %s' % (
                             gt('模拟宇宙', 'ui'),
                             gt('区域-%s' % level_type.type_name, 'ui')
                         ),
                         nodes=[before_route, run_route, after_route, go_next]
                         )

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        self.current_pos = None

        return None

    def _before_route(self) -> OperationOneRoundResult:
        """
        执行路线前的初始化 由各类型楼层自行实现
        :return:
        """
        return self.round_success()

    def _run_route(self) -> OperationOneRoundResult:
        """
        执行下一个指令
        :return:
        """
        op = SimUniRunRouteOp(self.ctx, self.route, config=self.config, op_callback=self._update_pos)
        return self.round_by_op(op.execute())

    def _update_pos(self, op_result: OperationResult):
        """
        更新坐标
        :param op_result:
        :return:
        """
        if op_result.success:
            self.current_pos = op_result.data

    def _after_route(self) -> OperationOneRoundResult:
        """
        执行路线后的特殊操作 由各类型楼层自行实现
        :return:
        """
        return self.round_success()

    def _go_next(self) -> OperationOneRoundResult:
        """
        前往下一层
        :return:
        """
        op = MoveToNextLevel(self.ctx, level_type=self.level_type, route=self.route,
                             config=self.config,
                             current_pos=self.current_pos)

        return self.round_by_op(op.execute())