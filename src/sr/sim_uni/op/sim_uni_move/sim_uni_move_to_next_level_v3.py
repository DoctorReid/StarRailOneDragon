import time

import numpy as np
from cv2.typing import MatLike
from typing import Optional, List

from basic import str_utils, cal_utils
from basic.i18_utils import gt
from basic.img import MatchResult
from basic.log_utils import log
from sr.const import OPPOSITE_DIRECTION
from sr.context.context import Context
from sr.control import GameController
from sr.image.sceenshot import screen_state, mini_map
from sr.operation import OperationOneRoundResult, StateOperation, StateOperationNode, Operation
from sr.operation.unit.interact import get_move_interact_words
from sr.sim_uni.op.move_in_sim_uni import MoveToNextLevel
from sr.sim_uni.op.sim_uni_move.sim_uni_move_by_detect import delta_angle_to_detected_object, turn_by_angle_slowly
from sr.sim_uni.sim_uni_const import SimUniLevelType, SimUniLevelTypeEnum


class MoveToNextLevelV3(StateOperation):

    def __init__(self, ctx: Context, level_type: SimUniLevelType, with_entry: bool = True,
                 turn_direction: int = 0):
        StateOperation.__init__(self, ctx, op_name=gt('向下层移动v3', 'ui'))
        self.level_type: SimUniLevelType = level_type
        self.start_with_entry: bool = with_entry  # 开始前是否识别到入口
        self.turn_direction: int = turn_direction  # 转动找下层入口的方向 1=右边 -1=左边

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        check_before_detect = StateOperationNode('画面识别前初始化', self.check_before_detect)

        turn = StateOperationNode('画面识别转向入口', self.turn_by_detect)
        self.add_edge(check_before_detect, turn)
        # YOLO识别不到的话 可能是距离太远 往最开始的方向靠近试试
        move_when_detect_fail = StateOperationNode('画面识别失败后移动', self.move_when_detect_fail)
        self.add_edge(turn, move_when_detect_fail, success=False, status=MoveToNextLevel.STATUS_ENTRY_NOT_FOUND)
        self.add_edge(move_when_detect_fail, turn)

        record = StateOperationNode('记录入口角度', self.record_detect_angle)
        self.add_edge(turn, record)

        check_by_feature_match = StateOperationNode('图标识别下层入口', self.check_by_feature_match)
        self.add_edge(record, check_by_feature_match)

        # 图标识别不到的话 可能是距离太远 往YOLO识别的方向靠近
        move_by_detect_angle = StateOperationNode('往画面识别的入口移动', self.move_by_detect_angle)
        self.add_edge(check_by_feature_match, move_by_detect_angle, status=MoveToNextLevel.STATUS_ENTRY_NOT_FOUND)
        # 靠近后重新开始
        self.add_edge(move_by_detect_angle, turn)

        # 图标识别成功 准备开始移动
        check_before_move = StateOperationNode('移动前初始化', self.check_before_move)
        self.add_edge(check_by_feature_match, check_before_move)

        # 开始移动
        move = StateOperationNode('往图标识别的入口移动', self.move_and_interact)
        self.add_edge(check_before_move, move)

        # 交互后可能出现确认
        confirm = StateOperationNode('确认', self.confirm)
        self.add_edge(move, confirm)

    def handle_init(self) -> Optional[OperationOneRoundResult]:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        可以返回初始化后判断的结果
        - 成功时跳过本指令
        - 失败时立刻返回失败
        - 不返回时正常运行本指令
        """
        self.detect_entry_angle: float = -1  # YOLO识别的入口所在的方向
        self.feature_no_entry_times: int = 0  # 特征识别图标没有找到入口的次数
        self.current_interact_word: str = ''  # 当前存在的交互词
        self.get_rid_direction: str = 'a'  # 脱困方向
        self.move_times: int = 0  # 累计的移动次数
        self.start_move_time: float = 0  # 开始移动的时间
        self.interacted: bool = False  # 是否已经尝试过交互
        self.detect_fail_times: int = 0  # YOLO识别失败的次数

        # 是否出现过交互词
        # 休整、精英楼层有其它可以交互的内容 因此需要出现过正确交互词才能交互
        # 其它楼层无脑交互即可
        self.existed_interact_word: bool = self.level_type not in [
            SimUniLevelTypeEnum.RESPITE.value,
            SimUniLevelTypeEnum.ELITE.value
        ]

        return None

    def check_before_detect(self) -> OperationOneRoundResult:
        """
        YOLO识别前的初始化
        :return:
        """
        if self.start_with_entry:
            self.record_detect_angle()

        return self.round_success()

    def turn_by_detect(self) -> OperationOneRoundResult:
        """
        靠YOLO识别 先大概转到下层入口方向
        :return:
        """
        screen = self.screenshot()

        frame_result = self.ctx.yolo_detector.sim_uni_yolo.detect(screen)

        entry_angles: List[float] = []
        for result in frame_result.results:
            delta_angle = delta_angle_to_detected_object(result)
            if result.detect_class.class_cate == '模拟宇宙下层入口':
                entry_angles.append(delta_angle)

        if len(entry_angles) > 0:
            avg_delta_angle = np.mean(entry_angles)
            log.debug('转向 %.2f', avg_delta_angle)
            turn_by_angle_slowly(self.ctx, avg_delta_angle)
            if avg_delta_angle < 30:  # 慢慢转过去
                return self.round_success()
            else:
                return self.round_wait(wait=0.1)
        else:
            self.ctx.controller.turn_by_angle(35 * self.turn_direction)
            return self.round_retry(status=MoveToNextLevel.STATUS_ENTRY_NOT_FOUND, wait=0.5)

    def record_detect_angle(self) -> OperationOneRoundResult:
        """
        记录YOLO识别入口的方向
        :return:
        """
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        self.detect_entry_angle = mini_map.analyse_angle(mm)

        # 其它的初始化
        self.feature_no_entry_times = 0

        return self.round_success()

    def move_when_detect_fail(self) -> OperationOneRoundResult:
        """
        朝最初的方向前进
        :return:
        """
        self.detect_fail_times += 1
        if self.detect_fail_times >= 3:
            return self.round_fail(status=MoveToNextLevel.STATUS_ENTRY_NOT_FOUND)
        else:
            return self.move_by_detect_angle()

    def check_by_feature_match(self) -> OperationOneRoundResult:
        """
        使用特征匹配识别当前有没有下层入口的图标
        :return:
        """
        screen = self.screenshot()
        type_list = MoveToNextLevel.get_next_level_type(screen, self.ctx.ih)

        if len(type_list) == 0:
            self.feature_no_entry_times += 1
            if self.feature_no_entry_times <= 6:
                # 来回转动视角
                angle = (25 + 10 * self.feature_no_entry_times) * (1 if self.feature_no_entry_times % 2 == 0 else -1)
                self.ctx.controller.turn_by_angle(angle)
                return self.round_wait(wait=1)
            else:
                return self.round_success(status=MoveToNextLevel.STATUS_ENTRY_NOT_FOUND)
        else:
            self.turn_to_target(type_list[0])
            return self.round_success()

    def move_by_detect_angle(self) -> OperationOneRoundResult:
        """
        特征匹配识别不到下层入口的图标 说明距离有点远
        先转到原来YOLO可以识别的视角 往前移动一段距离后重新尝试
        :return:
        """
        screen = self.screenshot()
        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)
        current_angle = mini_map.analyse_angle(mm)
        self.ctx.controller.turn_from_angle(current_angle, self.detect_entry_angle)

        time.sleep(1)
        self.ctx.controller.move('w', 1)

        return self.round_success()

    def check_before_move(self) -> OperationOneRoundResult:
        """
        移动前的初始化
        :return:
        """
        screen = self.screenshot()
        self.check_interact_word(screen)

        return self.round_success()

    def check_interact_word(self, screen: MatLike) -> None:
        """
        识别当前出现的交互词
        :param screen: 游戏画面
        :return:
        """
        words = get_move_interact_words(self.ctx, screen, single_line=True)
        self.current_interact_word = words[0].data if len(words) > 0 and len(words[0].data) > 0 else ''
        if len(self.current_interact_word) > 0:
            self.existed_interact_word = True

    def move_and_interact(self) -> OperationOneRoundResult:
        """
        移动并交互
        :return:
        """
        now = time.time()

        # 出现过交互词 且消失了 就可以无脑交互了
        need_ocr: bool = True # 现在OCR速度快 可以保持使用

        screen = self.screenshot()

        in_world = screen_state.is_normal_in_world(screen, self.ctx.im)

        if not in_world:
            # 如果已经不在大世界画了 就认为成功了
            return self.round_success()

        if self.ctx.controller.is_moving:
            if now - self.start_move_time > MoveToNextLevel.MOVE_TIME:
                self.ctx.controller.stop_moving_forward()
                self.move_times += 1

                if self.move_times >= 4:  # 正常情况不会连续移动这么多次都没有到下层入口 尝试脱困
                    self.ctx.controller.move(self.get_rid_direction, 1)
                    self.get_rid_direction = OPPOSITE_DIRECTION[self.get_rid_direction]
            elif need_ocr:
                interact = self.try_interact(screen)
                if interact is not None:
                    return interact
            return self.round_wait()
        else:
            type_list = MoveToNextLevel.get_next_level_type(screen, self.ctx.ih)
            if len(type_list) == 0:  # 当前没有入口 随便旋转看看
                # 因为前面已经转向了入口 所以就算被遮挡 只要稍微转一点应该就能看到了
                angle = (25 + 10 * self.op_round) * (1 if self.op_round % 2 == 0 else -1)  # 来回转动视角
                self.ctx.controller.turn_by_angle(angle)
                self.move_times = 0  # 没有识别到就是没有移动
                return self.round_retry(MoveToNextLevel.STATUS_ENTRY_NOT_FOUND, wait=1)

            target = MoveToNextLevel.get_target_entry(type_list, self.ctx.sim_uni_challenge_config)

            self.move_towards_target(target)
            return self.round_wait(wait=0.1)

    def try_interact(self, screen: MatLike) -> Optional[OperationOneRoundResult]:
        """
        尝试交互
        :param screen:
        :return:
        """
        if self.can_interact(screen):
            self.ctx.controller.interact(interact_type=GameController.MOVE_INTERACT_TYPE)
            log.debug('尝试交互进入下一层')
            self.interacted = True
            self.ctx.controller.stop_moving_forward()
            return self.round_wait(wait=0.1)
        else:
            return None

    def can_interact(self, screen: MatLike) -> bool:
        """
        当前是否可以交互
        :param screen: 屏幕截图
        :return:
        """
        self.check_interact_word(screen)
        return self.is_target_interact()

    def is_target_interact(self) -> bool:
        return (
                len(self.current_interact_word) > 0
                and str_utils.find_by_lcs(self.current_interact_word, gt('区域', 'ocr'), percent=0.1)
        )

    def move_towards_target(self, target: MatchResult):
        """
        朝目标移动 先让人物转向 让目标就在人物前方
        :param target:
        :return:
        """
        self.turn_to_target(target)
        self.ctx.controller.start_moving_forward()
        self.start_move_time = time.time()

    def turn_to_target(self, target: MatchResult, wait: float = 0.5):
        """
        朝目标转向
        :param target:
        :return:
        """
        angle_to_turn = self.get_angle_to_turn(target)
        self.ctx.controller.turn_by_angle(angle_to_turn)
        time.sleep(wait)

    def get_angle_to_turn(self, target: MatchResult) -> float:
        """
        获取需要转向的角度
        角度的定义与 game_controller.turn_by_angle 一致
        正数往右转 人物角度增加；负数往左转 人物角度减少
        :param target:
        :return:
        """
        # 小地图用的角度 正右方为0 顺时针为正
        mm_angle = cal_utils.get_angle_by_pts(MoveToNextLevel.CHARACTER_CENTER, target.center)

        return mm_angle - 270

    def confirm(self) -> OperationOneRoundResult:
        """
        精英层的确认
        :return:
        """
        self.ctx.controller.stop_moving_forward()
        if self.level_type != SimUniLevelTypeEnum.ELITE.value:
            return self.round_success()
        screen = self.screenshot()
        if not screen_state.is_normal_in_world(screen, self.ctx.im):
            click_confirm = self.ocr_and_click_one_line('确认', MoveToNextLevel.NEXT_CONFIRM_BTN,
                                                        screen=screen)
            if click_confirm == Operation.OCR_CLICK_SUCCESS:
                return self.round_success(wait=1)
            elif click_confirm == Operation.OCR_CLICK_NOT_FOUND:
                return self.round_success()
            else:
                return self.round_retry('点击确认失败', wait=0.25)
        else:
            return self.round_retry('在大世界页面')
