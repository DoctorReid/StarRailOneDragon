from typing import Union, List

import cv2
import numpy as np
from PIL.Image import Image

from basic.img import ImageLike, MatchResult, MatchResultList


def read_image_with_alpha(file_path: str, show_result: bool = False):
    """
    读取图片 如果没有透明图层则加入
    :param file_path: 图片路径
    :param show_result: 是否显示结果
    :return:
    """
    image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
    channels = cv2.split(image)
    if len(channels) != 4:
        # 创建透明图层
        alpha = np.ones(image.shape[:2], dtype=np.uint8) * 255
        # 合并图像和透明图层
        image = cv2.merge((image, alpha))
    if show_result:
        cv2.imshow('Result', image)
    return image


def convert_source(source_image: ImageLike, src_x_scale: float = 1, src_y_scale: float = 1):
    """
    将原图转化成适合使用的cv2格式，会转化成RGBA
    :param source_image: 原图
    :param src_x_scale: 原图缩放比例x
    :param src_y_scale: 原图缩放比例y
    :return: 转化图
    """
    source: cv2.typing.MatLike = None
    if type(source_image) == Image:
        if source_image.mode == 'RGBA':
            source = cv2.cvtColor(np.array(source_image), cv2.COLOR_RGBA2BGRA)
        else:
            source = cv2.cvtColor(np.array(source_image.convert('RGBA')), cv2.COLOR_RGBA2BGRA)
    elif type(source_image) == str:
        source = cv2.imread(source_image)
    else:
        source = source_image
    if src_x_scale != 1 or src_y_scale != 1:
        source = cv2.resize(source, (0, 0), fx=src_x_scale, fy=src_y_scale)
    return source


def show_image(img: cv2.typing.MatLike,
               rects: Union[MatchResult, MatchResultList] = None,
               win_name='DEBUG'):
    """
    显示一张图片
    :param img: 图片
    :param rects: 需要画出来的框
    :param win_name:
    :return:
    """
    to_show = img

    if rects is not None:
        to_show = img.copy()
        if type(rects) == MatchResult:
            cv2.rectangle(to_show, (rects.x, rects.y), (rects.x + rects.w, rects.y + rects.h), (255, 0, 0), 1)
        elif type(rects) == MatchResultList:
            for i in rects:
                cv2.rectangle(to_show, (i.x, i.y), (i.x + i.w, i.y + i.h), (255, 0, 0), 1)

    cv2.imshow(win_name, to_show)
    cv2.waitKey(0)


def image_rotate(img: cv2.typing.MatLike, angle: int, show_result: bool = False):
    """
    对图片按中心进行旋转
    :param img: 原图
    :param angle: 逆时针旋转的角度
    :param show_result: 显示结果
    :return: 旋转后图片
    """
    height, width = img.shape[:2]
    center = (width // 2, height // 2)

    # 获取旋转矩阵
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    # 应用旋转矩阵来旋转图像
    rotated_image = cv2.warpAffine(img, rotation_matrix, (width, height))

    if show_result:
        cv2.imshow('Result', rotated_image)

    return rotated_image


def convert_png_and_save(image_path: str, save_path: str):
    """
    将原图转化成png格式保存
    :param image_path: 原图路径
    :param save_path: 目标路径
    """
    img = read_image_with_alpha(image_path)
    img.save(save_path)


def mark_area_as_transparent(image: cv2.typing.MatLike, pos: List, outside: bool = False):
    """
    将图片的一个区域变成透明 然后返回新的图片
    :param image: 原图
    :param pos: 区域坐标 如果是矩形 传入 [x,y,w,h] 如果是圆形 传入 [x,y,r]。其他数组长度不处理
    :param outside: 是否将区域外变成透明
    :return: 新图
    """
    # 创建一个与图像大小相同的掩膜，用于指定要变成透明的区域
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    if len(pos) == 4:
        x, y, w, h = pos[0], pos[1], pos[2], pos[3]
        # 非零像素表示要变成透明的区域
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
    if len(pos) == 3:
        x, y, r = pos[0], pos[1], pos[2]
        # 非零像素表示要变成透明的区域
        cv2.circle(mask, (x, y), r, 255, -1)
    # 合并
    return cv2.bitwise_and(image, image, mask=mask if outside else cv2.bitwise_not(mask))


def match_with_mask(source: cv2.typing.MatLike, template: cv2.typing.MatLike, threshold) -> MatchResultList:
    """
    在原图中 匹配模板。两者都需要是rgba格式。
    模板会忽略透明图层
    :param source: 原图
    :param template: 模板
    :param threshold: 阈值
    :return: 所有匹配结果
    """
    ty, tx, _ = template.shape
    # 创建掩码图像，将透明背景像素设置为零
    mask = np.where(template[..., 3] > 0, 255, 0).astype(np.uint8)
    # 进行模板匹配，忽略透明背景
    result = cv2.matchTemplate(source, template, cv2.TM_CCOEFF_NORMED, mask=mask)

    match_result_list = MatchResultList()
    locations = np.where(result >= threshold)  # 过滤低置信度的匹配结果

    # 遍历所有匹配结果，并输出位置和置信度
    for pt in zip(*locations[::-1]):
        confidence = result[pt[1], pt[0]]  # 获取置信度
        match_result_list.append(MatchResult(confidence, pt[0], pt[1], tx, ty))
    return match_result_list


def concat_vertically(img: cv2.typing.MatLike, next_img: cv2.typing.MatLike, decision_height: int = 200):
    """
    垂直拼接图片。
    假设两张图片是通过垂直滚动得到的，即宽度一样，部分内容重叠
    :param img: 图
    :param next_img: 下一张图
    :decision_height: 用第二张图的多少高度来判断重叠部分
    :return:
    """
    # 截取一个横截面用来匹配
    next_part = next_img[0: decision_height, :]
    result = match_with_mask(img, next_part, 0.5)
    # 找出置信度最高的结果
    r = None
    for i in result:
        if r is None or i.confidence > r.confidence:
            r = i
    h, w, _ = img.shape
    overlap_h = h - r.y
    extra_part = next_img[overlap_h+1:,:]
    # 垂直拼接两张图像
    return cv2.vconcat([img, extra_part])