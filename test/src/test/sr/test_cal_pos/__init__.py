from typing import List

import cv2
import os
import yaml

import test
from basic import Point, cal_utils
from basic.img import MatchResult, cv2_utils
from basic.img.os import get_debug_image, save_debug_image
from basic.log_utils import log
from sr import cal_pos, performance_recorder
from sr.const import map_const
from sr.const.map_const import Region, get_region_by_prl_id
from sr.context import get_context
from sr.image.sceenshot import mini_map, large_map


class TestCase:

    def __init__(self, region: Region, pos: Point, num: int, running: bool, possible_pos: List[int]):
        self.region: Region = region
        self.pos: Point = pos
        self.num: int = num
        self.running: bool = running
        self.possible_pos: List[int] = possible_pos

    @property
    def unique_id(self) -> str:
        return '%s_%02d' % (self.region.prl_id, self.num)

    @property
    def image_name(self) -> str:
        return '%s_%02d.png' % (self.region.prl_id, self.num)


class TestCalPos(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

        self.cases: List[TestCase] = []

    @property
    def _test_cases_path(self) -> str:
        return os.path.join(self.sub_package_path, 'test_cases.yml')

    def _read_test_cases(self):
        data = []
        path = self._test_cases_path
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)

        self.cases = [self.dict_2_case(row) for row in data['cases']]

    @staticmethod
    def dict_2_case(data: dict) -> TestCase:
        region = get_region_by_prl_id(data['region'])
        pos = Point(data['pos'][0], data['pos'][1])
        num = data['num']
        running = data['running']
        possible_pos = data['possible_pos']
        return TestCase(region, pos, num, running, possible_pos)

    def _save_test_cases(self):
        data = {
            'cases': [self.case_2_dict(c) for c in self.cases]
        }
        path = self._test_cases_path
        with open(path, 'w', encoding='utf-8') as file:
            yaml.dump(data, file)

    @staticmethod
    def case_2_dict(case: TestCase) -> dict:
        data = {
            'region': case.region.prl_id,
            'pos': [case.pos.x, case.pos.y],
            'num': case.num,
            'running': case.running,
            'possible_pos': [case.possible_pos[0], case.possible_pos[1], case.possible_pos[2]]
        }

        return data

    def test_cal_pos(self):
        fail_cnt = 0
        self._read_test_cases()
        for case in self.cases:
            if case.region.prl_id != 'P03_XZLF_R02_LYD_F1 ' and case.num != 2:
                continue
            result = self.run_one_test_case(case, show=True)
            if not result:
                fail_cnt += 1
                log.info('%s 计算坐标失败', case.unique_id)

        performance_recorder.log_all_performance()
        self.assertTrue(fail_cnt == 0)

    def test_init_case(self):
        """
        从debug中初始化
        :return:
        """
        ctx = get_context()
        file_name: str = 'P03_XZLF_R02_LYD_F1_419_1318_30_True'
        mm = get_debug_image(file_name)

        str_list = file_name.split('_')
        is_running = (bool)(str_list.pop())
        pp_r = (int)(str_list.pop())
        pp_y = (int)(str_list.pop())
        pp_x = (int)(str_list.pop())
        region_prl_id = '_'.join(str_list)

        region = get_region_by_prl_id(region_prl_id)

        self._read_test_cases()
        idx: int = 1
        while True:
            existed: bool = False
            for c in self.cases:
                if c.region.prl_id != region_prl_id:
                    continue
                if c.num == idx:
                    existed = True
                    break
            if existed:
                idx += 1
            else:
                break

        case = TestCase(region, Point(pp_x, pp_y), idx, is_running, [pp_x, pp_y, pp_r])
        self.cases.append(case)
        self.cases = sorted(self.cases, key=lambda x: x.unique_id)
        self._save_test_cases()
        self.save_test_image(mm, case.image_name)
        log.info('新增样例 %s %02d', region_prl_id, idx)

    def run_one_test_case(self, case: TestCase, show: bool = False) -> bool:
        """
        执行一个测试样例
        :param case: 测试样例
        :param show: 显示
        :return: 是否与预期一致
        """
        ctx = get_context()
        ctx.init_image_matcher()

        mm = self.get_test_image_new(case.image_name)

        lm_info = ctx.ih.get_large_map(case.region)
        possible_pos = tuple(case.possible_pos)
        lm_rect = large_map.get_large_map_rect_by_pos(lm_info.gray.shape, mm.shape[:2], possible_pos)
        sp_map = map_const.get_sp_type_in_rect(lm_info.region, lm_rect)
        mm_info = mini_map.analyse_mini_map(mm, ctx.im, sp_types=set(sp_map.keys()))

        pos = cal_pos.cal_character_pos(ctx.im,
                                        lm_info=lm_info,
                                        mm_info=mm_info,
                                        possible_pos=possible_pos,
                                        running=case.running,
                                        lm_rect=lm_rect,
                                        retry_without_rect=False,
                                        show=show
                                        )
        if show:
            cv2.waitKey(0)

        log.info('%s 当前计算坐标为 %s', case.unique_id, pos)

        if pos is None:
            return False
        else:
            dis = cal_utils.distance_between(pos, case.pos)
            return dis < 5
