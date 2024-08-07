import difflib
import random
import time
from typing import ClassVar, Optional, List, Tuple

import cv2
import numpy as np
from cv2.typing import MatLike

from basic import Rect, Point, str_utils
from basic.i18_utils import gt
from basic.img import MatchResult, cv2_utils, MatchResultList
from basic.log_utils import log
from sr import const
from sr.app.world_patrol.world_patrol_config import WorldPatrolConfig
from sr.const import STANDARD_RESOLUTION_W, game_config_const
from sr.const.map_const import Planet, PLANET_LIST, best_match_planet_by_name, Region, best_match_region_by_name, \
    PLANET_2_REGION, TransportPoint
from sr.context.context import Context
from sr.image.sceenshot import large_map, LargeMapInfo
from sr.operation import Operation, OperationOneRoundResult, StateOperation, StateOperationEdge, StateOperationNode
from sr.screen_area.screen_large_map import ScreenLargeMap


class ChoosePlanet(Operation):

    def __init__(self, ctx: Context, planet: Planet):
        """
        在大地图页面 选择到对应的星球
        默认已经打开大地图了
        :param planet: 目标星球
        """
        super().__init__(ctx, 10, op_name=gt('选择星球 %s', 'ui') % planet.display_name)
        self.planet: Planet = planet  # 目标星球

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()
        # 根据左上角判断当前星球是否正确
        planet = large_map.get_planet(screen, self.ctx.ocr)
        if planet is not None and planet.np_id == self.planet.np_id:
            return self.round_success()

        if planet is not None:  # 在大地图
            log.info('当前在大地图 准备选择 星轨航图')
            area = ScreenLargeMap.STAR_RAIL_MAP.value
            click = self.find_and_click_area(area, screen)
            if click == Operation.OCR_CLICK_SUCCESS:
                return self.round_wait(wait=1)
            elif click == Operation.OCR_CLICK_NOT_FOUND:  # 点了传送点 星轨航图 没出现
                self.ctx.controller.click(large_map.EMPTY_MAP_POS)
                return self.round_wait(wait=0.5)
            else:
                return self.round_retry('点击星轨航图失败', wait=0.5)
        else:
            log.info('当前在星轨航图')
            planet_list = self.get_planet_pos(screen)

            target_pos: Optional[MatchResult] = None
            with_planet_before_target: bool = False  # 当前屏幕上是否有目标星球之前的星球

            for planet in PLANET_LIST:
                for planet_mr in planet_list:
                    if planet_mr.data == self.planet:
                        target_pos = planet_mr
                        break
                    if planet_mr.data == planet:
                        with_planet_before_target = True

                if target_pos is not None:
                    break

                if planet == self.planet:
                    break

            if target_pos is not None:
                self.choose_planet_by_pos(target_pos)
                return self.round_wait(wait=3)
            else:  # 当前屏幕没有目标星球的情况
                drag_from = Point(STANDARD_RESOLUTION_W // 2, 100)
                drag_to = drag_from + Point(-400 if with_planet_before_target else 400, 0)
                self.ctx.controller.click(drag_from)  # 这里比较神奇 直接拖动第一次会失败
                self.ctx.controller.drag_to(drag_to, drag_from)
                return self.round_retry(wait=1)

    def get_planet_pos(self, screen: MatLike) -> List[MatchResult]:
        """
        获取星轨航图上 星球名字的位置
        :param screen: 屏幕截图
        :return: 星球位置 data中是对应星球 Planet
        """
        # 二值化后更方便识别字体
        gray = cv2.cvtColor(screen, cv2.COLOR_RGB2GRAY)
        _, mask = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

        words = [p.cn for p in PLANET_LIST]
        ocr_map = self.ctx.ocr.match_words(mask, words, lcs_percent=self.gc.planet_lcs_percent)

        result_list: List[MatchResult] = []
        for ocr_word, mrl in ocr_map.items():
            planet = best_match_planet_by_name(ocr_word)
            if planet is not None:
                mr = mrl.max
                mr.data = planet
                result_list.append(mr)

        return result_list

    def choose_planet_by_pos(self, pos: MatchResult):
        """
        根据目标位置 点击选择星球
        :param pos:
        :return:
        """
        drag_from = pos.center
        drag_to = drag_from + Point(0, -100)
        self.ctx.controller.drag_to(drag_to, drag_from)  # 这里比较奇怪 需要聚焦一段时间才能点击到星球
        time.sleep(0.1)
        self.ctx.controller.click(drag_to, press_time=1)


class ChooseRegion(StateOperation):

    def __init__(self, ctx: Context, region: Region,
                 skip_planet_check: bool = False):
        """
        默认已经打开了大地图 且选择了正确的星球。
        选择目标区域
        :param ctx: 上下文
        :param region: 区域
        :param skip_planet_check: 跳过当前星球的检测
        """
        self.skip_planet_check: bool = skip_planet_check  # 跳过当前星球的检测
        self.planet: Planet = region.planet
        self.region: Region = region  # 目标区域
        self.region_config: WorldPatrolConfig = ctx.world_patrol_config
        if region.cn == '晖长石号':
            region.cn = self.region_config.radiant_feldspar_name

        self.region_to_choose_1: Region = region if region.parent is None else region.parent  # 第一步需要选择的区域
        self.sub_region_clicked: bool = False  # 是否已经点击了子区域

        edges: List[StateOperationEdge] = []

        check = StateOperationNode('检测星球', self._check_planet)
        choose_region = StateOperationNode('选择区域', self._choose_region)
        choose_floor = StateOperationNode('选择楼层', self._choose_floor)
        scale_main = StateOperationNode('主区域缩放地图', self._scale_main_region)
        choose_sub = StateOperationNode('选择子区域', self._choose_sub_region)
        scale_sub = StateOperationNode('子区域缩放地图', self._scale_sub_region)

        nodes = [check, choose_region, choose_floor, scale_main]
        if self.region.parent is not None:
            nodes.append(choose_sub)
            nodes.append(scale_sub)

        super().__init__(ctx, try_times=20,
                         op_name=gt('选择区域 %s') % region.display_name,
                         nodes=nodes
                         )

    def _check_planet(self) -> OperationOneRoundResult:
        if self.skip_planet_check:
            return self.round_success()
        screen = self.screenshot()

        planet = large_map.get_planet(screen, self.ctx.ocr)
        if planet is None or planet != self.planet:
            return self.round_wait('未在星球 %s' % self.planet.cn)
        else:
            return self.round_success()

    def _choose_region(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        area = ScreenLargeMap.TP_BTN.value
        click = self.find_and_click_area(area, screen)
        if click == Operation.OCR_CLICK_SUCCESS:
            # 右侧出现的传送 先取消掉
            return self.round_wait(wait=1)

        # 判断当前选择区域是否目标区域
        current_region_name = large_map.get_active_region_name(screen, self.ctx.ocr)
        current_region = best_match_region_by_name(current_region_name, planet=self.planet)
        print(current_region_name, current_region)
        log.info('当前区域文本 %s 匹配区域名称 %s', current_region_name,
                 current_region.cn if current_region is not None else '')

        is_current: bool = (current_region is not None and current_region.pr_id == self.region_to_choose_1.pr_id)

        # 还没有选好区域
        if not is_current:
            region_pos_list = self.get_region_pos_list(screen)
            pr_id_set: set[str] = set()
            for region_pos in region_pos_list:
                pr_id_set.add(region_pos.data.pr_id)
                if region_pos.data.pr_id == self.region_to_choose_1.pr_id:
                    self.ctx.controller.click(region_pos.center)
                    return self.round_retry(wait=1)

            # 没有发现目标区域 需要滚动
            with_before_region: bool = False  # 当前区域列表在目标区域之前
            region_list = PLANET_2_REGION.get(self.region_to_choose_1.planet.np_id)
            for r in region_list:
                if r.pr_id in pr_id_set:
                    with_before_region = True
                if r.pr_id == self.region_to_choose_1.pr_id:
                    break

            self.scroll_region_area(1 if with_before_region else -1)
            return self.round_retry(wait=1)
        else:
            return self.round_success()

    def get_region_pos_list(self, screen: MatLike, confidence: int = 0.3) -> List[MatchResult]:
        """
        获取当前屏幕显示的区域
        MatchResult.data = Region
        匹配全部显示的区域，是为了可以明确知道最后需要往哪个方向滚动。随机滚动存在卡死的可能。
        :param screen:
        :param confidence: 文本匹配的阈值 后续考虑替换掉 lcs_percent
        :return:
        """
        area = ScreenLargeMap.REGION_LIST.value
        part = cv2_utils.crop_image_only(screen, area.rect)
        ocr_map = self.ctx.ocr.run_ocr(part, merge_line_distance=40)

        # 初始化data 原来应该是 ocr 的文本
        for word, mrl in ocr_map.items():
            result = mrl.max
            if result is None:
                continue
            result.data = None
            result.x += area.rect.left_top.x
            result.y += area.rect.left_top.y

        # 匹诺康尼中 存在【现实】和【梦境】的小分类
        # 通过使用区域列表 在匹配结果中找到最合适的 避免选择到【现实】和【梦境】
        word_2_region_list: dict[str, List[Region]] = {}
        ocr_word_list = list(ocr_map.keys())
        plan_region_list = PLANET_2_REGION.get(self.region_to_choose_1.planet.np_id)
        for real_region in plan_region_list:
            match = difflib.get_close_matches(gt(real_region.cn, 'ocr'),
                                              ocr_word_list, n=1, cutoff=confidence)
            if len(match) == 0:
                continue

            # 理论上 可能出现两个区域(real_region)都匹配到一个目标(ocr_word)上
            # 例如 基座舱段 和 收容舱段 (real_region) 都匹配到了 收容舱段(ocr_word) 上
            # 但如果截图上就只有 收容舱段(ocr_word) 想要选择 基座舱段(real_region) 也会点击到 收容舱段(ocr_word) 上
            # 这时候先保存下来，再用 收容舱段(ocr_word) 匹配一个最佳的 real_region
            if match[0] not in word_2_region_list:
                word_2_region_list[match[0]] = [real_region]
            else:
                word_2_region_list[match[0]].append(real_region)

        # 最终返回结果
        result_list: List[MatchResult] = []
        for ocr_word, mrl in ocr_map.items():
            result = mrl.max
            if result is None:
                continue
            if ocr_word not in word_2_region_list:
                continue

            region_list: List[Region] = word_2_region_list[ocr_word]
            if len(region_list) == 1:
                result.data = region_list[0]
            else:
                region_name_list = [gt(region.cn, 'ocr') for region in region_list]
                match = difflib.get_close_matches(ocr_word, region_name_list, n=1, cutoff=confidence)
                if len(match) == 0:
                    continue
                for region in region_list:
                    if gt(region.cn, 'ocr') == match[0]:
                        result.data = region
                        break

            if result.data is not None:
                result_list.append(result)

        return result_list

    def scroll_region_area(self, d: int = 1):
        """
        在选择区域的地方滚动鼠标
        :param d: 滚动距离 正向下 负向上
        :return:
        """
        drag_to = large_map.REGION_LIST_RECT.center
        drag_from = Point(0, d * 200) + drag_to
        self.ctx.controller.drag_to(start=drag_from, end=drag_to, duration=0.5)

    def _choose_floor(self):
        op = ChooseFloor(self.ctx, self.region_to_choose_1.floor)
        return self.round_by_op(op.execute())

    def _scale_main_region(self) -> OperationOneRoundResult:
        if self.ctx.pos_lm_scale != self.region_to_choose_1.large_map_scale:
            op = ScaleLargeMap(self.ctx, self.region_to_choose_1.large_map_scale, is_main_region=True)
            return self.round_by_op(op.execute())
        else:
            return self.round_success('无需缩放')

    def _choose_sub_region(self) -> OperationOneRoundResult:
        if self.region.parent is None:
            return self.round_success('非子区域无需操作')

        screen = self.screenshot()

        if self.sub_region_clicked and self._in_sub_region(screen):
            return self.round_success(wait=1)

        screen_part, offset = match_screen_in_large_map(self.ctx, screen, self.region_to_choose_1)
        if offset is None:
            log.error('匹配大地图失败')
            drag_in_large_map(self.ctx)
            return self.round_retry(wait=0.5)
        else:
            dx, dy = get_map_next_drag(self.region.enter_lm_pos, offset)
            screen_map_rect = large_map.get_screen_map_rect(self.region_to_choose_1)

            if dx == 0 and dy == 0:  # 当前就能找传送点
                target: MatchResult = self._get_sub_enter_pos(screen_part, offset)
                if target is None:  # 没找到的话 按计算坐标点击
                    to_click = self.region.enter_lm_pos - offset.left_top + screen_map_rect.left_top
                    self.ctx.controller.click(to_click)
                else:
                    to_click = target.center + screen_map_rect.left_top
                    self.ctx.controller.click(to_click)
                self.sub_region_clicked = True
            else:
                drag_in_large_map(self.ctx, dx, dy)

            return self.round_retry(wait=0.5)

    def _in_sub_region(self, screen: MatLike) -> bool:
        """
        判断是否已经进入子区域 左上角显示的父区域的名字
        :return:
        """
        title_part = cv2_utils.crop_image_only(screen, ScreenLargeMap.PLANET_NAME.value.rect)
        ocr_result = self.ctx.ocr.ocr_for_single_line(title_part)
        ocr_region = best_match_region_by_name(ocr_result, self.region.planet)
        if ocr_region is None:
            return False
        else:
            return ocr_region.pr_id == self.region.parent.pr_id

    def _get_sub_enter_pos(self, screen_part: MatLike, offset: MatchResult):
        """
        在当前屏幕地图上匹配子区域入口
        :param screen_part: 屏幕上的大地图部分
        :param offset: 屏幕上的地图在完整大地图上的偏移量
        :return:
        """
        if self.region.enter_lm_pos is not None:
            sm_offset_x = self.region.enter_lm_pos.x - offset.x
            sm_offset_y = self.region.enter_lm_pos.y - offset.y
            sp_rect = Rect(sm_offset_x - 100, sm_offset_y - 100, sm_offset_x + 100, sm_offset_y + 100)
            crop_screen_map, sp_rect = cv2_utils.crop_image(screen_part, sp_rect)
            result: MatchResultList = self.ctx.im.match_template(crop_screen_map,
                                                                 self.region.enter_template_id,
                                                                 threshold=const.THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP)

            if result.max is not None:
                return MatchResult(result.max.confidence,
                                   result.max.x + sp_rect.x1,
                                   result.max.y + sp_rect.y1,
                                   result.max.w,
                                   result.max.h
                                   )
            else:
                return None
        else:
            result: MatchResultList = self.ctx.im.match_template(screen_part, self.region.enter_template_id,
                                                                 threshold=const.THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP)
            return result.max

    def _scale_sub_region(self):
        """
        进入子区域后进行缩放
        :return:
        """
        if self.region.parent is None:
            return self.round_success('非子区域无需操作')

        if self.ctx.pos_lm_scale != self.region.large_map_scale:
            op = ScaleLargeMap(self.ctx, self.region.large_map_scale, is_main_region=False)
            return self.round_by_op(op.execute())
        else:
            return self.round_success('无需缩放')


class ChooseFloor(Operation):

    def __init__(self, ctx: Context, floor: int, sub_region: bool = False):
        self.floor: int = floor
        self.target_floor_str = gt('%d层' % self.floor, 'ocr')
        self.neg_target_floor_str = gt('%d层' % (-self.floor), 'ocr')
        self.sub_region: bool = sub_region  # 是否子地图
        super().__init__(ctx, try_times=20,
                         op_name='%s %d' % (gt('选择楼层', 'ui'), floor)
                         )

    def _execute_one_round(self) -> OperationOneRoundResult:
        screen = self.screenshot()

        # 已经选好了区域 还需要选择层数
        if self.floor != 0:
            current_floor_str = large_map.get_active_floor(screen, self.ctx.ocr)
            log.info('当前层数 %s', current_floor_str)
            if current_floor_str is None:
                log.error('未找到当前选择的层数')
            log.info('目标层数 %s', self.target_floor_str)
            if self.target_floor_str != current_floor_str:
                cl = self.click_target_floor(screen)
                if not cl:
                    log.error('未成功点击层数')
                    return self.round_retry(wait=0.5)
                else:
                    return self.round_success(wait=0.5)
            else:  # 已经是目标楼层
                return self.round_success(wait=0.5)
        else:
            return self.round_success()

    def click_target_floor(self, screen) -> bool:
        """
        点击目标层数
        :param screen: 大地图界面截图
        :return:
        """
        pos = self.get_target_floor_pos(screen)
        if pos is not None:
            log.debug('选择楼层点击 %s', pos)
            return self.ctx.controller.click(pos)
        else:
            return False

    def get_target_floor_pos(self, screen: MatLike) -> Optional[Point]:
        """
        获取目标楼层的位置
        :param screen:
        :return:
        """
        area = ScreenLargeMap.FLOOR_LIST.value
        part = cv2_utils.crop_image_only(screen, area.rect)
        # cv2_utils.show_image(part, wait=0)
        ocr_results = self.ctx.ocr.run_ocr(part)

        if self.target_floor_str in ocr_results:
            mrl = ocr_results[self.target_floor_str]
        elif self.floor < 0 and self.neg_target_floor_str in ocr_results:  # 中文负数的识别结果比较不好 看看有没有正数的结果
            mrl = ocr_results[self.neg_target_floor_str]
        else:
            mrl = None

        if mrl is None:
            return None
        elif len(mrl) == 1:
            return mrl.max.center + area.rect.left_top
        else:
            target_mr: Optional[MatchResult] = None
            for mr in mrl:
                if (
                        target_mr is None
                        or (self.floor < 0 and mr.center.y > target_mr.center.y)  # 负数楼层选y轴大的
                        or (self.floor > 0 and mr.center.y < target_mr.center.y)  # 正数楼层选y轴小的
                ):
                    target_mr = mr
            return target_mr.center + area.rect.left_top


class ChooseTransportPoint(Operation):
    tp_name_rect: ClassVar[Rect] = Rect(1485, 120, 1870, 170)  # 右侧显示传送点名称的区域
    drag_distance: ClassVar[int] = -200

    def __init__(self, ctx: Context, tp: TransportPoint):
        super().__init__(ctx, 10, op_name=gt('选择传送点 %s') % tp.display_name)
        self.tp: TransportPoint = tp
        self.lm_info: LargeMapInfo = self.ctx.ih.get_large_map(self.tp.region)

    def _execute_one_round(self) -> int:
        screen = self.screenshot()

        # 判断地图中间是否有目标点中文可选
        if self.check_and_click_sp_cn(screen):
            time.sleep(1)
            return Operation.WAIT

        # 先判断右边是不是出现传送了
        if self.check_and_click_transport(screen):
            self.ctx.update_pos_after_tp(self.tp)
            time.sleep(2)
            return Operation.SUCCESS

        # 目标点中文 不是传送 或者不是目标传送点 点击一下地图空白位置
        self.ctx.controller.click(large_map.EMPTY_MAP_POS)
        time.sleep(0.5)

        screen_part, offset = match_screen_in_large_map(self.ctx, screen, self.tp.region)
        if offset is None:
            log.error('匹配大地图失败')
            drag_in_large_map(self.ctx)
            time.sleep(0.5)
            return Operation.RETRY

        dx, dy = get_map_next_drag(self.tp.lm_pos, offset)

        if dx == 0 and dy == 0:  # 当前就能找传送点
            target: MatchResult = self.get_tp_pos(screen_part, offset)
            screen_map_rect = large_map.get_screen_map_rect(self.tp.region)
            if target is None:  # 没找到的话 按计算坐标点击
                to_click = self.tp.lm_pos - offset.left_top + screen_map_rect.left_top
                self.ctx.controller.click(to_click)
                time.sleep(0.5)
            else:
                to_click = target.center + screen_map_rect.left_top
                self.ctx.controller.click(to_click)
                time.sleep(0.5)

        if dx != 0 or dy != 0:
            drag_in_large_map(self.ctx, dx, dy)
            time.sleep(0.5)

        return Operation.RETRY

    def check_and_click_transport(self, screen: MatLike):
        """
        判断右侧是否出现传送 已经是否对应的传送点
        如果是 则点击
        :param screen: 屏幕截图
        :return: 是否点击传送
        """
        tp_btn_part, _ = cv2_utils.crop_image(screen, large_map.TP_BTN_RECT)
        # cv2_utils.show_image(tp_btn_part, win_name='tp_btn_part')
        tp_btn_ocr = self.ctx.ocr.match_words(tp_btn_part, ['传送'])
        if len(tp_btn_ocr) > 0:
            # 看看是否目标传送点
            tp_name_part, _ = cv2_utils.crop_image(screen, ChooseTransportPoint.tp_name_rect)
            lower_color = np.array([55, 55, 55], dtype=np.uint8)
            upper_color = np.array([255, 255, 255], dtype=np.uint8)
            gold_part = cv2.inRange(tp_name_part, lower_color, upper_color)
            current_lang: str = self.ctx.game_config.lang
            if current_lang == game_config_const.LANG_CN:
                gold_part = cv2_utils.dilate(gold_part, 1)
            tp_name_str: str = None
            if current_lang == game_config_const.LANG_CN:
                tp_name_str = self.ctx.ocr.ocr_for_single_line(gold_part)
            elif current_lang == game_config_const.LANG_EN:
                ocr_result: dict = self.ctx.ocr.run_ocr(gold_part)
                tp_name_str = None
                for k in ocr_result.keys():
                    if tp_name_str is None:
                        tp_name_str = k
                    else:
                        tp_name_str += ' ' + k

            log.info('当前选择传送点名称 %s', tp_name_str)
            # cv2_utils.show_image(gold_part, win_name='gold_part')
            if (tp_name_str is not None and
                    str_utils.find_by_lcs(gt(self.tp.cn, 'ocr'), tp_name_str, ignore_case=True,
                                          percent=self.gc.special_point_lcs_percent)):
                # 点击传送
                to_click = large_map.TP_BTN_RECT.left_top
                for r in tp_btn_ocr.values():
                    to_click = to_click + r.max.center
                    break
                return self.ctx.controller.click(to_click)
        return False

    def get_tp_pos(self, screen_part: MatLike, offset: MatchResult):
        """
        在当前屏幕地图上匹配传送点 在传送点位置
        :param screen_part: 屏幕上的地图部分
        :param offset: 屏幕上的地图在完整大地图上的偏移量
        :return:
        """
        if self.tp.lm_pos is not None:
            sm_offset_x = self.tp.lm_pos.x - offset.x
            sm_offset_y = self.tp.lm_pos.y - offset.y
            sp_rect = Rect(sm_offset_x - 100, sm_offset_y - 100, sm_offset_x + 100, sm_offset_y + 100)
            crop_screen_map, sp_rect = cv2_utils.crop_image(screen_part, sp_rect)
            result: MatchResultList = self.ctx.im.match_template(crop_screen_map, self.tp.template_id,
                                                                 threshold=const.THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP)

            if result.max is not None:
                return MatchResult(result.max.confidence,
                                   result.max.x + sp_rect.x1,
                                   result.max.y + sp_rect.y1,
                                   result.max.w,
                                   result.max.h
                                   )
            else:
                return None
        else:
            result: MatchResultList = self.ctx.im.match_template(screen_part, self.tp.template_id,
                                                                 threshold=const.THRESHOLD_SP_TEMPLATE_IN_LARGE_MAP)
            return result.max

    def check_and_click_sp_cn(self, screen) -> bool:
        """
        判断地图中间是否有目标点中文可选 两个特殊点重叠的时候会出现
        发现的话进行点击
        :param screen: 屏幕截图
        :return:
        """
        screen_map_rect = large_map.get_screen_map_rect(self.tp.region)
        screen_map = cv2_utils.crop_image_only(screen, screen_map_rect)

        l = 190
        u = 255
        lower_color = np.array([l, l, l], dtype=np.uint8)
        upper_color = np.array([u, u, u], dtype=np.uint8)
        white_part = cv2.inRange(screen_map, lower_color, upper_color)  # 提取白色部分方便匹配

        # cv2_utils.show_image(white_part, win_name='check_and_click_sp_cn')
        ocr_result = self.ctx.ocr.match_words(white_part, words=[self.tp.cn],
                                              lcs_percent=self.gc.special_point_lcs_percent)

        for r in ocr_result.values():
            to_click = r.max.center + screen_map_rect.left_top
            return self.ctx.controller.click(to_click)

        return False


def match_screen_in_large_map(ctx: Context, screen: MatLike, region: Region) -> Tuple[MatLike, MatchResult]:
    """
    在当前屏幕截图中扣出大地图部分，并匹配到完整大地图上获取偏移量
    :param ctx:
    :param screen: 游戏屏幕截图
    :param region: 目标区域
    :return:
    """
    screen_map_rect = large_map.get_screen_map_rect(region)
    screen_part = cv2_utils.crop_image_only(screen, screen_map_rect)
    lm_info = ctx.ih.get_large_map(region)
    result: MatchResultList = ctx.im.match_image(lm_info.origin, screen_part)

    return screen_part, result.max


def drag_in_large_map(ctx: Context, dx: Optional[int] = None, dy: Optional[int] = None):
    """
    在大地图上拖动
    :param ctx:
    :param dx:
    :param dy:
    :return:
    """
    if dx is None:
        dx = 1 if random.randint(0, 1) == 1 else -1
    if dy is None:
        dy = 1 if random.randint(0, 1) == 1 else -1
    fx, fy = large_map.EMPTY_MAP_POS.tuple()
    tx, ty = fx + ChooseTransportPoint.drag_distance * dx, fy + ChooseTransportPoint.drag_distance * dy
    log.info('拖动地图 %s -> %s', (fx, fy), (tx, ty))
    ctx.controller.drag_to(end=Point(tx, ty), start=Point(fx, fy), duration=1)


def get_map_next_drag(lm_pos: Point, offset: MatchResult) -> Tuple[int, int]:
    """
    判断当前显示的部分大地图是否已经涵盖到目标点的坐标
    如果没有 则返回需要往哪个方向拖动
    :param lm_pos: 目标点在大地图上的坐标
    :param offset: 偏移量
    :return: 后续拖动方向 正代表坐标需要增加 正代表坐标需要减少
    """
    # 匹配结果矩形
    x1, y1 = offset.x, offset.y
    x2, y2 = x1 + offset.w, y1 + offset.h
    # 目标点坐标
    x, y = lm_pos.x, lm_pos.y

    dx, dy = 0, 0
    if x > x2:
        dx = 1
    elif x < x1:
        dx = -1
    if y > y2:
        dy = 1
    elif y < y1:
        dy = -1
    return dx, dy


class ScaleLargeMap(Operation):

    def __init__(self, ctx: Context, to_scale: int, is_main_region: bool = True):
        """
        默认在大地图页面 点击缩放按钮
        :param to_scale: 目标缩放比例
        :param is_main_region: 是否主区域
        """
        super().__init__(ctx, 5, op_name=gt('缩放地图至 %d', 'ui') % to_scale)
        self.is_main_region: bool = is_main_region
        self.to_scale: int = to_scale
        self.scale_per_time: int = -1 if to_scale < self.ctx.pos_lm_scale else 1  # 负数为缩小，正数为放大

    def _execute_one_round(self) -> OperationOneRoundResult:
        if self.to_scale == self.ctx.pos_lm_scale:
            return self.round_success()

        # 没有使用模板匹配找加减号的位置 实际测试无法区分减价
        if self.is_main_region:
            area = ScreenLargeMap.MAIN_SCALE_MINUS.value if self.scale_per_time < 0 else ScreenLargeMap.MAIN_SCALE_PLUS.value
        else:
            area = ScreenLargeMap.SUB_SCALE_MINUS.value if self.scale_per_time < 0 else ScreenLargeMap.SUB_SCALE_PLUS.value
        log.info('准备缩放地图 点击 %s %s', area.center,
                 self.ctx.controller.click(area.center))
        self.ctx.pos_lm_scale += self.scale_per_time
        if self.to_scale == self.ctx.pos_lm_scale:
            return self.round_success()
        else:
            return self.round_wait(wait=0.5)
