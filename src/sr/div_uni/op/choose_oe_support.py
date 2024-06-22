from typing import Optional

from basic.i18_utils import gt
from sr.context import Context
from sr.div_uni.screen_div_uni import ScreenDivUni
from sr.operation import StateOperation, OperationOneRoundResult, StateOperationNode
from sr.operation.battle.choose_support import ChooseSupport


class ChooseOeSupport(StateOperation):

    def __init__(self, ctx: Context, character_id: Optional[str]):
        """
        在饰品提取画面 选择支援
        """
        super().__init__(ctx, op_name=f"{gt('饰品提取', 'ui')} {gt('选择支援', 'ui')}")

        self.character_id: str = character_id
        """支援角色ID"""

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        check_screen = StateOperationNode('识别画面', self.check_screen)

        click_support = StateOperationNode('点击支援按钮', self.click_support)
        self.add_edge(check_screen, click_support)

        choose_support = StateOperationNode('选择支援', op=ChooseSupport(self.ctx, self.character_id))
        self.add_edge(click_support, choose_support)

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        if self.character_id is None:
            return self.round_success('无需支援')

    def check_screen(self) -> OperationOneRoundResult:
        """
        识别画面
        :return:
        """
        screen = self.screenshot()
        area = ScreenDivUni.OE_TITLE.value

        if self.find_area(area, screen):
            return self.round_success()
        else:
            return self.round_retry(f'未在{area.status}画面', wait_round_time=0.5)

    def click_support(self) -> OperationOneRoundResult:
        """
        点击支援按钮
        :return:
        """
        area = ScreenDivUni.OE_SUPPORT_BTN.value
        if self.ctx.controller.click(area.center):
            return self.round_success()
        else:
            return self.round_retry(f'点击{area.status}失败', wait_round_time=0.5)
