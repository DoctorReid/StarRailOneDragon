import flet as ft
import os

from flet_core import CrossAxisAlignment, MainAxisAlignment
from sentry_sdk.integrations import threading

from basic.i18_utils import gt
from basic.log_utils import log
from sr.app.world_patrol import WorldPatrol
from sr.context import Context


class WorldPatrolView:

    def __init__(self, page: ft.Page, ctx: Context):
        self.page = page
        self.ctx = ctx

        self.start_btn = ft.ElevatedButton(text=gt("F9 开始"), on_click=self.start)
        self.pause_btn = ft.ElevatedButton(text=gt("F9 暂停"), on_click=self.pause, visible=False)
        self.resume_btn = ft.ElevatedButton(text=gt("F9 继续"), on_click=self.resume, visible=False)
        self.stop_btn = ft.ElevatedButton(text=gt("F10 结束"), on_click=self.stop, disabled=True)

        ctrl_row = ft.Row(controls=[
            ft.Container(content=self.start_btn),
            ft.Container(content=self.pause_btn),
            ft.Container(content=self.resume_btn),
            ft.Container(content=self.stop_btn),
        ], alignment=MainAxisAlignment.CENTER)

        self.shutdown_check = ft.Checkbox(label=gt("结束后关机"), value=False, on_change=self.on_shutdown_changed)

        self.running = ft.ProgressRing(width=16, height=16, stroke_width=2, visible=False)
        self.running_status = ft.Text(value=gt('未开始'))
        progress_col = ft.Column(controls=[
            ft.Container(content=self.running, height=20),
            ft.Container(content=self.running_status),
            ft.Container(content=ctrl_row),
            ft.Container(content=self.shutdown_check)
        ], horizontal_alignment=CrossAxisAlignment.CENTER)

        self.component = ft.Column(
            spacing=0, horizontal_alignment=CrossAxisAlignment.CENTER, expand=True,
            controls=[
                ft.Container(expand=True),
                ft.Container(content=progress_col, expand=True, alignment=ft.alignment.bottom_center),
            ])

    def start(self, e):
        self.running_status.value = gt('运行中')
        self.running.visible = True
        self.start_btn.visible = False
        self.pause_btn.visible = True
        self.resume_btn.visible = False
        self.stop_btn.disabled = False
        self.page.update()

        self.ctx.register_stop(self, self.after_stop)
        self.ctx.register_pause(self, self.on_pause, self.on_resume)
        t = threading.Thread(target=self.run_app)
        t.start()

    def on_pause(self):
        self.running_status.value = gt('暂停')
        self.running.visible = False
        self.start_btn.visible = False
        self.pause_btn.visible = False
        self.resume_btn.visible = True
        self.stop_btn.disabled = True
        self.page.update()

    def pause(self, e):
        self.on_pause()
        self.ctx.switch()

    def on_resume(self):
        self.running_status.value = gt('运行中')
        self.running.visible = True
        self.start_btn.visible = False
        self.pause_btn.visible = True
        self.resume_btn.visible = False
        self.stop_btn.disabled = False
        self.page.update()

    def resume(self, e):
        self.on_resume()
        self.ctx.switch()

    def stop(self, e):
        self.ctx.stop_running()

    def run_app(self):
        app = WorldPatrol(self.ctx)
        app.execute()

    def after_stop(self):
        self.running_status.value = gt('未开始')
        self.running.visible = False
        self.start_btn.visible = True
        self.pause_btn.visible = False
        self.resume_btn.visible = False
        self.stop_btn.disabled = True
        self.page.update()

        self.ctx.unregister(self)

        if self.shutdown_check.value:
            log.info('执行完毕 准备关机')
            os.system("shutdown /s /t 60")

    def on_shutdown_changed(self, e):
        if not self.shutdown_check.value:
            log.info('已取消关机计划')
            os.system("shutdown /a")



wpv: WorldPatrolView = None


def get(page: ft.Page, ctx: Context):
    global wpv
    if wpv is None:
        wpv = WorldPatrolView(page, ctx)
    return wpv
