from basic import Point
from basic.img.os import get_debug_image
from basic.log_utils import log
from sr.const.map_const import get_region_by_prl_id
from sr.context.context import get_context
from test.sr.cal_pos.cal_pos_test_case import read_test_cases, TestCase, save_test_cases
from test.sr.cal_pos.test_cal_pos_for_sim_uni.test_cal_pos_for_sim_uni import TestCalPosForSimUni


class DebugCalPosForSimUni(TestCalPosForSimUni):

    def __init__(self, *args, **kwargs):
        TestCalPosForSimUni.__init__(self, *args, **kwargs)

    def test_init_case(self):
        ctx = get_context()
        file_name = 'P02_YLL6_R05_CXHL_274_1318_30_True'
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
