from typing import Optional, List

import cv2
import flet as ft
import keyboard
import yaml
from cv2.typing import MatLike

from basic import Point
from basic.i18_utils import gt
from basic.img import cv2_utils, MatchResult
from basic.img.os import get_debug_image
from basic.log_utils import log
from gui import components
from gui.settings import gui_config
from gui.settings.gui_config import ThemeColors
from gui.sr_basic_view import SrBasicView
from sr import cal_pos
from sr.app.sim_uni.sim_uni_route_holder import get_sim_uni_route_list, clear_sim_uni_route_cache, \
    match_best_sim_uni_route
from sr.sim_uni.sim_uni_route import SimUniRouteOperation, SimUniRoute
from sr.app.sim_uni.test_sim_uni_route_app import TestSimUniRouteApp
from sr.const import map_const, operation_const
from sr.context import Context
from sr.image.sceenshot import mini_map, LargeMapInfo, large_map
from sr.sim_uni.sim_uni_const import UNI_NUM_CN, level_type_from_id, SimUniLevelTypeEnum


class SimUniDraftRouteView(ft.Row, SrBasicView):

    def __init__(self, page: ft.Page, ctx: Context):
        SrBasicView.__init__(self, page, ctx)
        theme: ThemeColors = gui_config.theme()

        self.keyboard_hook = None

        self.existed_route_dropdown = ft.Dropdown(
            label='编辑已有路线', disabled=True, width=200,
            on_change=self._on_chosen_route_changed
        )
        self.algo_dropdown = ft.Dropdown(label='使用算法', width=100, disabled=True,
                                         options=[ft.dropdown.Option(text=str(i), key=str(i)) for i in range(1, 3)],
                                         value='1', on_change=self._on_algo_changed)
        self.cancel_edit_existed_btn = components.RectOutlinedButton(
            text='取消编辑', disabled=True,on_click=self._cancel_edit_existed)
        self.num_dropdown = ft.Dropdown(
            label=gt('选择宇宙', 'ui'), width=150,
            options=[
                ft.dropdown.Option(key=str(num), text=gt('第%s宇宙' % cn, 'ui')) for num, cn in UNI_NUM_CN.items()
            ],
            value='8',  # TODO 测试用默认选项
            on_change=self._on_uni_changed
        )
        self.level_type_dropdown = ft.Dropdown(
            label=gt('楼层类型', 'ui'), width=150,
            options=[
                ft.dropdown.Option(key=i.value.type_id, text=gt(i.value.type_name, 'ui')) for i in SimUniLevelTypeEnum
            ],
            on_change=self._on_uni_changed
        )
        self.save_btn = components.RectOutlinedButton(text='新建', disabled=True, on_click=self._do_save)
        self.delete_btn = components.RectOutlinedButton(text='删除', disabled=True, on_click=self._do_delete)
        self.test_btn = components.RectOutlinedButton(text='测试', disabled=True, on_click=self._do_test)
        route_btn_row = ft.Row(controls=[self.num_dropdown, self.level_type_dropdown,self.existed_route_dropdown, self.algo_dropdown])
        route_op_btn_row = ft.Row(controls=[self.cancel_edit_existed_btn, self.save_btn, self.delete_btn, self.test_btn])

        self.screenshot_btn = components.RectOutlinedButton(text=gt('F8 截图', 'ui'), on_click=self._do_screenshot, disabled=True)
        self.match_start_btn = components.RectOutlinedButton(text=gt('开始点匹配', 'ui'), on_click=self._cal_start_pos, disabled=True)
        self.previous_start_btn = components.RectOutlinedButton(text=gt('上一个', 'ui'), on_click=self._on_previous_start_clicked, disabled=True)
        self.next_start_btn = components.RectOutlinedButton(text=gt('下一个', 'ui'), on_click=self._on_next_start_clicked, disabled=True)
        self.set_start_btn = components.RectOutlinedButton(text=gt('选定开始点', 'ui'), on_click=self._on_set_start_clicked, disabled=True)
        self.cal_pos_btn = components.RectOutlinedButton(text=gt('计算坐标', 'ui'), on_click=self._on_cal_pos_clicked, disabled=True)
        screenshot_row = ft.Row(controls=[self.screenshot_btn,
                                          self.match_start_btn, self.previous_start_btn, self.next_start_btn, self.set_start_btn,
                                          self.cal_pos_btn])

        self.back_btn = components.RectOutlinedButton(text='后退', disabled=True, on_click=self._del_last_op)
        self.reset_btn = components.RectOutlinedButton(text='重置', disabled=True, on_click=self._clear_op)
        self.patrol_btn = components.RectOutlinedButton(text='攻击怪物', disabled=True, on_click=self._add_patrol)
        self.disposable_btn = components.RectOutlinedButton(text='攻击破坏物', disabled=True, on_click=self._add_disposable)
        self.slow_move_btn = components.RectOutlinedButton(text='禁疾跑', disabled=True, on_click=self._change_slow_move)
        self.no_pos_move_btn = components.RectOutlinedButton(text='机械移动', disabled=True, on_click=self._change_no_pos_move)
        self.add_next_btn = components.RectOutlinedButton(text='下层入口', disabled=True, on_click=self._add_next)
        self.add_reward_btn = components.RectOutlinedButton(text='沉浸奖励', disabled=True, on_click=self._add_reward)
        op_btn_row = ft.Row(controls=[self.back_btn, self.reset_btn, self.patrol_btn, self.disposable_btn,
                                      self.no_pos_move_btn, self.slow_move_btn,
                                      self.add_next_btn, self.add_reward_btn])

        info_card_width = 200
        self.screenshot_mm_display = ft.Image(src="a.png", error_content=ft.Text('等待截图'), visible=False)

        self.route_text = ft.TextField(multiline=True, min_lines=10, max_lines=27,
                                       width=info_card_width,
                                       on_blur=self._on_route_text_blur)
        info_card_content = ft.Column(controls=[
            ft.Container(content=components.CardTitleText('当前截图'), width=info_card_width,
                         border=ft.border.only(bottom=ft.border.BorderSide(1, theme['divider_color']))),
            self.screenshot_mm_display,
            ft.Container(content=components.CardTitleText('路线配置'), width=info_card_width,
                         border=ft.border.only(bottom=ft.border.BorderSide(1, theme['divider_color']))),
            self.route_text
        ], scroll=ft.ScrollMode.AUTO)

        info_card = components.Card(
            content=info_card_content,
            width=info_card_width
        )

        self.large_map_display = ft.Image(src="a.png", error_content=ft.Text('等待选择区域'), visible=False)
        self.large_map_width = 1000

        display_part = ft.Column(
            controls=[
                ft.Container(margin=ft.margin.only(top=5)),  # 单纯用来调整一下间隔
                route_btn_row,
                route_op_btn_row,
                screenshot_row,
                op_btn_row,
                ft.Container(content=self.large_map_display, width=self.large_map_width, height=self.large_map_width,
                             on_click=self._on_large_map_click,
                             alignment=ft.alignment.top_left)
            ],
            scroll=ft.ScrollMode.AUTO
        )

        op_card = components.Card(
            content=display_part,
            title=components.CardTitleText('控制面板'),
            width=self.large_map_width + 50
        )

        ft.Row.__init__(self, controls=[op_card, info_card], vertical_alignment=ft.CrossAxisAlignment.START,
                        spacing=10)

        self.mini_map_image: Optional[MatLike] = None  # 当前显示的小地图图片
        self.start_pos_list: List[MatchResult] = []  # 开始点候选名单
        self.chosen_start_pos_idx: int = 0  # 开始点候选名单的下标
        self.existed_route_list: Optional[List[SimUniRoute]] = None  # 当前选择宇宙下存在的路线

        self.chosen_route: Optional[SimUniRoute] = None  # 当前编辑的路线

    def handle_after_show(self):
        self.keyboard_hook = keyboard.on_press(self._on_key_press)
        screen = get_debug_image('5')
        if screen is not None:
            self.mini_map_image = mini_map.cut_mini_map(screen, self.sr_ctx.game_config.mini_map_pos)
            self._show_screenshot_mm()

    def handle_after_hide(self):
        keyboard.unhook(self.keyboard_hook)

    def _on_key_press(self, event):
        k = event.name
        if k == 'f8' and self.chosen_route is not None:
            self._do_screenshot()

    def _do_screenshot(self, e=None):
        """
        进行具体截图 并将小地图展示出来
        :param e:
        :return:
        """
        self.sr_ctx.init_image_matcher()
        self.sr_ctx.init_controller()
        self.sr_ctx.controller.init()
        screen = self.sr_ctx.controller.screenshot()
        self.mini_map_image = mini_map.cut_mini_map(screen, self.sr_ctx.game_config.mini_map_pos)
        self._show_screenshot_mm()
        self._update_screenshot_row()

    def _show_screenshot_mm(self):
        """
        展示当前截图的小地图
        :return:
        """
        if self.mini_map_image is None:
            self.screenshot_mm_display.visible = False
        else:
            self.screenshot_mm_display.src_base64 = cv2_utils.to_base64(self.mini_map_image)
            self.screenshot_mm_display.visible = True
        self.screenshot_mm_display.update()

    def _cal_start_pos(self, e=None):
        """
        计算起始坐标
        :return:
        """
        if self.mini_map_image is None:
            return

        level_type = level_type_from_id(self.level_type_dropdown.value)
        if self.chosen_route.region is None:
            existed_route = match_best_sim_uni_route(int(self.num_dropdown.value), level_type, self.mini_map_image)
            if existed_route is not None:
                log.info('已有地图 %s', existed_route.display_name)
                self.existed_route_dropdown.value = existed_route.uid
                self._on_chosen_route_changed()
                return
        else:
            level_type = level_type_from_id(self.level_type_dropdown.value)
            self.chosen_route = SimUniRoute(level_type.route_id)

        self.sr_ctx.init_image_matcher()
        mm_info = mini_map.analyse_mini_map(self.mini_map_image)

        pos_list: List[MatchResult] = []

        for _, region_list in map_const.PLANET_2_REGION.items():
            for region in region_list:
                # if region != map_const.P03_R03_F1:
                #     continue
                lm_info = self.sr_ctx.ih.get_large_map(region)
                if lm_info is None or lm_info.origin is None or lm_info.gray is None:
                    log.error('找不到大地图 %s', region.prl_id)
                    continue
                pos: MatchResult = cal_pos.sim_uni_cal_pos_by_gray(self.sr_ctx.im, lm_info, mm_info,
                                                                   scale_list=[1], match_threshold=0.2)
                if pos is None:
                    pos = cal_pos.sim_uni_cal_pos_by_original(self.sr_ctx.im, lm_info, mm_info,
                                                              scale_list=[1], match_threshold=0.2)
                log.info('匹配 %s 结果 %s', region.display_name, pos)
                if pos is None:
                    continue

                pos.data = region
                pos_list.append(pos)

        self.start_pos_list = sorted(pos_list, key=lambda x: x.confidence, reverse=True)
        self.chosen_start_pos_idx = 0
        self._update_screenshot_row()
        self._update_large_map_display()

    def _update_large_map_display(self):
        """
        显示大地图
        :return:
        """
        lm_info: Optional[LargeMapInfo] = None
        if self.chosen_route is None:  # 新建时候也会有一个route
            pass
        elif self.chosen_route.region is None:  # 还在匹配开始点
            if 0 <= self.chosen_start_pos_idx < len(self.start_pos_list):
                lm_info = self.sr_ctx.ih.get_large_map(self.start_pos_list[self.chosen_start_pos_idx].data)
        else:
            lm_info = self.sr_ctx.ih.get_large_map(self.chosen_route.region)

        if lm_info is None:
            self.large_map_display.visible = False
            self.large_map_display.update()
            return

        display_image = lm_info.origin.copy()

        last_point: Point = self.start_pos_list[self.chosen_start_pos_idx].center if self.chosen_route.start_pos is None else self.chosen_route.start_pos
        cv2.circle(display_image, last_point.tuple(), 5, color=(0, 255, 0), thickness=2)
        for route_item in self.chosen_route.op_list:
            if route_item['op'] in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE, operation_const.OP_NO_POS_MOVE]:
                pos = Point(x=route_item['data'][0], y=route_item['data'][1])
                cv2.circle(display_image, pos.tuple(), 5, color=(0, 0, 255), thickness=-1)
                if last_point is not None:
                    if route_item['op'] == operation_const.OP_MOVE:
                        color = (255, 0, 0)
                    elif route_item['op'] == operation_const.OP_SLOW_MOVE:
                        color = (255, 80, 80)
                    elif route_item['op'] == operation_const.OP_NO_POS_MOVE:
                        color = (255, 160, 160)
                    else:
                        color = (255, 255, 255)
                    cv2.line(display_image, last_point.tuple(), pos.tuple(), color=color, thickness=2)
                last_point = pos
            elif route_item['op'] in [operation_const.OP_PATROL, operation_const.OP_DISPOSABLE]:
                if last_point is not None:
                    cv2.circle(display_image, last_point.tuple(), 10, color=(0, 255, 255), thickness=2)
            elif route_item['op'] == operation_const.OP_INTERACT:
                if last_point is not None:
                    cv2.circle(display_image, last_point.tuple(), 12, color=(255, 0, 255), thickness=2)
            elif route_item['op'] == operation_const.OP_WAIT:
                if last_point is not None:
                    cv2.circle(display_image, last_point.tuple(), 14, color=(255, 255, 255), thickness=2)
            elif route_item['op'] == operation_const.OP_UPDATE_POS:
                pos = Point(x=route_item['data'][0], y=route_item['data'][1])
                cv2.circle(display_image, pos.tuple(), 5, color=(0, 0, 255), thickness=-1)
                last_point = pos

        for pos in self.chosen_route.next_pos_list:
            cv2.circle(display_image, pos.tuple(), 5, color=(100, 255, 100), thickness=-1)

        if self.chosen_route.reward_pos is not None:
            cv2.circle(display_image, self.chosen_route.reward_pos.tuple(), 5,
                       color=(200, 255, 200), thickness=-1)

        self.large_map_display.src_base64 = cv2_utils.to_base64(display_image)
        self.large_map_display.visible = True
        self.large_map_display.update()

    def _update_screenshot_row(self):
        """
        更新截图行相关的按钮状态
        :return:
        """
        route_chosen = self.chosen_route is not None
        start_chosen = route_chosen and self.chosen_route.region is not None
        screenshot_mm = self.screenshot_mm_display.visible

        self.screenshot_btn.disabled = not route_chosen
        self.screenshot_btn.update()

        self.previous_start_btn.disabled = not route_chosen or start_chosen or not screenshot_mm or (self.chosen_start_pos_idx <= 0)
        self.previous_start_btn.update()

        self.next_start_btn.disabled = not route_chosen or start_chosen or not screenshot_mm or (self.chosen_start_pos_idx >= len(self.start_pos_list) - 1)
        self.next_start_btn.update()

        self.match_start_btn.disabled = not screenshot_mm or (self.mini_map_image is None)
        self.match_start_btn.update()

        self.set_start_btn.disabled = not route_chosen or start_chosen or not screenshot_mm or not (0 <= self.chosen_start_pos_idx < len(self.start_pos_list))
        self.set_start_btn.update()

        self.cal_pos_btn.disabled = not route_chosen or not start_chosen or not screenshot_mm
        self.cal_pos_btn.update()

    def _on_previous_start_clicked(self, e):
        """
        切换到上一个开始点候选
        :param e:
        :return:
        """
        if self.chosen_start_pos_idx <= 0:
            return
        self.chosen_start_pos_idx -= 1
        self._update_screenshot_row()
        self._update_large_map_display()

    def _on_next_start_clicked(self, e):
        """
        切换到下一个开始点候选
        :param e:
        :return:
        """
        if self.chosen_start_pos_idx >= len(self.start_pos_list):
            return
        self.chosen_start_pos_idx += 1
        self._update_screenshot_row()
        self._update_large_map_display()

    def _on_set_start_clicked(self, e):
        """
        选定开始点
        :param e:
        :return:
        """
        if not 0 <= self.chosen_start_pos_idx < len(self.start_pos_list):
            return
        start_pos = self.start_pos_list[self.chosen_start_pos_idx]
        self.chosen_route.mm = self.mini_map_image
        self.chosen_route.region = start_pos.data
        self.chosen_route.start_pos = start_pos.center
        self.chosen_start_pos_idx = 0
        self.start_pos_list.clear()
        self._update_screenshot_row()
        self._on_op_list_changed()

    def _on_large_map_click(self, e):
        if self.chosen_route is None or self.chosen_route.region is None:
            return

        map_image: MatLike = self.sr_ctx.ih.get_large_map(self.chosen_route.region).origin
        original_height, original_width = map_image.shape[:2]
        if original_height > original_width:
            scale = self.large_map_width / original_height
        else:
            scale = self.large_map_width / original_width

        x = int(e.local_x / scale)
        y = int(e.local_y / scale)

        if x > original_width or y > original_height:
            return

        self.chosen_route.op_list.append(SimUniRouteOperation(op=operation_const.OP_MOVE, data=[x, y]))
        self._on_op_list_changed()

    def _on_route_text_blur(self, e):
        """
        路线配置变更时触发
        :param e:
        :return:
        """
        if self.chosen_route is None:
            return
        data = yaml.safe_load(self.route_text.value)
        self.chosen_route.load_from_route_yml(data)
        self._on_op_list_changed()

    def _update_route_text_display(self):
        """
        更新路线配置的文本显示
        :return:
        """
        self.route_text.value = self.chosen_route.get_route_text() if self.chosen_route is not None else ''
        self.route_text.update()

    def _on_op_list_changed(self):
        """
        指令列表发生变化时候的统一处理
        :return:
        """
        self._update_large_map_display()
        self._update_route_text_display()
        self._update_op_row()

    def _add_patrol(self, e):
        """
        添加攻击怪物的点
        :param e:
        :return:
        """
        self.chosen_route.op_list.append(SimUniRouteOperation(op=operation_const.OP_PATROL))
        self._on_op_list_changed()

    def _add_disposable(self, e):
        """
        添加攻击破坏物的点
        :param e:
        :return:
        """
        self.chosen_route.op_list.append(SimUniRouteOperation(op=operation_const.OP_DISPOSABLE))
        self._on_op_list_changed()

    def _change_slow_move(self, e):
        """
        将最后一个移动点改为慢走
        :param e:
        :return:
        """
        if not self.chosen_route.is_last_op_move:
            return
        l = len(self.chosen_route.op_list)
        self.chosen_route.op_list[l-1]['op'] = operation_const.OP_SLOW_MOVE
        self._on_op_list_changed()

    def _change_no_pos_move(self, e):
        """
        将最后一个移动点改为机械移动
        :param e:
        :return:
        """
        if not self.chosen_route.is_last_op_move:
            return
        l = len(self.chosen_route.op_list)
        self.chosen_route.op_list[l-1]['op'] = operation_const.OP_NO_POS_MOVE
        self._on_op_list_changed()

    def _add_next(self, e):
        """
        将最后一个点加入到下层交互点中
        :param e:
        :return:
        """
        if not self.chosen_route.is_last_op_move:
            return
        op = self.chosen_route.op_list.pop()
        self.chosen_route.next_pos_list.append(Point(op['data'][0], op['data'][1]))
        self._on_op_list_changed()

    def _add_reward(self, e):
        """
        将最后一个点设置为奖励点
        :param e:
        :return:
        """
        if not self.chosen_route.is_last_op_move:
            return
        op = self.chosen_route.op_list.pop()
        self.chosen_route.reward_pos = Point(op['data'][0], op['data'][1])
        self._on_op_list_changed()

    def _del_last_op(self, e):
        """
        删除最后一个指令
        :param e:
        :return:
        """
        if len(self.chosen_route.op_list) == 0:
            return
        self.chosen_route.op_list.pop(len(self.chosen_route.op_list) - 1)
        self._on_op_list_changed()

    def _clear_op(self, e):
        """
        清除所有指令
        :param e:
        :return:
        """
        if len(self.chosen_route.op_list) == 0:
            return
        self.chosen_route.op_list.clear()
        self._on_op_list_changed()

    def _do_save(self, e=None):
        """
        保存路线
        :param e:
        :return:
        """
        if self.chosen_route is None:  # 新建的 需要找一个下标
            level_type = level_type_from_id(self.level_type_dropdown.value)
            self.chosen_route = SimUniRoute(level_type.route_id)
            self._update_screenshot_row()
        else:
            self.chosen_route.add_support_world(int(self.num_dropdown.value))
            self.chosen_route.save()

        clear_sim_uni_route_cache()
        self._update_route_btn_row()

    def _do_delete(self, e):
        """
        删除路线
        :param e:
        :return:
        """
        if self.chosen_route is None:
            return
        self.chosen_route.delete()
        clear_sim_uni_route_cache()
        self._cancel_edit_existed()

    def _update_op_row(self):
        """
        更新指令相关按钮的状态
        :return:
        """
        route_chosen = self.chosen_route is not None
        start_chosen = route_chosen and self.chosen_route.region is not None
        is_elite = self.level_type_dropdown.value == SimUniLevelTypeEnum.ELITE.value.type_id or \
                   self.level_type_dropdown.value == SimUniLevelTypeEnum.BOSS.value.type_id

        self.back_btn.disabled = not start_chosen or len(self.chosen_route.op_list) == 0

        self.reset_btn.disabled = not start_chosen or len(self.chosen_route.op_list) == 0

        self.patrol_btn.disabled = not start_chosen or len(self.chosen_route.op_list) == 0

        self.disposable_btn.disabled = not start_chosen or len(self.chosen_route.op_list) == 0

        self.slow_move_btn.disabled = not start_chosen or not self.chosen_route.is_last_op_move

        self.no_pos_move_btn.disabled = not start_chosen or not self.chosen_route.is_last_op_move

        self.add_next_btn.disabled = not start_chosen or not self.chosen_route.is_last_op_move

        self.add_reward_btn.disabled = not start_chosen or not self.chosen_route.is_last_op_move or not is_elite

        self.update()

    def _cancel_edit_existed(self, e=None):
        """
        取消编辑选择的路线
        :param e:
        :return:
        """
        self.chosen_route = None
        self.existed_route_dropdown.value = None
        self._update_route_btn_row()
        self._update_screenshot_row()
        self._update_op_row()
        self._update_route_text_display()
        self._update_large_map_display()

    def _on_cal_pos_clicked(self, e=None):
        """
        根据当前截图计算坐标 需要已经设定好了开始点
        即已经知道在哪个区域地图了
        :param e:
        :return:
        """
        if self.mini_map_image is None or self.chosen_route is None or self.chosen_route.region is None:
            log.info('需要先选定开始点和截图')
            return
        self.sr_ctx.init_image_matcher()
        mm_info = mini_map.analyse_mini_map(self.mini_map_image)

        lm_info = self.sr_ctx.ih.get_large_map(self.chosen_route.region)
        last_pos = self.chosen_route.last_pos
        possible_pos = (last_pos.x, last_pos.y, 20)
        lm_rect = large_map.get_large_map_rect_by_pos(lm_info.gray.shape, self.mini_map_image.shape[:2], possible_pos)
        pos: MatchResult = cal_pos.sim_uni_cal_pos_by_gray(self.sr_ctx.im, lm_info, mm_info, lm_rect=lm_rect,
                                                           scale_list=[1], match_threshold=0.3)

        if pos is None:
            log.info('计算坐标失败')
            return

        self.chosen_route.op_list.append(SimUniRouteOperation(op=operation_const.OP_MOVE, data=[pos.center.x, pos.center.y]))
        self._on_op_list_changed()

    def _update_route_btn_row(self):
        """
        更新
        :return:
        """
        uni_chosen = self.num_dropdown.value is not None and self.level_type_dropdown.value is not None
        route_chosen = self.chosen_route is not None
        start_chosen = route_chosen and self.chosen_route.region is not None

        self.existed_route_dropdown.disabled = not uni_chosen
        if not self.existed_route_dropdown.disabled:
            level_type = level_type_from_id(self.level_type_dropdown.value)
            self.existed_route_list = get_sim_uni_route_list(level_type)
            self.existed_route_dropdown.options = [
                ft.dropdown.Option(key=i.uid, text=i.display_name)
                for i in self.existed_route_list
            ]
            if route_chosen:
                self.existed_route_dropdown.value = self.chosen_route.uid

        self.algo_dropdown.disabled = not route_chosen
        self.algo_dropdown.value = str(self.chosen_route.algo)
        self.cancel_edit_existed_btn.disabled = not route_chosen

        self.num_dropdown.disabled = route_chosen

        self.level_type_dropdown.disabled = route_chosen

        self.save_btn.disabled = not uni_chosen
        self.save_btn.text = '新建' if not route_chosen else '保存'

        self.delete_btn.disabled = not route_chosen

        self.test_btn.disabled = not route_chosen

        self.update()

    def _on_uni_changed(self, e=None):
        """
        选择宇宙变更时回调
        :param e:
        :return:
        """
        self._update_route_btn_row()

    def _on_chosen_route_changed(self, e=None):
        """
        选择路线改变时的回调
        :param e:
        :return:
        """
        for i in self.existed_route_list:
            if i.uid == self.existed_route_dropdown.value:
                self.chosen_route = i
                break

        self._update_route_btn_row()
        self._update_screenshot_row()
        self._update_op_row()
        self._update_large_map_display()
        self._update_route_text_display()

    def _do_test(self, e=None):
        """
        进行路线测试 会先进行保存
        :param e:
        :return:
        """
        if self.chosen_route is None:
            log.error('未选择路线')
            return
        self._do_save()
        app = TestSimUniRouteApp(self.sr_ctx,
                                 int(self.num_dropdown.value),
                                 level_type_from_id(self.level_type_dropdown.value),
                                 self.chosen_route
                                 )
        app.execute()

    def _on_algo_changed(self, e):
        if self.chosen_route is None:
            log.error('未选择路线')
            return
        self.chosen_route.algo = int(self.algo_dropdown.value)
        self._update_route_text_display()


_sim_uni_draft_route_view: Optional[SimUniDraftRouteView] = None


def get(page: ft.Page, ctx: Context) -> SimUniDraftRouteView:
    global _sim_uni_draft_route_view
    if _sim_uni_draft_route_view is None:
        _sim_uni_draft_route_view = SimUniDraftRouteView(page, ctx)

    return _sim_uni_draft_route_view
