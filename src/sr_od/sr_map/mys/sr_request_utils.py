import io
import os
from typing import List

import numpy as np
import requests
from PIL import Image

from one_dragon.base.geometry.rectangle import Rect
from one_dragon.utils import os_utils, str_utils, cv2_utils
from sr_od.sr_map.mys.sr_map_tree import MysSrRegionNode

APP_VERSION = "de16a09fca4e0ab89acf69fe0c12514f"

def get_map_tree() -> List[MysSrRegionNode]:
    """
    获取星铁地图树结构
    :return: 地图树结构
    """
    url = f'https://api-static.mihoyo.com/common/srmap/sr_map/v1/map/tree?map_id=38&app_sn=sr_map&lang=zh-cn&app_version={APP_VERSION}'
    response = requests.get(url)
    data = response.json()
    
    if data["retcode"] != 0:
        raise Exception(f"获取地图树失败: {data['message']}")
    
    tree_data = data["data"]["tree"]
    return [parse_region_node(node) for node in tree_data]


def get_map_info(region_id: int) -> MysSrRegionNode:
    """
    获取地图信息
    :param region_id: 区域id
    :return: 地图信息
    """
    url = f'https://api-static.mihoyo.com/common/srmap/sr_map/v1/map/info?map_id={region_id}&app_sn=sr_map&lang=zh-cn&app_version={APP_VERSION}'
    response = requests.get(url)
    data = response.json()

    if data["retcode"] != 0:
        raise Exception(f"获取信息失败: {data['message']}")

    info = data["data"]["info"]
    return parse_region_node(info)


def get_region_id(
        tree_list: list[MysSrRegionNode],
        planet_name: str,
        region_name: str,
) -> int | None:
    """
    获取某个区域的ID
    :param tree_list: 地图树列表
    :param planet_name: 星球名称
    :param region_name: 区域名称
    :return:
    """

    for planet_node in tree_list:
        if planet_node.name == planet_name:
            for region_node in planet_node.children:
                if region_node.name == region_name:
                    return region_node.id

    return None


def parse_region_node(data: dict) -> MysSrRegionNode:
    """
    解析区域节点
    :param data: 节点数据
    :return: 区域节点对象
    """
    children = [parse_region_node(child) for child in data.get("children", [])]
    return MysSrRegionNode(
        id=data["id"],
        name=data["name"],
        node_type=data["node_type"],
        depth=data["depth"],
        children=children,
        detail=data.get('detail', None),
    )


def get_map_image(image_url: str, resize: int = 120) -> Image:
    """
    获取地图图片
    请求 https://uploadstatic.mihoyo.com/sr-wiki/2023/02/14/288909604/400d12a7066c8d959e57357be056cafa_1241479384043926194.png?x-oss-process=image/resize,p_100/crop,x_0,y_256,w_256,h_256
    :param image_url: 图片链接
    :param resize: 缩放比例
    :return: 地图图片
    """
    url = f'{image_url}?x-oss-process=image/resize,p_{resize}'
    response = requests.get(url, stream=True)
    image_data = io.BytesIO(response.content)
    return Image.open(image_data)


def download_map_image(planet_name: str, region_name: str) -> dict[int, np.ndarray]:
    """
    下载地图图片
    :param planet_name: 星球名称
    :param region_name: 区域名称
    :return: key=楼层 value=图片
    """
    tree_arr = get_map_tree()
    region_id = get_region_id(tree_arr, planet_name, region_name)
    if region_id is None:
        raise Exception(f"未找到区域: {planet_name} - {region_name}")

    region_info = get_map_info(region_id)
    if region_info is None:
        raise Exception(f"未查到区域信息: {planet_name} - {region_name}")

    level_map = {}
    for level_info in region_info.children:
        if level_info.image_url is None or level_info.image_url == '':
            raise Exception(f"未找到图片: {planet_name} - {region_name} - {level_info.name}")

        # 计算楼层
        if level_info.name == region_name:
            level_num = 0
        else:
            level_num = str_utils.get_positive_digits(level_info.name)
            if level_info.name[0] == '-':
                level_num = -level_num

        pil_image: Image = get_map_image(level_info.image_url)

        # 将背景按游戏中的背景色进行填充
        pil_with_background = Image.new('RGB', pil_image.size, (200, 200, 200))  # 白色背景
        pil_with_background.paste(pil_image, mask=pil_image.split()[3])  # 使用 alpha 通道作为蒙版
        cv_image = np.array(pil_with_background)
        level_map[level_num] = cv_image

    return level_map


if __name__ == "__main__":
    # download_map_image('空间站「黑塔」', '主控舱段')
    pil_image = Image.open('downloaded_image.png')
    pil_with_background = Image.new('RGB', pil_image.size, (205, 205, 205))  # 白色背景
    pil_with_background.paste(pil_image, mask=pil_image.split()[3])  # 使用 alpha 通道作为蒙版
    cv_image = np.array(pil_with_background)
    # cv2_utils.save_image(cv_image, 'downloaded_image_with_background.png')

    test_map = cv2_utils.read_image(
        os.path.join(
            os_utils.get_path_under_work_dir('assets', 'template', 'large_map', 'P01_KJZHT', 'R01_ZKCD'),
            'raw.png'
        )
    )

    test_part = cv2_utils.crop_image_only(test_map, Rect(500, 300, 600, 400))
    mrl = cv2_utils.match_template(cv_image, test_part, 0.7)
    cv2_utils.show_image(cv_image, rects=mrl, wait=0)
    cv2_utils.show_overlap(cv_image, test_part, mrl.max.x, mrl.max.y, wait=0)