from typing import Callable, Optional, ClassVar

from cv2.typing import MatLike

from basic import Rect, str_utils
from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from sr.context.context import Context
from sr.image.sceenshot import screen_state
from sr.image.sceenshot.screen_state_enum import ScreenState
from sr.operation import StateOperation, OperationOneRoundResult, StateOperationNode, \
    StateOperationEdge


class SimUniReward(StateOperation):

    POWER_NUM_RECT: ClassVar[Rect] = Rect(623, 715, 655, 744)  # 开拓力数字部分
    QTY_RECT: ClassVar[Rect] = Rect(1060, 715, 1090, 744)  # 沉浸器数字部分
    CLOSE_REWARD_BTN: ClassVar[Rect] = Rect(1433, 331, 1492, 382)  # 关闭沉浸奖励

    STATUS_GET_REWARD: ClassVar[str] = '获取奖励'

    def __init__(self, ctx: Context, max_to_get: int,
                 on_reward: Optional[Callable[[int, int], None]] = None
                 ):
        """
        模拟宇宙 - 获取沉浸奖励 需要已经打开领取的对话框
        :param ctx:
        :param max_to_get: 最多获取多少次奖励
        :param on_reward: 获取奖励时的回调
        """
        edges = []
        get_reward = StateOperationNode('获取奖励', self._get_reward)
        empty = StateOperationNode('点击空白处关闭', self._click_empty)
        edges.append(StateOperationEdge(get_reward, empty, status=SimUniReward.STATUS_GET_REWARD))

        check = StateOperationNode('检查画面', self._check_state)
        edges.append(StateOperationEdge(empty, check))
        edges.append(StateOperationEdge(check, get_reward, status=ScreenState.SIM_REWARD.value))  # 第二次领取

        esc = StateOperationNode('退出', self._esc)
        edges.append(StateOperationEdge(get_reward, esc, ignore_status=True))  # 到达领取上限 或者 已经没有体力领取了
        edges.append(StateOperationEdge(get_reward, esc, success=False))  # 可能画面判断出错了
        edges.append(StateOperationEdge(check, esc, status=ScreenState.NORMAL_IN_WORLD.value))  # 已经领取完了

        super().__init__(ctx, try_times=5,
                         op_name='%s %s' % (gt('模拟宇宙', 'ui'), gt('沉浸奖励', 'ui')),
                         edges=edges, specified_start_node=get_reward
                         )

        self.max_to_get: int = max_to_get  # 最多获取多少次奖励
        self.get_reward_cnt: int = 0  # 当前获取了多少次奖励
        self.on_reward: Optional[Callable[[int, int], None]] = on_reward  # 获取奖励时的回调

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        self.get_reward_cnt = 0

        return None

    def _get_reward(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        state = screen_state.get_sim_uni_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                      reward=True)

        if state != ScreenState.SIM_REWARD.value:
            return self.round_retry('未在沉浸奖励画面', wait=1)

        if self.get_reward_cnt >= self.max_to_get:
            log.info('领取奖励完毕')
            self.ctx.controller.click(SimUniReward.CLOSE_REWARD_BTN.center)
            return self.round_success(wait=1)

        rect = self._get_reward_pos(screen)
        if rect is not None:
            self.ctx.controller.click(rect.center)
            if self.on_reward is not None:
                self.on_reward(
                    40 if rect == SimUniReward.POWER_NUM_RECT else 0,
                    1 if rect == SimUniReward.QTY_RECT else 0
                )
            return self.round_success(SimUniReward.STATUS_GET_REWARD)
        else:
            self.ctx.controller.click(SimUniReward.CLOSE_REWARD_BTN.center)
            return self.round_success(wait=1)

    def _get_reward_pos(self, screen: MatLike) -> Optional[Rect]:
        """
        获取可以点击的获取奖励按钮
        :param screen:
        :return:
        """
        for rect in [SimUniReward.QTY_RECT, SimUniReward.POWER_NUM_RECT]:  # 优先使用沉浸器
            part = cv2_utils.crop_image_only(screen, rect)
            black_part = cv2_utils.color_in_range(part, [0, 0, 0], [80, 80, 80])
            # cv2_utils.show_image(black_part, win_name='black_part', wait=0)
            ocr_result = self.ctx.ocr.run_ocr_single_line(black_part)
            digit = str_utils.get_positive_digits(ocr_result, err=0)
            if digit > 0:
                return rect

        return None

    def _click_empty(self) -> OperationOneRoundResult:
        """
        领取奖励后点击空白继续
        :return:
        """
        screen = self.screenshot()
        state = screen_state.get_sim_uni_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                      empty_to_close=True)

        if state != ScreenState.EMPTY_TO_CLOSE.value:
            return self.round_retry('未在点击空白处关闭画面', wait=1)

        click = self.ctx.controller.click(screen_state.TargetRect.EMPTY_TO_CLOSE.value.center)
        if click:
            return self.round_success(wait=1)
        else:
            return self.round_retry('点击空白处关闭失败', wait=1)

    def _check_state(self) -> OperationOneRoundResult:
        """
        每轮后检查状态
        :return:
        """
        screen = self.screenshot()
        state = self._get_screen_state(screen)
        if state is None:
            return self.round_retry('判断画面状态失败', wait=1)
        else:
            return self.round_success(state)

    def _get_screen_state(self, screen: MatLike):
        return screen_state.get_sim_uni_screen_state(screen, self.ctx.im, self.ctx.ocr,
                                                     in_world=True,
                                                     reward=True)

    def _esc(self) -> OperationOneRoundResult:
        """
        领取够了就退出
        :return:
        """
        return self.round_success()
