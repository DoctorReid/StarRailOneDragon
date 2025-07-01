import json


class MysSrRegionNode:

    def __init__(
            self,
            id: int,
            name: str,
            node_type: int,
            depth: int,
            children: list["MysSrRegionNode"],
            detail: str = None,  # 详细信息 是地图图片信息
            image_url: str = None,  # 图片地址
    ):
        self.id: int = id  # 米游社上的ID 通过这个ID可以获取到其他信息
        self.node_type: int = node_type  # 区域类型 1=父节点 2=叶子节点
        self.depth: int = depth  # 深度 应该最大是3
        self.name: str = name  # 名称 (星穹列车/派对车厢/2层) 如果没有层数则是 (星穹列车/观景车厢/观景车厢)
        self.children: list["MysSrRegionNode"] = children  # 子节点
        self.image_url: str = image_url

        if image_url is None and detail is not None:
            self.image_url = _get_image_url(detail)


def _get_image_url(detail_str: str) -> str | None:
    if detail_str is None or detail_str == '':
        return None
    json_data = json.loads(detail_str)
    slices = json_data.get('slices', [])
    if len(slices) == 0:
        return None

    return slices[0][0].get('url')



