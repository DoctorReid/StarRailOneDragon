import base64
import os
from typing import List

import cv2
import flet as ft
import yaml
from cv2.typing import MatLike
from flet_core import ScrollMode

from basic import os_utils
from basic.log_utils import log
from sr.app.world_patrol import load_all_route_id, WorldPatrolRoute, WorldPatrol, WorldPatrolRouteId, \
    WorldPatrolWhitelist
from sr.const import map_const, route_const
from sr.const.map_const import Planet, get_planet_by_cn, PLANET_LIST, PLANET_2_REGION, get_region_by_cn, Region, \
    REGION_2_SP, TransportPoint, region_with_another_floor
from sr.context import Context


class WorldPatrolDraftRouteView:

    def __init__(self, page: ft.Page, ctx: Context):
        self.page = page
        self.ctx = ctx

        self.author_text = ft.TextField(label='作者署名', width=200, value='DoctorReid')
        author_row = ft.Row(spacing=10, controls=[
            self.author_text,
            ft.Text(value='留下您的大名可以让大家知道您的贡献，匿名提供也替大家谢谢您')
            ])

        self.route_id_list: List[WorldPatrolRouteId] = None
        self.existed_route_dropdown = ft.Dropdown(
            label='编辑已有路线',
            on_change=self.on_existed_route_changed
        )
        self.chosen_route_id: WorldPatrolRouteId = None
        self.load_route_id_list()
        self.cancel_edit_existed_btn = ft.ElevatedButton(text='取消编辑已有路线', disabled=True, on_click=self.on_cancel_edit_existed)
        self.test_existed_btn = ft.ElevatedButton(text='测试选择线路', disabled=True, on_click=self.on_test_existed)
        self.back_btn = ft.ElevatedButton(text='后退', disabled=True, on_click=self.cancel_last)
        self.reset_btn = ft.ElevatedButton(text='重置', disabled=True, on_click=self.cancel_all)
        self.save_btn = ft.ElevatedButton(text='保存', disabled=True, on_click=self.save_route)
        self.delete_btn = ft.ElevatedButton(text='删除', disabled=True, on_click=self.delete_route)
        load_existed_row = ft.Row(spacing=10, controls=[
            self.existed_route_dropdown,
            self.cancel_edit_existed_btn,
            self.test_existed_btn,
            self.back_btn, self.reset_btn, self.save_btn, self.delete_btn
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
        self.floor_dropdown = ft.Dropdown(label='层数', width=200, on_change=self.on_floor_changed)
        self.tp_dropdown = ft.Dropdown(label='传送点', width=200, on_change=self.on_sp_change)

        choose_row = ft.Row(
            spacing=10,
            controls=[self.planet_dropdown, self.region_dropdown, self.floor_dropdown, self.tp_dropdown]
        )

        self.switch_floor_dropdown = ft.Dropdown(label='中途切换层数', width=150, on_change=self.on_switch_floor)
        self.patrol_btn = ft.ElevatedButton(text='攻击怪物', disabled=True, on_click=self.add_patrol)
        self.interact_text = ft.TextField(label="交互文本", width=150, disabled=True)
        self.interact_btn = ft.ElevatedButton(text='交互', disabled=True, on_click=self.on_interact)
        self.update_pos_btn = ft.ElevatedButton(text='不移动更新坐标', disabled=True, on_click=self.on_update_pos)
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
        self.add_wait_btn = ft.ElevatedButton(text='等待', disabled=True, on_click=self.add_wait)

        ctrl_row = ft.Row(
            spacing=10,
            controls=[self.switch_floor_dropdown, self.patrol_btn, self.interact_text, self.interact_btn, self.wait_timeout_text, self.wait_dropdown, self.add_wait_btn, self.update_pos_btn]
        )

        self.image_width = 1000
        self.map_img = ft.Image(src="a.png", fit=ft.ImageFit.CONTAIN, error_content=ft.Text('等待选择区域'), visible=False)

        display_part = ft.Column(
            controls=[
                ft.Container(content=author_row, padding=20),
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

        self.author_list: List[str] = [self.author_text.value]
        self.route_list: List = []
        self.chosen_planet: Planet = None
        self.chosen_region: Region = None
        self.chosen_sp: TransportPoint = None

    def on_planet_changed(self, e):
        p: Planet = get_planet_by_cn(self.planet_dropdown.value)

        self.chosen_planet = p

        self.update_region_list_by_planet()
        self.chosen_region = None
        self.floor_dropdown.options = []
        self.switch_floor_dropdown.options = []
        self.tp_dropdown.options = []
        self.chosen_sp = None

        self.chosen_route_id = None
        self.route_list = []

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

        self.chosen_route_id = None
        self.route_list = []

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

        self.chosen_route_id = None
        self.route_list = []

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

        self.page.update()

        self.chosen_route_id = None
        self.route_list = []
        self.draw_route_and_display()

    def draw_route_and_display(self):
        if self.chosen_region is None:
            return

        route = self.mock_temp_route(self.chosen_route_id)
        display_image = draw_route_in_image(self.ctx, route, route.route_id)

        # 图片转化成base64编码展示
        _, buffer = cv2.imencode('.png', display_image)
        base64_data = base64.b64encode(buffer)
        base64_string = base64_data.decode("utf-8")
        self.map_img.visible = True
        self.map_img.src_base64 = base64_string

        self.route_text.value = self.get_route_config_str()
        self.update_all_component_status()

    def on_map_click(self, e):
        map_image: MatLike = self.get_original_map_image()
        original_height, original_width = map_image.shape[:2]
        if original_height > original_width:
            scale = self.image_width / original_height
        else:
            scale = self.image_width / original_width

        x = int(e.local_x / scale)
        y = int(e.local_y / scale)

        if x > original_width or y > original_height:
            return

        self.route_list.append({'op': 'move', 'data': (x, y, int(self.switch_floor_dropdown.value))})
        self.draw_route_and_display()

    def get_original_map_image(self) -> MatLike:
        region = get_region_by_cn(self.chosen_region.cn, self.chosen_planet, floor=int(self.switch_floor_dropdown.value))
        return self.ctx.ih.get_large_map(region).origin

    def on_switch_floor(self, e):
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
        last_floor = int(self.floor_dropdown.value)
        display_auth_list = self.author_list.copy()
        if self.author_text.value not in display_auth_list:
            display_auth_list.append(self.author_text.value)
        cfg += "author: %s\n" % display_auth_list
        cfg += "planet: '%s'\n" % self.chosen_planet.cn
        cfg += "region: '%s'\n" % self.chosen_region.cn
        cfg += "floor: %d\n" % last_floor
        cfg += "tp: '%s'\n" % self.chosen_sp.cn
        cfg += "route:\n"
        for route_item in self.route_list:
            if route_item['op'] == 'move':
                cfg += "  - op: 'move'\n"
                pos = route_item['data']
                if pos[2] != last_floor:
                    cfg += "    data: [%d, %d, %d]\n" % (pos[0], pos[1], pos[2])
                else:
                    cfg += "    data: [%d, %d]\n" % (pos[0], pos[1])
                last_floor = pos[2]
            elif route_item['op'] == 'patrol':
                cfg += "  - op: 'patrol'\n"
            elif route_item['op'] == 'interact':
                cfg += "  - op: 'interact'\n"
                cfg += "    data: '%s'\n" % route_item['data']
            elif route_item['op'] == 'wait':
                cfg += "  - op: 'wait'\n"
                cfg += "    data: ['%s', '%d']\n" % (route_item['data'][0], route_item['data'][1])
            elif route_item['op'] == 'update_pos':
                cfg += "  - op: 'update_pos'\n"
                pos = route_item['data']
                if pos[2] != last_floor:
                    cfg += "    data: [%d, %d, %d]\n" % (pos[0], pos[1], pos[2])
                else:
                    cfg += "    data: [%d, %d]\n" % (pos[0], pos[1])
                last_floor = pos[2]
        return cfg

    def save_route(self, e):
        new_save: bool = self.chosen_route_id is None
        if new_save:
            same_region_cnt: int = 0
            same_tp_cnt: int = 0
            dir_path = os_utils.get_path_under_work_dir('config', 'world_patrol', self.chosen_planet.np_id)
            for filename in os.listdir(dir_path):
                idx = filename.find('.yml')
                if idx == -1:
                    continue
                if not filename.startswith(self.chosen_region.r_id):
                    continue
                same_region_cnt += 1
                tp_suffix = filename[len(self.chosen_region.r_id) + 5:idx]
                if not tp_suffix.startswith(self.chosen_sp.id):
                    continue
                same_tp_cnt += 1

            raw_id = '%s_R%02d_%s' % (self.chosen_region.r_id, same_region_cnt + 1, self.chosen_sp.id) + ('' if same_tp_cnt == 0 else '_%d' % (same_tp_cnt + 1))
            self.chosen_route_id = WorldPatrolRouteId(self.chosen_planet, raw_id)

        with open(self.chosen_route_id.file_path, "w", encoding="utf-8") as file:
            file.write(self.route_text.value)
        log.info('保存成功 %s', self.chosen_route_id.file_path)

        if new_save:
            self.load_route_id_list()
            self.update_all_component_status()

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
        last_floor = int(self.floor_dropdown.value)
        for route_item in self.route_list:
            if route_item['op'] == 'move' or route_item['op'] == 'update_pos':
                if len(route_item['data']) == 2:
                    route_item['data'].append(last_floor)
                else:
                    last_floor = route_item['data'][2]
        self.switch_floor_dropdown.value = str(last_floor)

    def on_existed_route_changed(self, e):
        """
        加载现有路线 除了路线点外全都不可编辑
        :param e:
        :return:
        """
        self.chosen_route_id = self.route_id_list[int(self.existed_route_dropdown.value)]
        route = WorldPatrolRoute(self.chosen_route_id)

        self.planet_dropdown.value = route.tp.planet.cn
        self.chosen_planet = route.tp.planet

        self.update_region_list_by_planet()
        self.region_dropdown.value = route.tp.region.cn
        self.chosen_region = route.tp.region

        self.update_floor_list_by_region()
        self.floor_dropdown.value = str(route.tp.region.floor)
        self.switch_floor_dropdown.value = str(route.tp.region.floor)

        self.update_sp_list_by_floor()
        self.tp_dropdown.value = route.tp.cn
        self.chosen_sp = route.tp

        self.author_list = route.author_list
        self.route_list = route.route_list
        self.init_route_list_from_outer_data()
        self.draw_route_and_display()

    def on_cancel_edit_existed(self, e):
        self.chosen_planet = None
        self.chosen_route_id = None
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

        self.route_list = []
        self.draw_route_and_display()
        self.update_all_component_status()

    def on_test_existed(self, e):
        whitelist: WorldPatrolWhitelist = WorldPatrolWhitelist('0')
        whitelist.type = 'white'
        whitelist.list = [self.chosen_route_id.unique_id]
        app = WorldPatrol(self.ctx, restart=True, whitelist=whitelist)
        app.first = False
        app.execute()

    def on_interact(self, e):
        self.route_list.append({'op': 'interact', 'data': self.interact_text.value})
        self.draw_route_and_display()

    def on_wait_changed(self, e):
        if self.wait_dropdown.value == route_const.WAIT_IN_WORLD:
            self.wait_timeout_text.value = '20'  # 给主界面加一个20秒固定超时时间
        elif self.wait_dropdown.value == route_const.WAIT_SECONDS:
            if int(self.wait_timeout_text.value) > 10:  # 等待秒数通常不会太长 默认一个1
                self.wait_timeout_text.value = '1'
        self.page.update()

    def add_wait(self, e):
        self.route_list.append({'op': 'wait', 'data': [self.wait_dropdown.value, int(self.wait_timeout_text.value)]})
        self.draw_route_and_display()

    def on_update_pos(self, e):
        idx = len(self.route_list) - 1
        print(self.route_list[idx])
        if self.route_list[idx]['op'] == 'move':
            self.route_list[idx]['op'] = 'update_pos'
        self.draw_route_and_display()

    def load_route_id_list(self):
        self.route_id_list = load_all_route_id()
        chosen_value = None
        options = []
        for i in range(len(self.route_id_list)):
            opt = ft.dropdown.Option(text=self.route_id_list[i].display_name, key=str(i))
            options.append(opt)
            if self.chosen_route_id is not None and self.chosen_route_id.equals(self.route_id_list[i]):
                chosen_value = str(i)
        self.existed_route_dropdown.options = options
        self.existed_route_dropdown.value = chosen_value

    def delete_route(self, e):
        os.remove(self.chosen_route_id.file_path)
        self.load_route_id_list()
        self.on_cancel_edit_existed(e)

    def update_all_component_status(self):
        """
        统一管理所有组件状态
        :return:
        """
        self.cancel_edit_existed_btn.disabled = self.chosen_route_id is None
        self.test_existed_btn.disabled = self.chosen_route_id is None
        self.back_btn.disabled = len(self.route_list) == 0
        self.reset_btn.disabled = len(self.route_list) == 0
        self.save_btn.disabled = len(self.route_list) == 0
        self.delete_btn.disabled = self.chosen_route_id is None

        self.planet_dropdown.disabled = self.chosen_route_id is not None
        self.region_dropdown.disabled = self.chosen_route_id is not None or self.chosen_planet is None
        self.floor_dropdown.disabled = self.region_dropdown.disabled or self.region_dropdown.value is None
        self.tp_dropdown.disabled = self.floor_dropdown.disabled or self.floor_dropdown.value is None

        self.switch_floor_dropdown.disabled = self.chosen_sp is None
        self.patrol_btn.disabled = self.chosen_sp is None
        self.interact_text.disabled = self.chosen_sp is None
        self.interact_btn.disabled = self.chosen_sp is None
        self.wait_timeout_text.disabled = self.chosen_sp is None
        self.wait_dropdown.disabled = self.chosen_sp is None
        self.add_wait_btn.disabled = self.chosen_sp is None
        self.update_pos_btn.disabled = self.chosen_sp is None

        self.page.update()

    def mock_temp_route(self, route_id: WorldPatrolRouteId=None) -> WorldPatrolRoute:
        if route_id is None:
            route_id = WorldPatrolRouteId(map_const.P01, 'R02_JZCD_R01_JKS')
        route = WorldPatrolRoute(route_id)

        route_id.planet = self.chosen_planet
        route_id.region = self.chosen_region
        route_id.tp = self.chosen_sp

        route.tp = self.chosen_sp
        route.route_list = self.route_list

        return route


gv: WorldPatrolDraftRouteView = None


def get(page: ft.Page, ctx: Context) -> WorldPatrolDraftRouteView:
    global gv
    if gv is None:
        gv = WorldPatrolDraftRouteView(page, ctx)

    return gv


def draw_route_in_image(ctx: Context, route: WorldPatrolRoute, route_id: WorldPatrolRouteId = None):
    """
    画一个
    :param ctx:
    :param route:
    :param route_id: 新建路线时候传入
    :return:
    """
    last_region = route_id.region if route_id is not None else route.tp.region
    for route_item in route.route_list:
        if route_item['op'] == 'move' or route_item['op'] == 'update_pos':
            pos = route_item['data']
            if len(pos) > 2:
                last_region = region_with_another_floor(last_region, pos[2])

    display_image = ctx.ih.get_large_map(last_region).origin.copy()

    last_point = None
    if route.tp is not None:
        last_point = route.tp.lm_pos
        cv2.circle(display_image, last_point[:2], 25, color=(0, 255, 0), thickness=3)
    for route_item in route.route_list:
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

    return display_image