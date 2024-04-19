from concurrent.futures import ThreadPoolExecutor

import flet as ft
from flet_core import CrossAxisAlignment, MainAxisAlignment

from basic import win_utils
from basic.i18_utils import gt
from basic.log_utils import log
from gui import snack_bar, components
from gui.sr_basic_view import SrBasicView
from sr.context import Context

_sr_app_view_executor = ThreadPoolExecutor(thread_name_prefix='sr_od_sr_app_view', max_workers=1)


class SrAppView(components.Card, SrBasicView):

    def __init__(self, page: ft.Page, ctx: Context):
        SrBasicView.__init__(self, page, ctx)

        self.start_btn = ft.ElevatedButton(text=gt("F9 开始", model='ui'), on_click=self.start)
        self.pause_btn = ft.ElevatedButton(text=gt("F9 暂停", model='ui'), on_click=self.pause, visible=False)
        self.resume_btn = ft.ElevatedButton(text=gt("F9 继续", model='ui'), on_click=self.resume, visible=False)
        self.stop_btn = ft.ElevatedButton(text=gt("F10 结束", model='ui'), on_click=self.stop, disabled=True)

        ctrl_row = ft.Row(controls=[
            ft.Container(content=self.start_btn),
            ft.Container(content=self.pause_btn),
            ft.Container(content=self.resume_btn),
            ft.Container(content=self.stop_btn),
        ], alignment=MainAxisAlignment.CENTER)

        self.after_done_dropdown = components.AfterDone(self._on_after_done_changed)

        self.running = ft.ProgressRing(width=16, height=16, stroke_width=2, visible=False)
        self.running_status = ft.Text(value=gt('未开始', model='ui'))
        progress_col = ft.Column(controls=[
            ft.Container(content=self.running, height=20),
            ft.Container(content=self.running_status),
            ft.Container(content=ctrl_row),
            ft.Container(content=self.after_done_dropdown)
        ], horizontal_alignment=CrossAxisAlignment.CENTER)

        self.diy_part = ft.Container(expand=True)
        content = ft.Column(
            spacing=5, horizontal_alignment=CrossAxisAlignment.CENTER, expand=True,
            controls=[
                self.diy_part,
                ft.Container(content=progress_col, expand=True, alignment=ft.alignment.bottom_center),
            ])

        components.Card.__init__(self, content)

    def start(self, e=None):
        if self.sr_ctx.running != 0:
            snack_bar.show_message(gt('请先结束其他运行中的功能 再启动', 'ui'), self.flet_page)
            return

        self.running_status.value = gt('运行中', model='ui')
        self.running.visible = True
        self.start_btn.visible = False
        self.pause_btn.visible = True
        self.resume_btn.visible = False
        self.stop_btn.disabled = False
        self.update()

        self.sr_ctx.register_stop(self, self.after_stop)
        self.sr_ctx.register_pause(self, self.on_pause, self.on_resume)
        _sr_app_view_executor.submit(self.run_app)

    def on_pause(self):
        self.running_status.value = gt('暂停', model='ui')
        self.running.visible = False
        self.start_btn.visible = False
        self.pause_btn.visible = False
        self.resume_btn.visible = True
        self.stop_btn.disabled = False
        self.update()

    def pause(self, e):
        self.sr_ctx.switch()

    def on_resume(self):
        self.running_status.value = gt('运行中', model='ui')
        self.running.visible = True
        self.start_btn.visible = False
        self.pause_btn.visible = True
        self.resume_btn.visible = False
        self.stop_btn.disabled = False
        self.update()

    def resume(self, e):
        self.sr_ctx.switch()

    def stop(self, e):
        self.sr_ctx.stop_running()

    def run_app(self):
        pass

    def after_stop(self):
        self.running_status.value = gt('未开始', model='ui')
        self.running.visible = False
        self.start_btn.visible = True
        self.pause_btn.visible = False
        self.resume_btn.visible = False
        self.stop_btn.disabled = True
        self.update()

        self.sr_ctx.unregister(self)

        if self.after_done_dropdown.value == 'shutdown':
            log.info('执行完毕 准备关机')
            win_utils.shutdown_sys(60)
        elif self.after_done_dropdown.value == 'close':
            log.info('执行完毕 关闭游戏')
            if self.sr_ctx.controller is not None:
                self.sr_ctx.controller.close_game()

    def _on_after_done_changed(self, e):
        if self.after_done_dropdown.value != 'shutdown':
            win_utils.cancel_shutdown_sys()
