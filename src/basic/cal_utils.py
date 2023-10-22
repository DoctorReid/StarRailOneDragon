import math


def distance_between(pos1: tuple, pos2: tuple) -> float:
    """
    计算两点之间的距离
    :param pos1:
    :param pos2:
    :return:
    """
    x1, y1 = pos1
    x2, y2 = pos2
    return math.sqrt(((x1 - x2) ** 2) + ((y1 - y2) ** 2))


def get_angle_by_pts(from_pos: tuple, to_pos: tuple) -> float:
    """
    计算两点形成向量的角度
    :param from_pos: 起始点
    :param to_pos: 结束点
    :return: 角度 正右方为0 顺时针为正
    """
    x1, y1 = from_pos
    x2, y2 = to_pos
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0:
        if dy > 0:
            return 90
        elif dy == 0:
            return 0
        else:
            return 270
    if dy == 0:
        if dx >= 0:
            return 0
        else:
            return 180
    angle = math.degrees(math.atan((dy) / (dx)))
    if angle > 0 and (dy < 0 and dx < 0):
        angle += 180
    elif angle < 0 and (dx < 0 and dy > 0):
        angle += 180
    elif angle < 0 and (dx > 0 and dy < 0):
        angle += 360
    return angle


def in_rect(point: tuple, rect: tuple) -> bool:
    """
    点是否在矩阵内
    :param point:
    :param rect:
    :return:
    """
    return rect[0] <= point[0] <= rect[2] and rect[1] <= point[1] <= rect[3]


def calculate_overlap_area(rect1, rect2):
    # rect1和rect2分别表示两个矩形的坐标信息 (x1, y1, x2, y2)
    x1, y1, x2, y2 = rect1
    x3, y3, x4, y4 = rect2

    if x1 > x4 or x2 < x3 or y1 > y4 or y2 < y3:
        # 两个矩形不相交，重叠面积为0
        return 0
    else:
        # 计算重叠矩形的左上角坐标和右下角坐标
        overlap_x1 = max(x1, x3)
        overlap_y1 = max(y1, y3)
        overlap_x2 = min(x2, x4)
        overlap_y2 = min(y2, y4)

        # 计算重叠矩形的宽度和高度
        width = overlap_x2 - overlap_x1
        height = overlap_y2 - overlap_y1

        # 计算重叠矩形的面积
        overlap_area = width * height
        return overlap_area


def coalesce(*args):
    """
    返回第一个非空元素
    :param args:
    :return:
    """
    return next((arg for arg in args if arg is not None), None)