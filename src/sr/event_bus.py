from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Any, List

from basic.log_utils import log

_sr_event_bus_executor = ThreadPoolExecutor(thread_name_prefix='sr_od_event_bus', max_workers=1)


class EventBus:

    def __init__(self):
        self.callbacks: dict[str, List[Callable[[Any], None]]] = {}

    def dispatch_event(self, event_id: str, event_obj: Any = None):
        """
        下发事件
        :param event_id: 事件ID
        :param event_obj: 事件体
        :return:
        """
        log.debug("事件触发 %s", event_id)
        _sr_event_bus_executor.submit(self._trigger_callback, event_id, event_obj)

    def _trigger_callback(self, event_id: str, event_obj: Any = None):
        """
        触发回调
        :param event_id: 事件ID
        :param event_obj: 事件体
        :return:
        """
        if event_id not in self.callbacks:
            pass
        for callback in self.callbacks[event_id]:
            try:
                callback(event_obj)
            except:
                log.error('事件处理失败', exc_info=True)

    def listen(self, event_id: str, callback: Callable[[Any], None]):
        """
        新增监听事件
        :param event_id:
        :param callback:
        :return:
        """
        if event_id not in self.callbacks:
            self.callbacks[event_id] = []
        existed_callbacks = self.callbacks[event_id]
        if callback not in existed_callbacks:
            existed_callbacks.append(callback)

    def unlisten(self, event_id: str, callback: Callable[[Any], None]):
        """
        解除一个事件的监听
        :param event_id:
        :param callback:
        :return:
        """
        if event_id not in self.callbacks:
            return
        self.callbacks[event_id].remove(callback)

    def unlisten_all(self, obj: Any):
        """
        解除一个对象的所有监听
        :param obj:
        :return:
        """
        to_remove = {}
        for key, existed_callbacks in self.callbacks.items():
            to_remove[key] = []
            for existed in existed_callbacks:
                if id(existed.__self__) == id(obj):
                    to_remove[key].append(existed)

        for key, removes in to_remove.items():
            for remove in removes:
                self.callbacks[key].remove(remove)
