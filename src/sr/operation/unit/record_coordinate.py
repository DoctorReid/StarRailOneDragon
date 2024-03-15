import cv2
import os
import yaml

from cv2.typing import MatLike

from basic import Point, os_utils
from basic.img import MatchResult
from basic.log_utils import log
from sr import cal_pos
from sr.const import map_const
from sr.const.map_const import Region
from sr.context import Context
from sr.image.sceenshot import mini_map, large_map, LargeMapInfo
from sr.operation import Operation, OperationOneRoundResult


class RecordCoordinate(Operation):

    def __init__(self, ctx: Context, region: Region, last_point: Point):
        """
        站在原地不动 进行截图和坐标记录。需要在确保不被攻击的情况下使用
        """
        super().__init__(ctx,
                         op_name='坐标记录')

        self.region: Region = region  # 区域
        self.lm_info: LargeMapInfo = self.ctx.ih.get_large_map(self.region)
        self.last_point: Point = last_point  # 上一个点的坐标
        self.record_times: int = 0  # 当前已记录次数

    def _execute_one_round(self) -> OperationOneRoundResult:
        self.record_times += 1
        if self.record_times >= 6:
            return Operation.round_success()

        screen = self.screenshot()

        mm = mini_map.cut_mini_map(screen, self.ctx.game_config.mini_map_pos)

        move_time = 1

        move_distance = self.ctx.controller.cal_move_distance_by_time(move_time)
        possible_pos = (self.last_point.x, self.last_point.y, move_distance)
        lm_rect = large_map.get_large_map_rect_by_pos(self.lm_info.gray.shape, mm.shape[:2], possible_pos)

        sp_map = map_const.get_sp_type_in_rect(self.region, lm_rect)
        mm_info = mini_map.analyse_mini_map(mm, self.ctx.im, sp_types=set(sp_map.keys()))

        try:
            next_pos = cal_pos.cal_character_pos(self.ctx.im, self.lm_info, mm_info,
                                                 possible_pos=possible_pos,
                                                 lm_rect=lm_rect, retry_without_rect=False,
                                                 running=False)
        except Exception:
            next_pos = None
            log.error('识别坐标失败', exc_info=True)

        if next_pos is None:
            return Operation.round_wait(wait=0.5)

        self.save(self.region, mm, next_pos)

    @staticmethod
    def save(region: Region, mm: MatLike, pos: MatchResult):
        """
        保存小地图和对应的坐标结果
        :param region:
        :param mm:
        :param pos:
        :return:
        """
        mm_file_name = 'mm.png'
        pos_file_name = 'pos.yml'

        base_dir = RecordCoordinate.get_base_dir(region)
        idx: int = 1
        while True:
            case_dir = os.path.join(base_dir, '%03d' % idx)
            if not os.path.exists(case_dir):
                os.mkdir(case_dir)
                break

            file_list = [mm_file_name, pos_file_name]
            for file in file_list:
                file_path = os.path.join(case_dir, file)
                if not os.path.exists(file_path):
                    break

            idx += 1

        mm_file_path = os.path.join(case_dir, mm_file_name)
        cv2.imwrite(mm_file_path, mm)

        pos_file_path = os.path.join(case_dir, pos_file_name)
        with open(pos_file_path, 'w', encoding='utf-8') as file:
            data = {
                'region': region.prl_id,
                'x': pos.x,
                'y': pos.y,
                'w': pos.w,
                'h': pos.h,
                'c': pos.confidence
            }
            yaml.dump(data, file)

    @staticmethod
    def get_base_dir(region: Region):
        return os_utils.get_path_under_work_dir('.debug', 'cal_pos', region.prl_id)
