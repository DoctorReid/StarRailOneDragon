from concurrent.futures import ThreadPoolExecutor


class SrPreheatContext:

    def __init__(self, ctx):
        from sr_od.context.sr_context import SrContext
        self.ctx: SrContext = ctx
        self.executor = ThreadPoolExecutor(thread_name_prefix='sr_od_app_preheat', max_workers=1)

    def preheat_for_world_patrol_async(self) -> None:
        """
        锄大地预热-异步
        :return:
        """
        self.executor.submit(self.preheat_for_world_patrol)

    def preheat_for_world_patrol(self) -> None:
        """
        锄大地预热-异步
        :return:
        """
        self.preheat_mm_icon()
        from sr_od.sr_map import mini_map_utils
        mini_map_utils.preheat()

    def preheat_mm_icon(self):
        """
        预热小地图图标
        :return:
        """
        for prefix in ['mm_tp', 'mm_sp', 'mm_boss', 'mm_sub']:
            for i in range(100):
                if i == 0:
                    continue

                template_id = '%s_%02d' % (prefix, i)
                t = self.ctx.template_loader.get_template('mm_icon', template_id)
                if t is None:
                    break
                _ = t.gray
                _ = t.features

