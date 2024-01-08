from typing import Optional

import flet as ft
import keyboard
from cv2.typing import MatLike

from basic.i18_utils import gt
from basic.img import cv2_utils
from basic.log_utils import log
from gui import components
from gui.sr_basic_view import SrBasicView
from sr.context import Context
from sr.image.sceenshot import mini_map
from sr.operation.unit.rogue import UNI_NUM_CN


class SimUniDraftRouteView(components.Card, SrBasicView):

    def __init__(self, page: ft.Page, ctx: Context):
        SrBasicView.__init__(self, page, ctx)

        self.keyboard_hook = None

        self.screenshot_btn = components.RectOutlinedButton(text=gt('F8 截图', 'ui'), on_click=self._do_screenshot)

        self.num_dropdown = ft.Dropdown(
            label=gt('模拟宇宙', 'ui'),
            options=[
                ft.dropdown.Option(key=str(num), text=gt('第%s宇宙' % cn, 'ui')) for num, cn in UNI_NUM_CN.items()
            ],
        )

        self.mini_map_display = ft.Image(src="a.png", error_content=ft.Text('等待选择区域'), visible=False)

        display_part = ft.Column(
            controls=[
                ft.Row(controls=[self.screenshot_btn]),
                ft.Row(controls=[self.num_dropdown]),
                ft.Row(controls=[self.mini_map_display])
            ],
            scroll=ft.ScrollMode.AUTO
        )

        components.Card.__init__(self, display_part)

        self.mini_map_image: Optional[MatLike] = None

    def handle_after_show(self):
        self.keyboard_hook = keyboard.on_press(self._on_key_press)
        pass

    def handle_after_hide(self):
        keyboard.unhook(self.keyboard_hook)

    def _on_key_press(self, event):
        k = event.name
        if k == 'f8':
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
        self.mini_map_image = mini_map.cut_mini_map(screen)

    def _show_mini_map(self):
        """
        展示小地图
        :return:
        """
        if self.mini_map_image is None:
            self.mini_map_display.visible = False
        else:
            self.mini_map_display.src_base64 = cv2_utils.to_base64(self.mini_map_image)
            self.mini_map_display.visible = True

        self.mini_map_display.update()


_sim_uni_draft_route_view: Optional[SimUniDraftRouteView] = None


def get(page: ft.Page, ctx: Context) -> SimUniDraftRouteView:
    global _sim_uni_draft_route_view
    if _sim_uni_draft_route_view is None:
        _sim_uni_draft_route_view = SimUniDraftRouteView(page, ctx)

    return _sim_uni_draft_route_view
