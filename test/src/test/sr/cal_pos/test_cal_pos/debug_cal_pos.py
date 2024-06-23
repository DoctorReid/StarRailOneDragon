from basic import Point
from basic.img.os import get_debug_image
from basic.log_utils import log
from sr import performance_recorder
from sr.const.map_const import get_region_by_prl_id
from sr.context.context import get_context
from test.sr.cal_pos.cal_pos_test_case import read_test_cases, TestCase, save_test_cases
from test.sr.cal_pos.test_cal_pos.test_cal_pos import TestCalPos


class DebugCalPos(TestCalPos):

    def __init__(self, *args, **kwargs):
        TestCalPos.__init__(self, *args, **kwargs)

    def test_specified_one(self):
        fail_cnt = 0
        self.cases = read_test_cases(self.cases_path)
        for case in self.cases:
            if case.unique_id != 'P04_PNKN_R06_CSSH_02':
                continue
            result = self.run_one_test_case(case, show=True)
            if not result:
                fail_cnt += 1
                log.info('%s 计算坐标失败', case.unique_id)

        performance_recorder.log_all_performance()
        self.assertEqual(0, fail_cnt)

    def test_init_case(self):
        """
        从debug中初始化
        :return:
        """
        ctx = get_context()
        file_name: str = '_1711787600419'
        mm = get_debug_image(file_name)

        str_list = file_name.split('_')
        is_running = (bool)(str_list.pop())
        pp_r = (int)(str_list.pop())
        pp_y = (int)(str_list.pop())
        pp_x = (int)(str_list.pop())
        region_prl_id = '_'.join(str_list)

        region = get_region_by_prl_id(region_prl_id)

        self.cases = read_test_cases(self.cases_path)
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
        save_test_cases(self.cases, self.cases_path)
        self.save_test_image(mm, case.image_name)
        log.info('新增样例 %s', case.unique_id)
