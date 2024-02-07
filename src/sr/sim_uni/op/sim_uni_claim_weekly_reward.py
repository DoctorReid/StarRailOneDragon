from typing import ClassVar

from cv2.typing import MatLike

from basic.i18_utils import gt
from sr.context import Context
from sr.image.sceenshot import screen_state
from sr.operation import StateOperation, OperationOneRoundResult, Operation, StateOperationNode, StateOperationEdge
from sr.screen_area.sim_uni import ScreenSimUniEntry


class SimUniClaimWeeklyReward(StateOperation):

    STATUS_WITH_REWARD: ClassVar[str] = '可领取奖励'

    def __init__(self, ctx: Context):
        """
        模拟宇宙 领取每周的积分奖励
        需要在模拟宇宙的主页面中使用
        :param ctx:
        """
        edges = []

        wait = StateOperationNode('等待加载', self._wait_ui)
        check = StateOperationNode('检查奖励', self._check_reward)
        edges.append(StateOperationEdge(wait, check))

        claim = StateOperationNode('领取奖励', self._claim_reward)
        edges.append(StateOperationEdge(check, claim, status=SimUniClaimWeeklyReward.STATUS_WITH_REWARD))

        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('获取每周积分奖励', 'ui')),
                         edges=edges
                         )

    def _wait_ui(self) -> OperationOneRoundResult:
        """
        等待加载页面
        :return:
        """
        screen = self.screenshot()
        state = screen_state.get_sim_uni_initial_screen_state(screen, self.ctx.im, self.ctx.ocr)

        if state in [screen_state.ScreenState.SIM_TYPE_EXTEND.value, screen_state.ScreenState.SIM_TYPE_NORMAL.value]:
            return Operation.round_success()
        else:
            return Operation.round_retry('未在模拟宇宙画面', wait=1)

    def _check_reward(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        return self._check_reward_by_screen(screen)

    def _check_reward_by_screen(self, screen: MatLike) -> OperationOneRoundResult:
        """
        根据截图 判断并点击奖励图标
        :param screen:
        :return:
        """
        area = ScreenSimUniEntry.WEEKLY_REWARD_ICON.value
        click = self.find_and_click_area(area, screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(SimUniClaimWeeklyReward.STATUS_WITH_REWARD, wait=1)
        elif click == Operation.OCR_CLICK_NOT_FOUND:
            return Operation.round_success()
        else:
            return Operation.round_retry('点击奖励图标失败', wait=1)

    def _claim_reward(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        return self._claim_reward_by_screen(screen)

    def _claim_reward_by_screen(self, screen: MatLike) -> OperationOneRoundResult:
        """
        根据截图 点击一件领取
        :param screen: 屏幕截图
        :return:
        """
        area = ScreenSimUniEntry.WEEKLY_REWARD_CLAIM.value
        click = self.find_and_click_area(area, screen)

        if click == Operation.OCR_CLICK_SUCCESS:
            return Operation.round_success(wait=1)
        else:
            return Operation.round_retry('点击%s失败' % area.text, wait=1)

