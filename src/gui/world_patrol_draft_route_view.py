import base64
import os
import time
from typing import List

import cv2
import flet as ft
from cv2.typing import MatLike
from flet_core import ScrollMode

from basic.img import cv2_utils
from basic.img.os import get_debug_world_patrol_dir
from basic.log_utils import log
from sr import constants, image
from sr.constants.map import Planet, get_planet_by_cn, PLANET_LIST, PLANET_2_REGION, get_region_by_cn, Region, \
    REGION_2_SP, TransportPoint
from sr.context import Context


class WorldPatrolDraftRouteView:

    def __init__(self, page: ft.Page, ctx: Context):
        self.page = page
        self.ctx = ctx

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
        self.back_btn = ft.ElevatedButton(text='后退', disabled=True, on_click=self.cancel_last)
        self.reset_btn = ft.ElevatedButton(text='重置', disabled=True, on_click=self.cancel_all)
        self.save_btn = ft.ElevatedButton(text='保存', disabled=True, on_click=self.save_route)
        ctrl_row = ft.Row(
            spacing=10,
            controls=[self.switch_level, self.back_btn, self.reset_btn, self.save_btn]
        )

        self.map_img = ft.Image(src="a.png", fit=ft.ImageFit.CONTAIN, error_content=ft.Text('等待选择区域'), visible=False)

        self.component = ft.Column(
            controls=[
                ft.Container(content=choose_row, padding=20),
                ft.Container(content=ctrl_row, padding=20),
                ft.Container(content=self.map_img, width=800, height=800, on_click=self.on_map_click,
                             alignment=ft.alignment.top_left)
            ],
            scroll=ScrollMode.AUTO
        )

        self.route_list: List = []
        self.chosen_planet: Planet = None
        self.chosen_region: Region = None
        self.chosen_sp: TransportPoint = None

    def on_planet_changed(self, e):
        p: Planet = get_planet_by_cn(self.planet_dropdown.value)
        r_arr = PLANET_2_REGION[p.id]
        self.chosen_planet = p

        self.region_dropdown.options = [ft.dropdown.Option(text=r.cn, key=r.cn) for r in r_arr if r.level in [0, 1]]
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

    def on_region_change(self, e):
        region_name = self.region_dropdown.value
        self.chosen_region = None

        r_arr = PLANET_2_REGION[self.chosen_planet.id]

        self.level_dropdown.disabled = False
        self.level_dropdown.options = [ft.dropdown.Option(text=str(r.level), key=str(r.level)) for r in r_arr if r.cn == region_name]

        self.switch_level.disabled = False
        self.switch_level.options = [ft.dropdown.Option(text=str(r.level), key=str(r.level)) for r in r_arr if r.cn == region_name]

        self.tp_dropdown.disabled = True
        self.tp_dropdown.options = []
        self.chosen_sp = None

        self.page.update()

        self.route_list = []
        self.draw_route_and_display()

    def on_level_changed(self, e):
        region_name = self.region_dropdown.value
        region_level = int(self.level_dropdown.value)
        region: Region = get_region_by_cn(region_name, planet=self.chosen_planet, level=region_level)
        sp_arr = REGION_2_SP.get(region.get_pr_id())
        self.chosen_region = region

        self.switch_level.value = self.level_dropdown.value

        self.tp_dropdown.disabled = False
        self.tp_dropdown.options = [ft.dropdown.Option(text=sp.cn, key=sp.cn) for sp in sp_arr if sp.region == region]
        self.chosen_sp = None

        self.page.update()

        self.route_list = []
        self.draw_route_and_display()

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
        for i in self.route_list:
            cv2.circle(display_image, i[:2], 5, color=(0, 0, 255), thickness=-1)
            if last_point is not None:
                cv2.line(display_image, last_point[:2], i[:2], color=(255, 0, 0), thickness=2)
            last_point = i

        cv2_utils.show_image(display_image)

        # 图片转化成base64编码展示
        _, buffer = cv2.imencode('.png', display_image)
        base64_data = base64.b64encode(buffer)
        base64_string = base64_data.decode("utf-8")
        self.map_img.visible = True
        self.map_img.src_base64 = base64_string

        self.back_btn.disabled = len(self.route_list) == 0
        self.reset_btn.disabled = len(self.route_list) == 0
        self.save_btn.disabled = len(self.route_list) == 0

        self.page.update()

    def on_map_click(self, e):
        map_image: MatLike = self.get_original_map_image()
        original_height, original_width = map_image.shape[:2]
        if original_height > original_width:
            scale = 800 / original_height
        else:
            scale = 800 / original_width

        x = int(e.local_x / scale)
        y = int(e.local_y / scale)

        self.route_list.append((x, y, int(self.switch_level.value)))
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

    def save_route(self, e):
        dir_path = get_debug_world_patrol_dir()
        file_path = os.path.join(dir_path, "%d.yml" % round(time.time() * 1000))
        with open(file_path, "w", encoding="utf-8") as file:
            last_level = int(self.level_dropdown.value)
            file.write("planet: '%s'\n" % self.chosen_planet.cn)
            file.write("region: '%s'\n" % self.chosen_region.cn)
            file.write("level: %d\n" % last_level)
            file.write("tp: '%s'\n" % self.chosen_sp.cn)
            file.write("route:\n")
            for pos in self.route_list:
                file.write("  - op: 'move'\n")
                if pos[2] != last_level:
                    file.write("    data: [%d, %d, %d]\n" % (pos[0], pos[1], pos[2]))
                else:
                    file.write("    data: [%d, %d]\n" % (pos[0], pos[1]))
                last_level = pos[2]
            file.write("  - op: 'patrol'\n")
        log.info('保存成功')


gv: WorldPatrolDraftRouteView = None


def get(page: ft.Page, ctx: Context) -> WorldPatrolDraftRouteView:
    global gv
    if gv is None:
        gv = WorldPatrolDraftRouteView(page, ctx)

    return gv
