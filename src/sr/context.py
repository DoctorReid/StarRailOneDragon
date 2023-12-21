import subprocess
import threading
import time

import keyboard
import pyautogui

from basic import os_utils
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
        self.start_callback: dict = {}
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
        self.first_transport: bool = True  # 第一次传送

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
            log.error('请先结束其他运行中的功能 再启动', self.running)
            return False

        if not self.init_all(renew=True):
            self.stop_running()
            return False

        self.running = 1
        self.controller.init()
        self._after_start()
        return True

    @property
    def is_stop(self) -> bool:
        return self.running == 0

    @property
    def is_running(self) -> bool:
        return self.running == 1

    @property
    def is_pause(self) -> bool:
        return self.running == 2

    @property
    def status_text(self) -> str:
        if self.running == 0:
            return gt('空闲', 'ui')
        elif self.running == 1:
            return gt('运行中', 'ui')
        elif self.running == 2:
            return gt('暂停中', 'ui')
        else:
            return 'unknow'

    def _after_start(self):
        for obj_id, callback in self.start_callback.items():
            t = threading.Thread(target=callback)
            t.start()

    def stop_running(self):
        if self.running == 0:
            return
        log.info('停止运行')  # 这里不能先判断 self.running == 0 就退出 因为有可能启动初始化就失败 这时候需要触发 after_stop 回调各方
        if self.running == 1:  # 先触发暂停 让执行中的指令停止
            self.switch()
        self.running = 0
        self._after_stop()

    def _after_stop(self):
        for obj_id, callback in self.stop_callback.items():
            t = threading.Thread(target=callback)
            t.start()

        if os_utils.is_debug():
            log_all_performance()

    def switch(self):
        if self.running == 1:
            log.info('暂停运行')
            self.running = 2
            self._after_pause()
        elif self.running == 2:
            log.info('恢复运行')
            self.running = 1
            self._after_resume()

    def _after_pause(self):
        callback_arr = self.pause_callback.copy()
        for obj_id, callback in callback_arr.items():
            t = threading.Thread(target=callback)
            t.start()

    def _after_resume(self):
        callback_arr = self.resume_callback.copy()
        for obj_id, callback in callback_arr.items():
            t = threading.Thread(target=callback)
            t.start()

    def register_status_changed_handler(self, obj,
                                        after_start_callback=None,
                                        after_pause_callback=None,
                                        after_resume_callback=None,
                                        after_stop_callback=None):
        if after_start_callback is not None:
            self.start_callback[id(obj)] = after_start_callback
        if after_pause_callback is not None:
            self.pause_callback[id(obj)] = after_pause_callback
        if after_resume_callback is not None:
            self.resume_callback[id(obj)] = after_resume_callback
        if after_stop_callback is not None:
            self.stop_callback[id(obj)] = after_stop_callback

    def register_pause(self, obj,
                       pause_callback,
                       resume_callback):
        self.pause_callback[id(obj)] = pause_callback
        self.resume_callback[id(obj)] = resume_callback

    def register_stop(self, obj, stop_callback):
        self.stop_callback[id(obj)] = stop_callback

    def unregister(self, obj):
        if id(obj) in self.start_callback:
            del self.start_callback[id(obj)]
        if id(obj) in self.pause_callback:
            del self.pause_callback[id(obj)]
        if id(obj) in self.resume_callback:
            del self.resume_callback[id(obj)]
        if id(obj) in self.stop_callback:
            del self.stop_callback[id(obj)]

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

            for i in range(30):
                if self.running == 0:
                    break
                time.sleep(1)
                try:
                    self.controller = PcController(win=get_game_win(), ocr=self.ocr)
                    self.running = 0
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
        log.info('加载工具中')
        result: bool = True
        result = result and self.init_image_matcher(renew)
        result = result and self.init_ocr_matcher(renew)
        result = result and self.init_controller(renew)
        if result:
            log.info('加载工具完毕')
        return result

    def mouse_position(self):
        self.init_controller(False)
        rect = self.controller.win.get_win_rect()
        pos = pyautogui.position()
        log.info('当前鼠标坐标 %s', (pos.x - rect.x, pos.y - rect.y))

    def screenshot(self):
        """
        仅供快捷键使用 命令途中获取截图请使用 controller.screenshot()
        :return:
        """
        self.init_controller(False)
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
    global_context.running = 1
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

