import base64
import os
import time
from typing import List

import cv2
import flet as ft
import yaml
from cv2.typing import MatLike
from flet_core import ScrollMode

from basic import config_utils
from basic.img import cv2_utils
from basic.img.os import get_debug_world_patrol_dir
from basic.log_utils import log
from sr.app.world_patrol import load_all_route_id, WorldPatrolRoute, WorldPatrol
from sr.constants.map import Planet, get_planet_by_cn, PLANET_LIST, PLANET_2_REGION, get_region_by_cn, Region, \
    REGION_2_SP, TransportPoint
from sr.context import Context


class WorldPatrolDraftRouteView:

    def __init__(self, page: ft.Page, ctx: Context):
        self.page = page
        self.ctx = ctx

        self.existed_route_dropdown = ft.Dropdown(
            label='编辑已有路线',
            options=[
                ft.dropdown.Option(text=r[12:], key=r) for r in load_all_route_id()
            ],
            on_change=self.on_existed_route_changed
        )
        self.chosen_route_id: str = None
        self.cancel_edit_existed_btn = ft.ElevatedButton(text='取消编辑已有路线', disabled=True, on_click=self.on_cancel_edit_existed)
        self.text_existed_btn = ft.ElevatedButton(text='测试选择线路', disabled=True, on_click=self.on_test_existed)
        self.back_btn = ft.ElevatedButton(text='后退', disabled=True, on_click=self.cancel_last)
        self.reset_btn = ft.ElevatedButton(text='重置', disabled=True, on_click=self.cancel_all)
        self.save_btn = ft.ElevatedButton(text='保存', disabled=True, on_click=self.save_route)
        load_existed_row = ft.Row(spacing=10, controls=[
            self.existed_route_dropdown,
            self.cancel_edit_existed_btn,
            self.text_existed_btn,
            self.back_btn, self.reset_btn, self.save_btn
        ])

        self.planet_dropdown = ft.Dropdown(
            label='星球',
            width=200,
            options=[
                ft.dropdown.Option(text=p.cn, key=p.cn) for p in PLANET_LIST
            ],
            on_change=self.on_planet_changed
        )
        self.region_dropdown = ft.Dropdown(label='区域', width=200, on_change=self.on_region_change)
        self.level_dropdown = ft.Dropdown(label='层数', width=200, on_change=self.on_level_changed)
        self.tp_dropdown = ft.Dropdown(label='传送点', width=200, on_change=self.on_sp_change)

        choose_row = ft.Row(
            spacing=10,
            controls=[self.planet_dropdown, self.region_dropdown, self.level_dropdown, self.tp_dropdown]
        )

        self.switch_level = ft.Dropdown(label='路线中切换层数', width=200, on_change=self.on_switch_level)
        self.patrol_btn = ft.ElevatedButton(text='攻击怪物', disabled=True, on_click=self.add_patrol)
        self.interact_text = ft.TextField(label="交互文本", width=200, disabled=True)
        self.interact_btn = ft.ElevatedButton(text='交互', disabled=True, on_click=self.on_interact)
        self.update_pos_btn = ft.ElevatedButton(text='不移动更新坐标', disabled=True, on_click=self.on_update_pos)
        self.wait_dropdown = ft.Dropdown(
            label='等待', width=200,
            options=[
                ft.dropdown.Option(text='主界面', key='in_world')
            ],
            on_change=self.on_wait_changed
        )

        ctrl_row = ft.Row(
            spacing=10,
            controls=[self.switch_level, self.patrol_btn, self.interact_text, self.interact_btn, self.wait_dropdown, self.update_pos_btn]
        )

        self.image_width = 1000
        self.map_img = ft.Image(src="a.png", fit=ft.ImageFit.CONTAIN, error_content=ft.Text('等待选择区域'), visible=False)

        display_part = ft.Column(
            controls=[
                ft.Container(content=load_existed_row, padding=20),
                ft.Container(content=choose_row, padding=20),
                ft.Container(content=ctrl_row, padding=20),
                ft.Container(content=self.map_img, width=self.image_width, height=self.image_width,
                             on_click=self.on_map_click,
                             alignment=ft.alignment.top_left)
            ],
            scroll=ScrollMode.AUTO
        )
        self.route_text = ft.TextField(label="路线配置", multiline=True, min_lines=10, max_lines=100, on_blur=self.on_route_text_blur)

        self.component = ft.Row(
            controls=[
                ft.Container(content=display_part),
                ft.VerticalDivider(width=1),
                ft.Container(content=self.route_text, alignment=ft.alignment.top_center),
            ]
        )

        self.route_list: List = []
        self.chosen_planet: Planet = None
        self.chosen_region: Region = None
        self.chosen_sp: TransportPoint = None

    def on_planet_changed(self, e):
        p: Planet = get_planet_by_cn(self.planet_dropdown.value)

        self.chosen_planet = p

        self.update_region_list_by_planet()
        self.region_dropdown.disabled = False
        self.chosen_region = None

        self.level_dropdown.disabled = True
        self.level_dropdown.options = []

        self.switch_level.disabled = True
        self.switch_level.options = []

        self.tp_dropdown.disabled = True
        self.tp_dropdown.options = []
        self.chosen_sp = None

        self.page.update()

        self.route_list = []
        self.draw_route_and_display()

    def update_region_list_by_planet(self):
        """
        根据选择星球更新区域列表
        :return:
        """
        r_arr = PLANET_2_REGION[self.chosen_planet.id] if self.chosen_planet is not None else []
        self.region_dropdown.options = [ft.dropdown.Option(text=r.cn, key=r.cn) for r in r_arr if r.level in [0, 1]]

    def on_region_change(self, e):
        self.chosen_region = None

        self.update_level_list_by_region()
        self.level_dropdown.disabled = False
        self.switch_level.disabled = False

        self.tp_dropdown.disabled = True
        self.tp_dropdown.options = []
        self.chosen_sp = None

        self.page.update()

        self.route_list = []
        self.draw_route_and_display()

    def update_level_list_by_region(self):
        r_arr = PLANET_2_REGION[self.chosen_planet.id]
        region_name = self.region_dropdown.value
        self.level_dropdown.options = [ft.dropdown.Option(text=str(r.level), key=str(r.level)) for r in r_arr if r.cn == region_name]
        self.switch_level.options = [ft.dropdown.Option(text=str(r.level), key=str(r.level)) for r in r_arr if r.cn == region_name]

    def on_level_changed(self, e):
        region_name = self.region_dropdown.value
        region_level = int(self.level_dropdown.value)
        region: Region = get_region_by_cn(region_name, planet=self.chosen_planet, level=region_level)
        self.chosen_region = region

        self.switch_level.value = self.level_dropdown.value

        self.update_sp_list_by_level()
        self.tp_dropdown.disabled = False
        self.chosen_sp = None

        self.page.update()

        self.route_list = []
        self.draw_route_and_display()

    def update_sp_list_by_level(self):
        sp_arr = REGION_2_SP.get(self.chosen_region.get_pr_id())
        self.tp_dropdown.options = [ft.dropdown.Option(text=sp.cn, key=sp.cn) for sp in sp_arr if sp.region == self.chosen_region]


    def on_sp_change(self, e):
        sp_arr = REGION_2_SP.get(self.chosen_region.get_pr_id())
        for sp in sp_arr:
            if sp.region == self.chosen_region and sp.cn == self.tp_dropdown.value:
                self.chosen_sp = sp
                break

        self.switch_level.value = self.level_dropdown.value

        self.page.update()

        self.route_list = []
        self.draw_route_and_display()

    def draw_route_and_display(self):
        if self.chosen_region is None:
            self.map_img.visible = False
            self.patrol_btn.disabled = True
            self.interact_text.disabled = True
            self.interact_btn.disabled = True
            self.wait_dropdown.disabled = True
            self.update_pos_btn.disabled = True
            self.back_btn.disabled = True
            self.reset_btn.disabled = True
            self.save_btn.disabled = True
            self.page.update()
            return

        map_image: MatLike = self.get_original_map_image()
        display_image = map_image.copy()

        last_point = None
        if self.chosen_sp is not None:
            last_point = self.chosen_sp.lm_pos
            cv2.circle(display_image, last_point[:2], 25, color=(0, 255, 0), thickness=3)
        for route_item in self.route_list:
            if route_item['op'] == 'move':
                pos = route_item['data']
                cv2.circle(display_image, pos[:2], 5, color=(0, 0, 255), thickness=-1)
                if last_point is not None:
                    cv2.line(display_image, last_point[:2], pos[:2], color=(255, 0, 0), thickness=2)
                last_point = pos
            elif route_item['op'] == 'patrol':
                if last_point is not None:
                    cv2.circle(display_image, last_point[:2], 10, color=(0, 255, 255), thickness=2)
            elif route_item['op'] == 'interact':
                if last_point is not None:
                    cv2.circle(display_image, last_point[:2], 12, color=(255, 0, 255), thickness=2)
            elif route_item['op'] == 'wait':
                if last_point is not None:
                    cv2.circle(display_image, last_point[:2], 14, color=(255, 255, 255), thickness=2)
            elif route_item['op'] == 'update_pos':
                pos = route_item['data']
                cv2.circle(display_image, pos[:2], 5, color=(0, 0, 255), thickness=-1)
                last_point = pos

        cv2_utils.show_image(display_image)

        # 图片转化成base64编码展示
        _, buffer = cv2.imencode('.png', display_image)
        base64_data = base64.b64encode(buffer)
        base64_string = base64_data.decode("utf-8")
        self.map_img.visible = True
        self.map_img.src_base64 = base64_string

        self.patrol_btn.disabled = False
        self.interact_text.disabled = False
        self.interact_btn.disabled = False
        self.wait_dropdown.disabled = False
        self.wait_dropdown.value = None
        self.update_pos_btn.disabled = False
        self.back_btn.disabled = len(self.route_list) == 0
        self.reset_btn.disabled = len(self.route_list) == 0
        self.save_btn.disabled = len(self.route_list) == 0
        self.route_text.value = self.get_route_config_str()

        self.page.update()

    def on_map_click(self, e):
        map_image: MatLike = self.get_original_map_image()
        original_height, original_width = map_image.shape[:2]
        if original_height > original_width:
            scale = self.image_width / original_height
        else:
            scale = self.image_width / original_width

        x = int(e.local_x / scale)
        y = int(e.local_y / scale)

        self.route_list.append({'op': 'move', 'data': (x, y, int(self.switch_level.value))})
        self.draw_route_and_display()

    def get_original_map_image(self) -> MatLike:
        region = get_region_by_cn(self.chosen_region.cn, self.chosen_planet, level=int(self.switch_level.value))
        return self.ctx.ih.get_large_map(region).origin

    def on_switch_level(self, e):
        self.draw_route_and_display()

    def cancel_last(self, e):
        self.route_list.pop()
        self.draw_route_and_display()

    def cancel_all(self, e):
        self.route_list = []
        self.draw_route_and_display()

    def get_route_config_str(self) -> str:
        cfg: str = ''
        if self.chosen_sp is None:
            return
        last_level = int(self.level_dropdown.value)
        cfg += "planet: '%s'\n" % self.chosen_planet.cn
        cfg += "region: '%s'\n" % self.chosen_region.cn
        cfg += "level: %d\n" % last_level
        cfg += "tp: '%s'\n" % self.chosen_sp.cn
        cfg += "route:\n"
        for route_item in self.route_list:
            if route_item['op'] == 'move':
                cfg += "  - op: 'move'\n"
                pos = route_item['data']
                if pos[2] != last_level:
                    cfg += "    data: [%d, %d, %d]\n" % (pos[0], pos[1], pos[2])
                else:
                    cfg += "    data: [%d, %d]\n" % (pos[0], pos[1])
                last_level = pos[2]
            elif route_item['op'] == 'patrol':
                cfg += "  - op: 'patrol'\n"
            elif route_item['op'] == 'interact':
                cfg += "  - op: 'interact'\n"
                cfg += "    data: '%s'\n" % route_item['data']
            elif route_item['op'] == 'wait':
                cfg += "  - op: 'wait'\n"
                cfg += "    data: '%s'\n" % route_item['data']
            elif route_item['op'] == 'update_pos':
                cfg += "  - op: 'update_pos'\n"
                pos = route_item['data']
                if pos[2] != last_level:
                    cfg += "    data: [%d, %d, %d]\n" % (pos[0], pos[1], pos[2])
                else:
                    cfg += "    data: [%d, %d]\n" % (pos[0], pos[1])
        return cfg

    def save_route(self, e):
        if self.chosen_route_id is None:
            dir_path = get_debug_world_patrol_dir()
            file_path = os.path.join(dir_path, "%s_%s_%s.yml" % (self.chosen_planet.cn ,self.chosen_region.cn, self.chosen_sp.cn))
        else:
            file_path = config_utils.get_config_file_path(self.chosen_route_id, sub_dir='world_patrol')
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(self.route_text.value)
        log.info('保存成功 %s', file_path)

    def add_patrol(self, e):
        self.route_list.append({'op': 'patrol'})
        self.draw_route_and_display()

    def on_route_text_blur(self, e):
        """
        避免使用on_change死循环 只有失去焦点的时候更新
        :param e:
        :return:
        """
        data = yaml.load(self.route_text.value, Loader=yaml.SafeLoader)
        self.route_list = data['route']
        self.init_route_list_from_outer_data()
        self.draw_route_and_display()

    def init_route_list_from_outer_data(self):
        """
        当路线是从外部文件加载或编辑框过来时 稍微处理一下格式
        :return:
        """
        last_level = int(self.level_dropdown.value)
        for route_item in self.route_list:
            if route_item['op'] == 'move' or route_item['op'] == 'update_pos':
                if len(route_item['data']) == 2:
                    route_item['data'].append(last_level)
                else:
                    last_level = route_item['data'][2]

    def on_existed_route_changed(self, e):
        """
        加载现有路线 除了路线点外全都不可编辑
        :param e:
        :return:
        """
        self.chosen_route_id = self.existed_route_dropdown.value
        route = WorldPatrolRoute(self.chosen_route_id)
        self.cancel_edit_existed_btn.disabled = False
        self.text_existed_btn.disabled = False

        self.planet_dropdown.value = route.tp.planet.cn
        self.planet_dropdown.disabled = True
        self.chosen_planet = route.tp.planet

        self.update_region_list_by_planet()
        self.region_dropdown.value = route.tp.region.cn
        self.region_dropdown.disabled = True
        self.chosen_region = route.tp.region

        self.update_level_list_by_region()
        self.level_dropdown.value = str(route.tp.region.level)
        self.level_dropdown.disabled = True
        self.switch_level.value = str(route.tp.region.level)
        self.switch_level.disabled = False

        self.update_sp_list_by_level()
        self.tp_dropdown.value = route.tp.cn
        self.tp_dropdown.disabled = True
        self.chosen_sp = route.tp

        self.route_list = route.route_list
        self.init_route_list_from_outer_data()
        self.draw_route_and_display()

    def on_cancel_edit_existed(self, e):
        self.cancel_edit_existed_btn.disabled = True
        self.text_existed_btn.disabled = True
        self.chosen_route_id = None
        self.existed_route_dropdown.value = None

        self.planet_dropdown.value = None
        self.chosen_planet = None
        self.planet_dropdown.disabled = False

        self.region_dropdown.value = None
        self.chosen_region = None
        self.region_dropdown.disabled = True

        self.level_dropdown.value = None
        self.level_dropdown.disabled = True

        self.tp_dropdown.value = None
        self.chosen_sp = None
        self.tp_dropdown.disabled = True

        self.switch_level.value = None

        self.route_list = []
        self.draw_route_and_display()

    def on_test_existed(self, e):
        app = WorldPatrol(self.ctx, restart=True, route_id_list=[self.chosen_route_id])
        app.first = False
        app.execute()

    def on_interact(self, e):
        self.route_list.append({'op': 'interact', 'data': self.interact_text.value})
        self.draw_route_and_display()

    def on_wait_changed(self, e):
        self.route_list.append({'op': 'wait', 'data': self.wait_dropdown.value})
        self.draw_route_and_display()

    def on_update_pos(self, e):
        idx = len(self.route_list) - 1
        print(self.route_list[idx])
        if self.route_list[idx]['op'] == 'move':
            self.route_list[idx]['op'] = 'update_pos'
        self.draw_route_and_display()


gv: WorldPatrolDraftRouteView = None


def get(page: ft.Page, ctx: Context) -> WorldPatrolDraftRouteView:
    global gv
    if gv is None:
        gv = WorldPatrolDraftRouteView(page, ctx)

    return gv
