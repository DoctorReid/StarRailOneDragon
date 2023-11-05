import threading

import keyboard
import pyautogui
import subprocess
import time

from basic.i18_utils import gt
from basic.img.os import save_debug_image
from basic.log_utils import log
from sr.config import game_config
from sr.config.game_config import GameConfig
from sr.const import game_config_const
from sr.control import GameController
from sr.control.pc_controller import PcController
from sr.image import ImageMatcher
from sr.image.cn_ocr_matcher import CnOcrMatcher
from sr.image.cv2_matcher import CvImageMatcher
from sr.image.en_ocr_matcher import EnOcrMatcher
from sr.image.image_holder import ImageHolder
from sr.image.ocr_matcher import OcrMatcher
from sr.image.sceenshot import fill_uid_black
from sr.performance_recorder import PerformanceRecorder, get_recorder, log_all_performance
from sr.win import Window


class Context:

    def __init__(self):
        self.platform: str = 'PC'
        self.ih: ImageHolder = ImageHolder()
        self.im: ImageMatcher = None
        self.ocr: OcrMatcher = None
        self.controller: GameController = None
        self.running: int = 0  # 0-停止 1-运行 2-暂停
        self.press_event: dict = {}
        self.pause_callback: dict = {}
        self.resume_callback: dict = {}
        self.stop_callback: dict = {}

        keyboard.on_press(self.on_key_press)
        self.register_key_press('f9', self.switch)
        self.register_key_press('f10', self.stop_running)
        self.register_key_press('f11', self.screenshot)
        if self.platform == 'PC':
            self.register_key_press('f12', self.mouse_position)

        self.recorder: PerformanceRecorder = get_recorder()
        self.open_game_by_script: bool = False  # 脚本启动的游戏

    def register_key_press(self, key, callback):
        if key not in self.press_event:
            self.press_event[key] = []
        self.press_event[key].append(callback)

    def on_key_press(self, event):
        k = event.name
        if k in self.press_event:
            log.debug('触发按键 %s', k)
            for callback in self.press_event[k]:
                callback()

    def start_running(self) -> bool:
        if self.running != 0:
            log.error('不处于停止状态 当前状态(%d) 启动失败', self.running)
            return False

        self.running = 1
        self.controller.init()
        return True

    def stop_running(self):
        log.info('停止运行')  # 这里不能先判断 self.running == 0 就退出 因为有可能启动初始化就失败 这时候需要触发 after_stop 回调各方
        if self.running == 1:  # 先触发暂停 让执行中的指令停止
            self.switch()
        self.running = 0
        t = threading.Thread(target=self.after_stop)
        t.start()

    def after_stop(self):
        for obj_id, callback in self.stop_callback.items():
            callback()

        log_all_performance()

    def switch(self):
        if self.running == 1:
            log.info('暂停运行')
            self.running = 2
            callback_arr = self.pause_callback.copy()
            for obj_id, callback in callback_arr.items():
                callback()
        elif self.running == 2:
            log.info('恢复运行')
            self.running = 1
            callback_arr = self.resume_callback.copy()
            for obj_id, callback in callback_arr.items():
                callback()

    def register_pause(self, obj,
                       pause_callback,
                       resume_callback):
        self.pause_callback[id(obj)] = pause_callback
        self.resume_callback[id(obj)] = resume_callback

    def register_stop(self, obj, stop_callback):
        self.stop_callback[id(obj)] = stop_callback

    def unregister(self, obj):
        if id(obj) in self.pause_callback:
            del self.pause_callback[id(obj)]
        if id(obj) in self.resume_callback:
            del self.resume_callback[id(obj)]

    def init_controller(self, renew: bool = False) -> bool:
        self.open_game_by_script = False
        if renew:
            self.controller = None
        try:
            if self.controller is None:
                if self.platform == 'PC':
                    self.controller = PcController(win=get_game_win(), ocr=self.ocr)
        except pyautogui.PyAutoGUIException:
            log.info('未开打游戏')
            if not try_open_game():
                return False

            for i in range(10):
                time.sleep(1)
                try:
                    self.controller = PcController(win=get_game_win(), ocr=self.ocr)
                    break
                except pyautogui.PyAutoGUIException:
                    log.info('未检测到游戏窗口 等待中')

            if self.controller is None:
                log.error('未能检测到游戏窗口')
                return False
            self.open_game_by_script = True
        log.info('加载游戏控制器完毕')
        return True

    def init_image_matcher(self, renew: bool = False) -> bool:
        if renew:
            self.im = None
        if self.im is None:
            self.im = CvImageMatcher(self.ih)
        log.info('加载图片匹配器完毕')
        return True

    def init_ocr_matcher(self, renew: bool = False) -> bool:
        if renew:
            self.ocr = None
        if self.ocr is None:
            self.ocr = get_ocr_matcher(game_config.get().lang)
        log.info('加载OCR识别器完毕')
        return True

    def init_all(self, renew: bool = False) -> bool:
        result: bool = True
        result = result and self.init_image_matcher(renew)
        result = result and self.init_ocr_matcher(renew)
        result = result and self.init_controller(renew)
        return result

    def mouse_position(self):
        rect = self.controller.win.get_win_rect()
        pos = pyautogui.position()
        log.info('当前鼠标坐标 %s', (pos.x - rect.x, pos.y - rect.y))

    def screenshot(self):
        """
        仅供快捷键使用 命令途中获取截图请使用 controller.screenshot()
        :return:
        """
        self.init_controller()
        save_debug_image(fill_uid_black(self.controller.screenshot()))


def try_open_game() -> bool:
    """
    尝试打开游戏 如果有配置游戏路径的话
    :return:
    """
    gc: GameConfig = game_config.get()
    if gc.game_path == '':
        log.info('未配置游戏路径 无法自动启动')
        return False
    log.info('尝试自动启动游戏 路径为 %s', gc.game_path)
    subprocess.Popen(gc.game_path)
    return True


def get_game_win() -> Window:
    return Window(gt('崩坏：星穹铁道', model='ui'))


_ocr_matcher = {}


def get_ocr_matcher(lang: str) -> OcrMatcher:
    matcher: OcrMatcher = None
    if lang not in _ocr_matcher:
        if lang == game_config_const.LANG_CN:
            matcher = CnOcrMatcher()
        elif lang == game_config_const.LANG_EN:
            matcher = EnOcrMatcher()
        _ocr_matcher[lang] = matcher
    else:
        matcher = _ocr_matcher[lang]
    return matcher


global_context: Context = Context()


def get_context() -> Context:
    global global_context
    return global_context

