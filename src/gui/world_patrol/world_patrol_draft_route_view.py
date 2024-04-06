import base64
import os
from typing import List, Optional

import cv2
import flet as ft
import keyboard
import yaml
from cv2.typing import MatLike
from flet_core import ScrollMode

import sr.const.operation_const
from basic import os_utils, Point
from basic.i18_utils import gt
from basic.img import cv2_utils, MatchResult
from basic.log_utils import log
from gui import snack_bar, components
from gui.settings import gui_config
from gui.settings.gui_config import ThemeColors
from gui.sr_basic_view import SrBasicView
from sr import cal_pos
from sr.app.world_patrol.world_patrol_route import WorldPatrolRouteId, WorldPatrolRoute, load_all_route_id, new_route_id
from sr.app.world_patrol.world_patrol_whitelist_config import WorldPatrolWhitelist
from sr.app.world_patrol.world_patrol_app import WorldPatrol
from sr.const import map_const, operation_const
from sr.const.map_const import Planet, get_planet_by_cn, PLANET_LIST, PLANET_2_REGION, get_region_by_cn, Region, \
    REGION_2_SP, TransportPoint, region_with_another_floor
from sr.context import Context
from sr.image.sceenshot import mini_map, large_map


class WorldPatrolDraftRouteView(ft.Row, SrBasicView):

    def __init__(self, flet_page: ft.Page, sr_ctx: Context):
        SrBasicView.__init__(self, flet_page, sr_ctx)
        theme: ThemeColors = gui_config.theme()
        self.keyboard_hook = None

        self.chosen_planet: Optional[Planet] = None
        self.chosen_region: Optional[Region] = None
        self.chosen_sp: Optional[TransportPoint] = None
        self.chosen_route: Optional[WorldPatrolRoute] = None

        self.author_text = ft.TextField(label='作者署名', width=200, value='DoctorReid')
        author_row = ft.Row(spacing=10, controls=[
            self.author_text,
            ft.Text(value='留下您的大名可以让大家知道您的贡献，匿名提供也替大家谢谢您')
            ])

        self.existed_route_id_list: Optional[List[WorldPatrolRouteId]] = None
        self.existed_route_dropdown = ft.Dropdown(
            label='编辑已有路线',
            on_change=self.on_existed_route_changed
        )
        self.first_test_route: bool = True
        self.load_route_id_list()
        self.cancel_edit_existed_btn = components.RectOutlinedButton(text='取消编辑', disabled=True, on_click=self.on_cancel_edit_existed)
        self.test_existed_btn = components.RectOutlinedButton(text='测试', disabled=True, on_click=self.test_existed)
        self.back_btn = components.RectOutlinedButton(text='Q 后退', disabled=True, on_click=self.cancel_last)
        self.reset_btn = components.RectOutlinedButton(text='重置', disabled=True, on_click=self.cancel_all)
        self.save_btn = components.RectOutlinedButton(text='保存', disabled=True, on_click=self.save_route)
        self.delete_btn = components.RectOutlinedButton(text='删除', disabled=True, on_click=self.delete_route)
        load_existed_row = ft.Row(spacing=10, controls=[
            self.existed_route_dropdown,
            self.cancel_edit_existed_btn,
            self.test_existed_btn,
            self.back_btn, self.reset_btn, self.save_btn, self.delete_btn
        ])

        self.planet_dropdown = ft.Dropdown(
            label='星球',
            width=100,
            options=[
                ft.dropdown.Option(text=p.cn, key=p.cn) for p in PLANET_LIST
            ],
            on_change=self.on_planet_changed
        )
        self.region_dropdown = ft.Dropdown(label='区域', width=200, on_change=self.on_region_change)
        self.floor_dropdown = ft.Dropdown(label='层数', width=50, on_change=self.on_floor_changed)
        self.tp_dropdown = ft.Dropdown(label='传送点', width=200, on_change=self.on_sp_change)
        self.switch_floor_dropdown = ft.Dropdown(label='中途切换层数', width=150, on_change=self.on_switch_floor)
        self.scale_up_btn = components.RectOutlinedButton(text='放大', on_click=self._on_scale_up)
        self.scale_down_btn = components.RectOutlinedButton(text='缩小', on_click=self._on_scale_down)

        choose_row = ft.Row(
            spacing=10,
            controls=[self.planet_dropdown, self.region_dropdown, self.floor_dropdown, self.tp_dropdown, self.switch_floor_dropdown,
                      self.scale_up_btn, self.scale_down_btn]
        )

        self.screenshot_btn = components.RectOutlinedButton(text=gt('F8 截图', 'ui'), on_click=self._do_screenshot, disabled=True)
        self.mini_map_image: Optional[MatLike] = None  # 当前显示的小地图图片
        self.cal_pos_btn = components.RectOutlinedButton(text=gt('计算坐标', 'ui'), on_click=self._on_cal_pos_clicked, disabled=True)
        self.screen_cal_pos_btn = components.RectOutlinedButton(text=gt('R 截图计算坐标', 'ui'), on_click=self._on_screen_cal_pos_clicked, disabled=True)
        self.screen_patrol_btn = components.RectOutlinedButton(text=gt('F 截图攻击怪物', 'ui'), on_click=self._on_screen_patrol_clicked, disabled=True)
        self.screen_disposable_btn = components.RectOutlinedButton(text=gt('5 截图可破坏物', 'ui'), on_click=self._on_screen_disposable_clicked, disabled=True)

        self.patrol_btn = components.RectOutlinedButton(text='攻击怪物', disabled=True, on_click=self.add_patrol)
        self.disposable_btn = components.RectOutlinedButton(text='可破坏物', disabled=True, on_click=self.add_disposable)
        self.interact_text = ft.TextField(label="交互文本", width=150, disabled=True)
        self.interact_btn = components.RectOutlinedButton(text='交互', disabled=True, on_click=self.on_interact)
        self.update_pos_btn = components.RectOutlinedButton(text='传送更新坐标', disabled=True, on_click=self.on_update_pos)
        self.wait_timeout_text = ft.TextField(
            label='等待秒数', width=100,
        )
        self.wait_dropdown = ft.Dropdown(
            label='等待类型', width=100,
            options=[
                ft.dropdown.Option(text='主界面', key='in_world'),
                ft.dropdown.Option(text='秒数', key='seconds')
            ],
            on_change=self.on_wait_changed
        )
        self.add_wait_btn = components.RectOutlinedButton(text='等待', disabled=True, on_click=self.add_wait)
        self.no_run_btn = components.RectOutlinedButton(text='禁疾跑', disabled=True, on_click=self.add_no_run)

        screen_row = ft.Row(
            spacing=10,
            controls=[self.screenshot_btn, self.cal_pos_btn,
                      self.screen_cal_pos_btn, self.screen_patrol_btn, self.screen_disposable_btn]
        )

        ctrl_row = ft.Row(
            spacing=10,
            controls=[self.patrol_btn, self.disposable_btn, self.interact_text, self.interact_btn,
                      self.wait_dropdown, self.wait_timeout_text, self.add_wait_btn, self.update_pos_btn, self.no_run_btn]
        )

        self.large_map_width = 1000
        self.map_img = ft.Image(src="a.png", fit=ft.ImageFit.CONTAIN, error_content=ft.Text('等待选择区域'), visible=False)
        self.map_container = ft.Container(content=self.map_img, width=self.large_map_width, height=self.large_map_width,
                                          on_click=self.on_map_click, alignment=ft.alignment.top_left)

        display_part = ft.Column(
            controls=[
                ft.Container(content=author_row, padding=3),
                ft.Container(content=load_existed_row, padding=3),
                ft.Container(content=choose_row, padding=3),
                ft.Container(content=ctrl_row, padding=3),
                ft.Container(content=screen_row, padding=3),
                self.map_container
            ],
            scroll=ScrollMode.AUTO
        )
        op_card = components.Card(content=display_part,
                                  title=components.CardTitleText('控制面板'),
                                  width=self.large_map_width + 50)

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

        ft.Row.__init__(self, controls=[op_card, info_card], vertical_alignment=ft.CrossAxisAlignment.START,
                        spacing=10)

    def handle_after_show(self):
        self.keyboard_hook = keyboard.on_press(self._on_key_press)

    def handle_after_hide(self):
        if self.keyboard_hook is not None:
            keyboard.unhook(self.keyboard_hook)

    def _on_key_press(self, event):
        k = event.name
        if k == 'f8' and self.chosen_route is not None:
            self._do_screenshot()
        if k == 'r' and self.chosen_route is not None:
            self._on_screen_cal_pos_clicked()
        if k == 'q' and self.chosen_route is not None:
            self.cancel_last()
        if k == 'f' and self.chosen_route is not None:
            self._on_screen_patrol_clicked()
        if k == '5' and self.chosen_route is not None:
            self._on_screen_disposable_clicked()

    def _do_screenshot(self, e=None):
        """
        进行具体截图 并将小地图展示出来
        :param e:
        :return:
        """
        if self.sr_ctx.im is None:
            self.sr_ctx.init_image_matcher()

        if self.sr_ctx.controller is None:
            self.sr_ctx.init_controller()
            self.sr_ctx.controller.init()

        screen = self.sr_ctx.controller.screenshot()
        self.mini_map_image = mini_map.cut_mini_map(screen, self.sr_ctx.game_config.mini_map_pos)
        self._show_screenshot_mm()
        self.update_all_component_status()

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

    def _on_cal_pos_clicked(self, e=None) -> bool:
        """
        根据当前截图计算坐标 需要先选择好了路线
        :param e:
        :return: 是否计算成功
        """
        if self.mini_map_image is None or self.chosen_route is None:
            log.info('需要先选定开始点和截图')
            return False
        self.sr_ctx.init_image_matcher()
        mm_info = mini_map.analyse_mini_map(self.mini_map_image, self.sr_ctx.im)

        region, last_pos = self.chosen_route.last_pos
        lm_info = self.sr_ctx.ih.get_large_map(region)
        max_distance = 40

        while True:
            possible_pos = (last_pos.x, last_pos.y, max_distance)
            lm_rect = large_map.get_large_map_rect_by_pos(lm_info.gray.shape, self.mini_map_image.shape[:2], possible_pos)
            pos: MatchResult = cal_pos.cal_character_pos(self.sr_ctx.im, lm_info, mm_info,
                                                         lm_rect=lm_rect,
                                                         retry_without_rect=False, running=False)
            if pos is not None:
                break
            else:
                max_distance += 20
                if max_distance > 100:
                    break

        if pos is None:
            log.info('计算坐标失败')
            return False

        target_pos: Point = pos.center
        self._add_move_op(target_pos.x, target_pos.y, int(self.switch_floor_dropdown.value))
        self.draw_route_and_display()
        return True

    def _on_screen_cal_pos_clicked(self, e=None):
        """
        截图并计算坐标
        :param e:
        :return:
        """
        if self.screen_cal_pos_btn.disabled:
            return
        self._do_screenshot()
        self._on_cal_pos_clicked()

    def _on_screen_patrol_clicked(self, e=None):
        """
        截图并计算坐标 标记为攻击怪物
        :param e:
        :return:
        """
        if self.screen_patrol_btn.disabled:
            return
        self._do_screenshot()
        pos = self._on_cal_pos_clicked()
        if pos:
            self.add_patrol()

    def _on_screen_disposable_clicked(self, e=None):
        """
        截图并计算坐标 标记为可破坏物
        :param e:
        :return:
        """
        if self.screen_disposable_btn.disabled:
            return
        self._do_screenshot()
        pos = self._on_cal_pos_clicked()
        if pos:
            self.add_disposable()

    def on_planet_changed(self, e):
        p: Planet = get_planet_by_cn(self.planet_dropdown.value)

        self.chosen_planet = p

        self.update_region_list_by_planet()
        self.chosen_region = None
        self.floor_dropdown.options = []
        self.switch_floor_dropdown.options = []
        self.tp_dropdown.options = []
        self.chosen_sp = None

        self.chosen_route = None

        self.update_all_component_status()
        self.draw_route_and_display()

    def update_region_list_by_planet(self):
        """
        根据选择星球更新区域列表
        :return:
        """
        r_arr = PLANET_2_REGION[self.chosen_planet.np_id] if self.chosen_planet is not None else []
        self.region_dropdown.options = [ft.dropdown.Option(text=r.cn, key=r.cn) for r in r_arr if r.floor in [0, 1]]

    def on_region_change(self, e):
        self.chosen_region = None

        self.update_floor_list_by_region()
        self.tp_dropdown.options = []
        self.chosen_sp = None

        self.chosen_route = None

        self.update_all_component_status()
        self.draw_route_and_display()

    def update_floor_list_by_region(self):
        r_arr = PLANET_2_REGION[self.chosen_planet.np_id]
        region_name = self.region_dropdown.value
        self.floor_dropdown.options = [ft.dropdown.Option(text=str(r.floor), key=str(r.floor)) for r in r_arr if r.cn == region_name]
        self.switch_floor_dropdown.options = [ft.dropdown.Option(text=str(r.floor), key=str(r.floor)) for r in r_arr if r.cn == region_name]

    def on_floor_changed(self, e):
        region_name = self.region_dropdown.value
        region_floor = int(self.floor_dropdown.value)
        region: Region = get_region_by_cn(region_name, planet=self.chosen_planet, floor=region_floor)
        self.chosen_region = region

        self.switch_floor_dropdown.value = self.floor_dropdown.value

        self.update_sp_list_by_floor()
        self.chosen_sp = None

        self.chosen_route: Optional[WorldPatrolRoute] = None

        self.update_all_component_status()
        self.draw_route_and_display()

    def update_sp_list_by_floor(self):
        sp_arr = REGION_2_SP.get(self.chosen_region.pr_id)
        self.tp_dropdown.options = [ft.dropdown.Option(text=sp.cn, key=sp.cn) for sp in sp_arr if sp.region == self.chosen_region]

    def on_sp_change(self, e):
        sp_arr = REGION_2_SP.get(self.chosen_region.pr_id)
        for sp in sp_arr:
            if sp.region == self.chosen_region and sp.cn == self.tp_dropdown.value:
                self.chosen_sp = sp
                break

        self.switch_floor_dropdown.value = self.floor_dropdown.value

        self.flet_page.update()

        self.new_temp_route()

        self.draw_route_and_display()

    def draw_route_and_display(self):
        if self.chosen_region is None:
            return

        display_image = draw_route_in_image(self.sr_ctx, self.chosen_region, self.chosen_route)

        # 图片转化成base64编码展示
        _, buffer = cv2.imencode('.png', display_image)
        base64_data = base64.b64encode(buffer)
        base64_string = base64_data.decode("utf-8")
        self.map_img.visible = True
        self.map_img.src_base64 = base64_string

        self.route_text.value = '' if self.chosen_route is None else self.chosen_route.route_config_str
        self.update_all_component_status()

    def on_map_click(self, e):
        map_image: MatLike = self.get_original_map_image()
        original_height, original_width = map_image.shape[:2]
        if original_height > original_width:
            scale = self.large_map_width / original_height
        else:
            scale = self.large_map_width / original_width

        x = int(e.local_x / scale)
        y = int(e.local_y / scale)

        if x > original_width or y > original_height:
            return

        self._add_move_op(x, y, int(self.switch_floor_dropdown.value))
        self.draw_route_and_display()

    def _add_move_op(self, x:int , y: int, floor: int):
        """
        在最后添加一个移动的指令
        :return:
        """
        if self.chosen_route is None:
            log.error('未选择路线')
            return
        self.chosen_route.add_move(x, y, floor)

    def get_original_map_image(self) -> MatLike:
        region = get_region_by_cn(self.chosen_region.cn, self.chosen_planet, floor=int(self.switch_floor_dropdown.value))
        return self.sr_ctx.ih.get_large_map(region).origin

    def on_switch_floor(self, e):
        if self.chosen_route is None:
            log.error('未选择路线')
            return
        self.chosen_route.switch_floor(int(self.switch_floor_dropdown.value))
        self.draw_route_and_display()

    def _on_scale_up(self, e):
        """
        放大地图
        :param e:
        :return:
        """
        self.large_map_width += 100
        self.map_container.width = self.large_map_width
        self.map_container.height = self.large_map_width
        self.map_container.update()

    def _on_scale_down(self, e):
        """
        缩小地图
        :param e:
        :return:
        """
        self.large_map_width -= 100
        self.map_container.width = self.large_map_width
        self.map_container.height = self.large_map_width
        self.map_container.update()

    def cancel_last(self, e=None):
        """
        取消最后一个指令
        :param e:
        :return:
        """
        if self.back_btn.disabled:
            return
        if self.chosen_route is None:
            log.error('未选择路线')
            return
        self.chosen_route.pop_last()
        self.draw_route_and_display()

    def cancel_all(self, e):
        """
        取消所有指令
        :param e:
        :return:
        """
        if self.chosen_route is None:
            log.error('未选择路线')
            return
        self.chosen_route.reset()
        self.draw_route_and_display()

    def save_route(self, e):
        if self.chosen_route is None:
            log.error('未选择路线')
            return
        is_new = self.chosen_route.is_new
        self.chosen_route.add_author(self.author_text.value, save=False)
        self.chosen_route.save()

        if is_new:
            self.load_route_id_list()
            self.update_all_component_status()

    def add_patrol(self, e=None):
        if self.chosen_route is None:
            log.error('未选择路线')
            return
        self.chosen_route.add_patrol()
        self.draw_route_and_display()

    def add_disposable(self, e=None):
        """
        增加攻击可破坏物
        :param e:
        :return:
        """
        if self.chosen_route is None:
            log.error('未选择路线')
            return
        self.chosen_route.add_disposable()
        self.draw_route_and_display()

    def _on_route_text_blur(self, e):
        """
        避免使用on_change死循环 只有失去焦点的时候更新
        :param e:
        :return:
        """
        if self.chosen_route is None:
            log.error('未选择路线')
            return
        data = yaml.load(self.route_text.value, Loader=yaml.SafeLoader)
        self.chosen_route.init_from_yaml_data(data)
        self._update_after_chosen_route_changed()

    def _update_after_chosen_route_changed(self):
        """
        选择路线变更后的处理
        :return:
        """
        self.planet_dropdown.value = self.chosen_route.tp.planet.cn
        self.chosen_planet = self.chosen_route.tp.planet

        self.update_region_list_by_planet()
        self.region_dropdown.value = self.chosen_route.tp.region.cn
        self.chosen_region = self.chosen_route.tp.region

        self.update_floor_list_by_region()
        self.floor_dropdown.value = str(self.chosen_route.tp.region.floor)
        self.switch_floor_dropdown.value = str(self.chosen_route.tp.region.floor)

        self.update_sp_list_by_floor()
        self.tp_dropdown.value = self.chosen_route.tp.cn
        self.chosen_sp = self.chosen_route.tp

        self.draw_route_and_display()

    def on_existed_route_changed(self, e):
        """
        加载现有路线 除了路线点外全都不可编辑
        :param e:
        :return:
        """
        chosen_route_id = self.existed_route_id_list[int(self.existed_route_dropdown.value)]
        self.chosen_route = WorldPatrolRoute(chosen_route_id)

        self._update_after_chosen_route_changed()

    def on_cancel_edit_existed(self, e):
        self.chosen_planet = None
        self.chosen_route = None
        self.existed_route_dropdown.value = None

        self.planet_dropdown.value = None
        self.chosen_planet = None
        self.planet_dropdown.disabled = False

        self.region_dropdown.value = None
        self.chosen_region = None

        self.floor_dropdown.value = None

        self.tp_dropdown.value = None
        self.chosen_sp = None

        self.switch_floor_dropdown.value = None

        self.draw_route_and_display()
        self.update_all_component_status()

    def test_existed(self, e):
        if self.test_existed_btn.disabled:
            return
        whitelist: WorldPatrolWhitelist = WorldPatrolWhitelist('0')
        whitelist.type = 'white'
        whitelist.list = [self.chosen_route.route_id.unique_id]
        app = WorldPatrol(self.sr_ctx, ignore_record=True, whitelist=whitelist, team_num=0)
        app.first = self.first_test_route
        app.execute()
        self.first_test_route = False

    def on_interact(self, e):
        if self.chosen_route is None:
            log.error('未选择路线')
            return
        self.chosen_route.add_interact(self.interact_text.value)
        self.draw_route_and_display()

    def on_wait_changed(self, e):
        if self.wait_dropdown.value == sr.const.operation_const.WAIT_TYPE_IN_WORLD:
            self.wait_timeout_text.value = '20'  # 给主界面加一个20秒固定超时时间
        elif self.wait_dropdown.value == sr.const.operation_const.WAIT_TYPE_SECONDS:
            if int(self.wait_timeout_text.value) > 10:  # 等待秒数通常不会太长 默认一个1
                self.wait_timeout_text.value = '1'
        self.flet_page.update()

    def add_wait(self, e):
        if self.chosen_route is None:
            log.error('未选择路线')
            return
        if self.wait_dropdown.value is None or self.wait_timeout_text.value is None:
            log.error('需要先填入等待类型和等待描述', self.flet_page)
            return
        self.chosen_route.add_wait(self.wait_dropdown.value, int(self.wait_timeout_text.value))
        self.draw_route_and_display()

    def on_update_pos(self, e):
        if self.chosen_route is None:
            log.error('未选择路线')
            return
        self.chosen_route.mark_last_as_update()
        self.draw_route_and_display()

    def load_route_id_list(self):
        self.existed_route_id_list = load_all_route_id()
        chosen_value = None
        options = []
        for i in range(len(self.existed_route_id_list)):
            opt = ft.dropdown.Option(text=self.existed_route_id_list[i].display_name, key=str(i))
            options.append(opt)
            if self.chosen_route is not None and self.chosen_route.route_id.unique_id == self.existed_route_id_list[i].unique_id:
                chosen_value = str(i)
        self.existed_route_dropdown.options = options
        self.existed_route_dropdown.value = chosen_value

    def delete_route(self, e):
        if self.chosen_route is None:
            log.error('未选择路线')
            return
        self.chosen_route.delete()
        self.load_route_id_list()
        self.on_cancel_edit_existed(e)

    def update_all_component_status(self):
        """
        统一管理所有组件状态
        :return:
        """
        self.cancel_edit_existed_btn.disabled = self.chosen_route is None
        self.test_existed_btn.disabled = self.chosen_route is None
        self.back_btn.disabled = self.chosen_route is None or self.chosen_route.empty_op
        self.reset_btn.disabled = self.chosen_route is None or self.chosen_route.empty_op
        self.save_btn.disabled = self.chosen_route is None or self.chosen_route.empty_op
        self.delete_btn.disabled = self.chosen_route is None

        self.planet_dropdown.disabled = self.chosen_route is not None
        self.region_dropdown.disabled = self.chosen_route is not None or self.chosen_planet is None
        self.floor_dropdown.disabled = self.region_dropdown.disabled or self.region_dropdown.value is None
        self.tp_dropdown.disabled = self.floor_dropdown.disabled or self.floor_dropdown.value is None

        self.switch_floor_dropdown.disabled = self.chosen_sp is None
        self.patrol_btn.disabled = self.chosen_sp is None
        self.disposable_btn.disabled = self.chosen_sp is None
        self.interact_text.disabled = self.chosen_sp is None
        self.interact_btn.disabled = self.chosen_sp is None
        self.wait_timeout_text.disabled = self.chosen_sp is None
        self.wait_dropdown.disabled = self.chosen_sp is None
        self.add_wait_btn.disabled = self.chosen_sp is None
        self.no_run_btn.disabled = self.chosen_sp is None
        self.update_pos_btn.disabled = self.chosen_sp is None

        self.screenshot_btn.disabled = self.chosen_route is None
        self.cal_pos_btn.disabled = self.chosen_route is None or self.mini_map_image is None
        self.screen_cal_pos_btn.disabled = self.chosen_route is None
        self.screen_patrol_btn.disabled = self.chosen_route is None
        self.screen_disposable_btn.disabled = self.chosen_route is None

        self.flet_page.update()

    def new_temp_route(self):
        """
        新建一条临时路线 未保存
        :return:
        """
        route_id = new_route_id(self.chosen_planet, self.chosen_region, self.chosen_sp)
        self.chosen_route = WorldPatrolRoute(route_id)
        self.chosen_route.add_author(self.author_text.value, save=False)

    def add_no_run(self, e):
        """
        对最后一个
        :param e:
        :return:
        """
        if self.chosen_route is None:
            log.error('未选择路线')
            return
        self.chosen_route.switch_slow_move()
        self.draw_route_and_display()


_world_patrol_draft_route_view: Optional[WorldPatrolDraftRouteView] = None


def get(page: ft.Page, ctx: Context) -> WorldPatrolDraftRouteView:
    global _world_patrol_draft_route_view
    if _world_patrol_draft_route_view is None:
        _world_patrol_draft_route_view = WorldPatrolDraftRouteView(page, ctx)

    return _world_patrol_draft_route_view


def draw_route_in_image(ctx: Context, region: Region, route: WorldPatrolRoute):
    """
    画一个
    :param ctx:
    :param region: 区域
    :param route: 路线 在传送点还没有选的时候 可能为空
    :return:
    """
    last_region = region

    if route is not None:
        last_region, _ = route.last_pos

    display_image = ctx.ih.get_large_map(last_region).origin.copy()

    if route is None:
        return display_image

    last_point = None
    if route.tp is not None:
        last_point = route.tp.tp_pos.tuple()
        cv2.circle(display_image, route.tp.lm_pos.tuple(), 15, color=(100, 255, 100), thickness=2)
        cv2.circle(display_image, route.tp.tp_pos.tuple(), 5, color=(0, 255, 0), thickness=2)
    for route_item in route.route_list:
        if route_item.op in [operation_const.OP_MOVE, operation_const.OP_SLOW_MOVE]:
            pos = route_item.data
            cv2.circle(display_image, pos[:2], 5, color=(0, 0, 255), thickness=-1)
            if last_point is not None:
                cv2.line(display_image, last_point[:2], pos[:2],
                         color=(255, 0, 0) if route_item.op == operation_const.OP_MOVE else (255, 255, 0),
                         thickness=2)
            cv2.putText(display_image, str(route_item.idx), (pos[0] - 5, pos[1] - 13),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1, cv2.LINE_AA)
            last_point = pos
        elif route_item.op == operation_const.OP_PATROL:
            if last_point is not None:
                cv2.circle(display_image, last_point[:2], 10, color=(0, 255, 255), thickness=2)
        elif route_item.op == operation_const.OP_DISPOSABLE:
            if last_point is not None:
                cv2.circle(display_image, last_point[:2], 10, color=(67, 34, 49), thickness=2)
        elif route_item.op == operation_const.OP_INTERACT:
            if last_point is not None:
                cv2.circle(display_image, last_point[:2], 12, color=(255, 0, 255), thickness=2)
        elif route_item.op == operation_const.OP_WAIT:
            if last_point is not None:
                cv2.circle(display_image, last_point[:2], 14, color=(255, 255, 255), thickness=2)
        elif route_item.op == operation_const.OP_UPDATE_POS:
            pos = route_item.data
            cv2.circle(display_image, pos[:2], 5, color=(0, 0, 255), thickness=-1)
            last_point = pos

    return display_image
