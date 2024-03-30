import os
from typing import Optional

import cv2

from basic import os_utils
from basic.img import cv2_utils
from sr.const.map_const import Region
from sr.image import TemplateImage, get_large_map_dir_path
from sr.image.sceenshot import LargeMapInfo


class ImageHolder:

    def __init__(self):
        self.large_map = {}
        self.template = {}

    def load_large_map(self, region: Region) -> LargeMapInfo:
        """
        加载某张大地图到内存中
        :param region: 对应区域
        :return: 地图图片
        """
        dir_path = get_large_map_dir_path(region)
        info = LargeMapInfo()
        info.region = region
        info.raw = cv2_utils.read_image(os.path.join(dir_path, 'raw.png'))
        info.origin = cv2_utils.read_image(os.path.join(dir_path, 'origin.png'))
        info.gray = cv2_utils.read_image(os.path.join(dir_path, 'gray.png'))
        info.mask = cv2_utils.read_image(os.path.join(dir_path, 'mask.png'))
        feature_path = os.path.join(dir_path, 'features.xml')
        if os.path.exists(feature_path):
            file_storage = cv2.FileStorage(feature_path, cv2.FILE_STORAGE_READ)
            # 读取特征点和描述符
            info.kps = cv2_utils.feature_keypoints_from_np(file_storage.getNode("keypoints").mat())
            info.desc = file_storage.getNode("descriptors").mat()
            # 释放文件存储对象
            file_storage.release()
        self.large_map[region.prl_id] = info
        return info

    def pop_large_map(self, region: Region, map_type: str):
        """
        将某张地图从内存中删除
        :param region: 对应区域
        :param map_type: 地图类型
        :return:
        """
        key = region.prl_id
        if key in self.large_map:
            del self.large_map[key]

    def get_large_map(self, region: Region) -> LargeMapInfo:
        """
        获取某张大地图
        :param region: 区域
        :return: 地图图片
        """
        if region.prl_id not in self.large_map:
            # 尝试加载一次
            return self.load_large_map(region)
        else:
            return self.large_map[region.prl_id]

    def load_template(self, template_id: str, sub_dir: Optional[str] = None) -> Optional[TemplateImage]:
        """
        加载某个模板到内存
        :param template_id: 模板id
        :param sub_dir: 子文件夹
        :return: 模板图片
        """
        dir_path = os.path.join(os_utils.get_path_under_work_dir('images', 'template', sub_dir), template_id)
        if not os.path.exists(dir_path):  # 注意上方不要直接用get_path_under_work_dir获取全路径 避免创建空文件夹
            return None
        template: TemplateImage = TemplateImage()
        template.origin = cv2_utils.read_image(os.path.join(dir_path, 'origin.png'))
        template.gray = cv2_utils.read_image(os.path.join(dir_path, 'gray.png'))
        template.mask = cv2_utils.read_image(os.path.join(dir_path, 'mask.png'))

        feature_path = os.path.join(dir_path, 'features.xml')
        if os.path.exists(feature_path):
            file_storage = cv2.FileStorage(feature_path, cv2.FILE_STORAGE_READ)
            # 读取特征点和描述符
            template.kps = cv2_utils.feature_keypoints_from_np(file_storage.getNode("keypoints").mat())
            template.desc = file_storage.getNode("descriptors").mat()
            # 释放文件存储对象
            file_storage.release()
        else:
            if template.origin is not None and template.mask is not None:
                template.kps, template.desc = cv2_utils.feature_detect_and_compute(template.origin, template.mask)

        key = '%s:%s' % ('' if sub_dir is None else sub_dir, template_id)
        self.template[key] = template
        return template

    def pop_template(self, template_id: str):
        """
        将某个模板从内存中删除
        :param template_id: 模板id
        :return:
        """
        if template_id in self.template:
            del self.template[template_id]

    def get_template(self, template_id: str, sub_dir: Optional[str] = None) -> TemplateImage:
        """
        获取某个模板
        :param template_id: 模板id
        :param sub_dir: 子文件夹
        :return: 模板图片
        """
        key = '%s:%s' % ('' if sub_dir is None else sub_dir, template_id)
        if key in self.template:
            return self.template[key]
        else:
            return self.load_template(template_id, sub_dir)

    def preheat_for_world_patrol(self):
        """
        锄大地预热加载模板
        :return:
        """
        for prefix in ['mm_tp', 'mm_sp', 'mm_boss', 'mm_sub']:
            for i in range(100):
                if i == 0:
                    continue

                template_id = '%s_%02d' % (prefix, i)
                t: TemplateImage = self.get_template(template_id)
                if t is None:
                    break

    def get_character_avatar_template(self, template_id: str) -> TemplateImage:
        """
        获取角色头像模板
        :param template_id: 模板id
        :return: 模板图片
        """
        return self.get_template(template_id, sub_dir='character_avatar')

    def get_character_combat_type(self, template_id: str) -> TemplateImage:
        """
        获取角色战斗属性模板
        :param template_id: 模板id
        :return: 模板图片
        """
        return self.get_template(template_id, sub_dir='character_combat_type')

    def get_sim_uni_template(self, template_id: str) -> TemplateImage:
        """
        获取模板 - 模拟宇宙
        :param template_id: 模板id
        :return: 模板图片
        """
        return self.get_template(template_id, sub_dir='sim_uni')
