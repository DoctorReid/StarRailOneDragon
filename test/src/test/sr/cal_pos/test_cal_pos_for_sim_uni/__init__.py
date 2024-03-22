import os

import cv2

import test
from basic import Point, cal_utils
from basic.img import MatchResult, cv2_utils
from basic.img.os import get_debug_image, save_debug_image
from basic.log_utils import log
from sr import cal_pos, performance_recorder
from sr.const import map_const
from sr.const.map_const import get_region_by_prl_id
from sr.context import get_context
from sr.image.image_holder import ImageHolder
from sr.image.sceenshot import mini_map, large_map
from test.sr.cal_pos.cal_pos_test_case import read_test_cases, TestCase, save_test_cases


class TestCalPosForSimUni(test.SrTestBase):

    def __init__(self, *args, **kwargs):
        test.SrTestBase.__init__(self, *args, **kwargs)

        ih = ImageHolder()
        # 预热 方便后续统计耗时
        ih.preheat_for_world_patrol()
        mini_map.preheat()

    @property
    def cases_path(self) -> str:
        return os.path.join(self.sub_package_path, 'test_cases.yml')

    def test_cal_pos_for_sim_uni(self):
        fail_cnt = 0
        case_list = read_test_cases(self.cases_path)
        for case in case_list:
            # if case.unique_id !='P02_YLL6_R11_MDZ_F1_02':
            #     continue
            result = self.run_one_test_case(case, show=False)
            if not result:
                fail_cnt += 1
                log.info('%s 计算坐标失败', case.unique_id)

        performance_recorder.log_all_performance()
        self.assertEqual(0, fail_cnt)

    def test_init_case(self):
        ctx = get_context()
        file_name = 'P02_YLL6_R11_MDZ_F1_487_530_30_True'
        mm = get_debug_image(file_name)

        str_list = file_name.split('_')
        is_running = (bool)(str_list.pop())
        pp_r = (int)(str_list.pop())
        pp_y = (int)(str_list.pop())
        pp_x = (int)(str_list.pop())
        region_prl_id = '_'.join(str_list)

        region = get_region_by_prl_id(region_prl_id)

        case_list = read_test_cases(self.cases_path)
        idx: int = 1
        while True:
            existed: bool = False
            for c in case_list:
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
        case_list.append(case)
        case_list = sorted(case_list, key=lambda x: x.unique_id)
        save_test_cases(case_list, self.cases_path)

        self.save_test_image(mm, case.image_name)
        log.info('新增样例 %s', case.unique_id)
        self.run_one_test_case(case, show=True)

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
        lm_rect = large_map.get_large_map_rect_by_pos(lm_info.gray.shape, mm.shape[:2], case.possible_pos)
        mm_info = mini_map.analyse_mini_map(mm, ctx.im)

        pos = cal_pos.sim_uni_cal_pos(ctx.im,
                                      lm_info=lm_info,
                                      mm_info=mm_info,
                                      possible_pos=case.possible_pos,
                                      running=case.running,
                                      lm_rect=lm_rect,
                                      show=show
                                      )
        if show:
            cv2.waitKey(0)

        if pos is None:
            log.error('%s 当前计算坐标为空', case.unique_id)
            return False
        else:
            dis = cal_utils.distance_between(pos, case.pos)
            log.info('%s 当前计算坐标为 %s 与目标点距离 %.2f', case.unique_id, pos, dis)
            return dis < 5

    def test_for_debug(self):
        ctx = get_context()
        ctx.init_image_matcher()

        screen = get_debug_image('_1707144839172')
        mm = mini_map.cut_mini_map(screen)
        save_debug_image(mm)
        mm_info = mini_map.analyse_mini_map(mm, ctx.im)

        for _, region_list in map_const.PLANET_2_REGION.items():
            for region in region_list:
                if region != map_const.P02_R10:
                    continue
                lm_info = ctx.ih.get_large_map(region)
                pos: MatchResult = cal_pos.sim_uni_cal_pos_by_gray(ctx.im, lm_info, mm_info,
                                                                   scale_list=[1], match_threshold=0.2,
                                                                   show=True)
                log.info('匹配 %s 结果 %s', region.display_name, pos)
                if pos is not None:
                    cv2_utils.show_overlap(lm_info.origin, mm_info.origin, pos.left_top.x, pos.left_top.y, win_name='overlap')
                cv2.waitKey(0)

    def test_cal_for_debug(self):
        ctx = get_context()
        ctx.init_image_matcher()

        screen = get_debug_image('_1706412936314')
        mm = mini_map.cut_mini_map(screen)
        mm_info = mini_map.analyse_mini_map(mm, ctx.im)

        possible_pos = (957, 392, 25)
        region = map_const.P01_R04_F1
        lm_info = ctx.ih.get_large_map(region)
        lm_rect = large_map.get_large_map_rect_by_pos(lm_info.gray.shape, mm.shape[:2], possible_pos)
        pos: Point = cal_pos.sim_uni_cal_pos(ctx.im, lm_info, mm_info,
                                             lm_rect=lm_rect, running=True,
                                             show=True)
        log.info('匹配 %s 结果 %s', region.display_name, pos)
        cv2.waitKey(0)
