import time
from typing import Optional

from one_dragon.base.geometry.point import Point
from one_dragon.base.screen import screen_utils
from one_dragon.utils import str_utils
from one_dragon.utils.i18_utils import gt
from one_dragon.utils.log_utils import log
from one_dragon.yolo.detect_utils import DetectObjectResult
from sr_od.app.div_uni.div_uni_data_service import DivUniDataService
from sr_od.app.div_uni.entity.div_uni_equation import DivUniEquation
from sr_od.app.div_uni.entity.div_uni_reward import DivUniReward
from sr_od.app.div_uni.entity.div_uni_reward_pos import DivUniRewardPos
from sr_od.config.character_const import is_valid_path_name
from sr_od.context.sr_context import SrContext
from cv2.typing import MatLike

class DivUniContext:

    def __init__(self, ctx: SrContext):
        self.ctx: SrContext = ctx
        self.data_service: DivUniDataService = DivUniDataService()

        self.level_priority_list: list[str] = [4, 3, 2, 1, 0]

    def init_for_div_uni(self) -> None:
        self.data_service.load_all()

    def check_screen_name(self, screen: MatLike) -> str:
        """
        判断当前画面属于哪个差分宇宙里的画面
        """
        screen_name_list = [
            '差分宇宙-大世界',

            '模拟宇宙-获得物品',
            '模拟宇宙-获得奇物',
            '模拟宇宙-获得祝福',
            '差分宇宙-获得方程',

            '差分宇宙-选择奇物',
            '差分宇宙-选择祝福',
        ]
        current_screen_name = screen_utils.get_match_screen_name(
            self.ctx, screen,
            screen_name_list=screen_name_list)
        self.ctx.screen_loader.update_current_screen_name(current_screen_name)
        return current_screen_name

    def is_div_uni_normal_world(self, screen: MatLike) -> bool:
        """
        是否在差分宇宙的大世界画面
        """
        screen_name_list = [
            '差分宇宙-大世界',
        ]
        current_screen_name = screen_utils.get_match_screen_name(
            self.ctx, screen,
            screen_name_list=screen_name_list)
        self.ctx.screen_loader.update_current_screen_name(current_screen_name)
        return current_screen_name is not None

    def get_curio_pos(self, screen: MatLike) -> list[DivUniRewardPos]:
        """
        识别画面中的奇物位置
        """
        target_word_list: list[str] = [
            gt(curio.name)
            for curio in self.data_service.curio_list
        ]

        pos_list: list[DivUniRewardPos] = []
        ocr_result_map = self.ctx.ocr.run_ocr(screen)
        for ocr_result, mrl in ocr_result_map.items():
            if mrl.max is None:
                continue

            curio_idx = str_utils.find_best_match_by_difflib(ocr_result, target_word_list)
            if curio_idx is None or curio_idx < 0:
                continue

            curio = self.data_service.curio_list[curio_idx]
            for mr in mrl:
                pos_list.append(DivUniRewardPos(curio, mr.rect))

        display_text: str = ', '.join([i.reward.name for i in pos_list])
        log.info(f'当前识别奇物: {display_text}')
        return pos_list

    def get_equation_pos(self, screen: MatLike) -> list[DivUniRewardPos]:
        """
        识别画面中的方程位置
        """
        target_word_list: list[str] = [
            gt(i.name)
            for i in self.data_service.equation_list
        ]

        pos_list: list[DivUniRewardPos] = []
        ocr_result_map = self.ctx.ocr.run_ocr(screen)
        for ocr_result, mrl in ocr_result_map.items():
            if mrl.max is None:
                continue

            target_idx = str_utils.find_best_match_by_difflib(ocr_result, target_word_list)
            if target_idx is None or target_idx < 0:
                continue

            equation = self.data_service.equation_list[target_idx]
            for mr in mrl:
                pos_list.append(DivUniRewardPos(equation, mr.rect))

        display_text: str = ', '.join([i.reward.name for i in pos_list])
        log.info(f'当前识别方程: {display_text}')
        return pos_list

    def get_bless_pos(self, screen: MatLike) -> list[DivUniRewardPos]:
        """
        识别画面中的祝福位置
        """
        target_word_list: list[str] = [
            gt(bless.name)
            for bless in self.data_service.bless_list
        ]

        pos_list: list[DivUniRewardPos] = []
        ocr_result_map = self.ctx.ocr.run_ocr(screen)
        for ocr_result, mrl in ocr_result_map.items():
            if mrl.max is None:
                continue

            target_idx = str_utils.find_best_match_by_difflib(ocr_result, target_word_list)
            if target_idx is None or target_idx < 0:
                continue

            bless = self.data_service.bless_list[target_idx]
            for mr in mrl:
                pos_list.append(DivUniRewardPos(bless, mr.rect))

        display_text: str = ', '.join([i.reward.name for i in pos_list])
        log.info(f'当前识别祝福: {display_text}')
        return pos_list

    def get_reward_by_priority(
            self,
            reward_list: list[DivUniRewardPos], choose_num: int,
            consider_priority_1: bool = True, consider_priority_2: bool = True,
            consider_not_in_priority: bool = True,
            ignore_idx_list: Optional[list[int]] = None,
            consider_priority_new: bool = False,
    ) -> list[DivUniRewardPos]:
        """
        根据优先级 返回需要选择的奖励
        :param reward_list: 识别到的藏品结果
        :param choose_num: 需要选择的数量
        :param consider_priority_1: 是否考虑优先级1的内容
        :param consider_priority_2: 是否考虑优先级2的内容
        :param consider_not_in_priority: 是否考虑优先级以外的选项
        :param ignore_idx_list: 需要忽略的下标
        :param consider_priority_new: 是否优先选择NEW类型 最高优先级
        :return: 按优先级选择的结果
        """
        log.info(f'当前考虑优先级 数量={choose_num} NEW!={consider_priority_new} 第一优先级={consider_priority_1} 第二优先级={consider_priority_2} 其他={consider_not_in_priority}')
        priority_list_to_consider = []
        # if consider_priority_1:
        #     priority_list_to_consider.append(self.challenge_config.artifact_priority)
        # if consider_priority_2:
        #     priority_list_to_consider.append(self.challenge_config.artifact_priority_2)
        if len(priority_list_to_consider) == 0:  # 没有设置优先时 默认考虑全部
            consider_not_in_priority = True

        priority_idx_list: list[int] = []  # 优先级排序的下标

        # 优先选择NEW类型 最高优先级
        if consider_priority_new:
            for target_level in self.level_priority_list:
                for idx in range(len(reward_list)):
                    if ignore_idx_list is not None and idx in ignore_idx_list:  # 需要忽略的下标
                        continue

                    if idx in priority_idx_list:  # 已经加入过了
                        continue

                    pos = reward_list[idx]
                    if pos.reward.level != target_level:
                        continue

                    if not pos.is_new:
                        continue

                    priority_idx_list.append(idx)

        # 按优先级顺序 将匹配的藏品下标加入
        # 同时 优先考虑等级高的
        for target_level in self.level_priority_list:
            for priority_list in priority_list_to_consider:
                for priority in priority_list:
                    for idx in range(len(reward_list)):
                        if ignore_idx_list is not None and idx in ignore_idx_list:  # 需要忽略的下标
                            continue

                        if idx in priority_idx_list:  # 已经加入过了
                            continue

                        reward: DivUniReward = reward_list[idx].reward
                        if reward.level != target_level:  # 不符合目标等级
                            continue

                        if self.is_reward_in_priority(reward, priority):
                            priority_idx_list.append(idx)

        # 将剩余的 按等级加入
        if consider_not_in_priority:
            for target_level in self.level_priority_list:
                for idx in range(len(reward_list)):
                    if ignore_idx_list is not None and idx in ignore_idx_list:  # 需要忽略的下标
                        continue

                    if idx in priority_idx_list:  # 已经加入过了
                        continue

                    reward: DivUniReward = reward_list[idx].reward

                    if reward.level == target_level:
                        priority_idx_list.append(idx)

        result_list: list[DivUniRewardPos] = []
        for i in range(choose_num):
            if i >= len(priority_idx_list):
                continue
            result_list.append(reward_list[priority_idx_list[i]])

        display_text = ', '.join([i.reward.display_name for i in result_list]) if len(result_list) > 0 else '无'
        log.info(f'当前符合优先级列表 {display_text}')

        return result_list

    def is_reward_in_priority(self, reward: DivUniReward, priority_word: str) -> bool:
        """
        判断一个奖励是否符合优先级
        :param reward: 奖励
        :param priority_word: 优先级配置文本
        """
        split_idx = priority_word.find(' ')
        if split_idx != -1:
            # 有空格的情况 说明指定了具体的奖励
            target_category = priority_word[:split_idx]
            target_name = priority_word[split_idx + 1:]
        else:
            # 没有空格的情况 说明只需要匹配分类
            target_category = priority_word
            target_name = ''

        if reward.category != target_category:  # 不符合分类
            if isinstance(reward, DivUniEquation):
                # 如果是方程 则可以额外看是否满足对应命途
                if target_name != '':  # 有具体名称的 不是命途选项
                    return False

                if not is_valid_path_name(target_name):  # 不是命途名称
                    return False

                if target_name not in reward.path_list:  # 不在所需命途中
                    return False
            else:
                return False

        # 符合分类 且只需要匹配分类
        if target_name == '':
            return True

        # 最后看名字是否完全一致
        return target_name == reward.name

    def view_down(self):
        """
        视角往下移动 方便识别目标
        :return:
        """
        if self.ctx.detect_info.view_down:
            return
        self.ctx.controller.turn_down(25)
        self.ctx.detect_info.view_down = True
        time.sleep(0.2)

    def turn_to_target(self, target: DetectObjectResult) -> bool:
        """
        将画面转向识别目标
        :return 是否有转向
        """
        target_center = Point(target.center[0], target.center[1])
        if target_center.x < 760:
            self.ctx.controller.turn_by_distance(-100)
            return True
        elif target_center.x < 860:
            self.ctx.controller.turn_by_distance(-50)
            return True
        elif target_center.x < 910:
            self.ctx.controller.turn_by_distance(-25)
            return True
        elif target_center.x > 1160:
            self.ctx.controller.turn_by_distance(+100)
            return True
        elif target_center.x > 1060:
            self.ctx.controller.turn_by_distance(+50)
            return True
        elif target_center.x > 1010:
            self.ctx.controller.turn_by_distance(+25)
            return True
        else:
            return False