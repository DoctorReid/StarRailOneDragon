import cv2
import os
import numpy as np
from cv2.typing import MatLike

from basic import os_utils
from basic.img import cv2_utils
from basic.img.cv2_utils import convert_to_standard
from sr import constants
from sr.image.image_holder import ImageHolder
from sr.image.sceenshot import mini_map
from sr.image.sceenshot.mini_map import get_arrow_mask


def _read_template_raw_image(template_id):
    dir_path = os.path.join(os_utils.get_path_under_work_dir('images', 'template'), template_id)
    if not os.path.exists(dir_path):
        return None
    img = cv2_utils.read_image(os.path.join(dir_path, 'raw.png'))

    if img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img


def convert_template(template_id, save: bool = False):
    """
    把抠图后的图标灰度保存
    :param template_id:
    :param save:
    :return:
    """
    ih = ImageHolder()
    template = ih.get_template(template_id)
    gray = cv2.cvtColor(template.origin, cv2.COLOR_BGRA2GRAY)
    mask = np.where(template.origin[..., 3] > 0, 255, 0).astype(np.uint8)
    cv2_utils.show_image(template.origin, win_name='origin')
    cv2_utils.show_image(gray, win_name='gray')
    cv2_utils.show_image(mask, win_name='mask', wait=0)
    if save:
        dir = os_utils.get_path_under_work_dir('images', 'template', template_id)
        cv2.imwrite(os.path.join(dir, 'gray.png'), gray)
        cv2.imwrite(os.path.join(dir, 'mask.png'), mask)


def init_tp_with_background(template_id: str, noise_threshold: int = 0):
    """
    对传送点进行抠图 尽量多截取一点黑色背景
    将裁剪出来的图片 转化保留灰度图和对应掩码
    如果原图有透明通道 会转化成无透明通道的
    最后结果图都会转化到 51*51 并居中
    会覆盖原图 发现有问题可在图片显示时退出程序
    :param template_id:
    :return:
    """
    raw = _read_template_raw_image(template_id)
    if raw.shape[2] == 4:
        raw = cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, np.mean(gray), 255, cv2.THRESH_BINARY)
    if noise_threshold > 0:
        mask = cv2_utils.connection_erase(mask, threshold=noise_threshold)

    # 背景统一使用道路颜色 因为地图上传送点附近大概率都是道路 这样更方便匹配
    final_origin, final_mask = convert_to_standard(raw, mask, width=51, height=51, bg_color=constants.COLOR_MAP_ROAD_BGR)

    show_and_save(template_id, final_origin, final_mask)

def init_sp_with_background(template_id: str, noise_threshold: int = 0):
    """
    对特殊点进行抠图
    特殊点会自带一些黑色背景 通过找黑色的菱形区域保留下来
    将裁剪出来的图片 转化保留灰度图和对应掩码
    如果原图有透明通道 会转化成无透明通道的
    最后结果图都会转化到 51*51 并居中
    会覆盖原图 发现有问题可在图片显示时退出程序
    :param template_id:
    :param noise_threshold: 连通块小于多少时认为是噪点 视情况调整
    :return:
    """
    raw = _read_template_raw_image(template_id)
    sim = cv2_utils.color_similarity_2d(raw, (160, 210, 240))  # 前景颜色 特殊点主体部分
    cv2_utils.show_image(sim, win_name='sim')
    front_binary = cv2.inRange(sim, 180, 255)
    cv2_utils.show_image(front_binary, win_name='front_binary')

    # 画出黑色的菱形背景
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
    cv2_utils.show_image(gray, win_name='gray')
    black = cv2.inRange(gray, 0, 20)

    l1, r1, t1, b1 = get_four_corner(black)
    print(l1, r1, t1, b1)
    # 找特殊点主体部分的几个角 可能会覆盖到菱形
    l2, r2, t2, b2 = get_four_corner(front_binary)
    print(l2, r2, t2, b2)
    l = l1 if l1[0] < l2[0] else l2
    r = r1 if r1[0] > r2[0] else r2
    t = t1 if t1[1] < t2[1] else t2
    b = b1 if b1[1] > b2[1] else b2

    points = np.array([l, t, r, b], np.int32)
    points = points.reshape((-1, 1, 2))
    back_binary = np.zeros_like(gray)
    cv2.fillPoly(back_binary, [points], color=255)
    cv2_utils.show_image(back_binary, win_name='back_binary')

    binary = cv2.bitwise_or(front_binary, back_binary)
    cv2_utils.show_image(binary, win_name='binary')
    mask = cv2_utils.connection_erase(binary, threshold=noise_threshold)
    mask = cv2_utils.connection_erase(mask, threshold=noise_threshold, erase_white=False)

    final_origin, final_mask = convert_to_standard(raw, mask, width=51, height=51, bg_color=constants.COLOR_MAP_ROAD_BGR)

    show_and_save(template_id, final_origin, final_mask)


def init_ui_icon(template_id: str, noise_threshold: int = 0):
    """
    对界面交互图标进行抠图
    图标都是白色的 找一个较为深色背景的地图进行截图即可
    将裁剪出来的图片 转化保留灰度图和对应掩码
    如果原图有透明通道 会转化成无透明通道的
    最后结果图都会转化到 65*65 并居中
    发现有问题可在图片显示时退出程序
    :param template_id:
    :param noise_threshold: 连通块小于多少时认为是噪点 视情况调整
    :return:
    """
    raw = _read_template_raw_image(template_id)
    gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, np.mean(gray), 255, cv2.THRESH_BINARY)
    if noise_threshold > 0:
        mask = cv2_utils.connection_erase(mask, threshold=noise_threshold)
    final_origin, final_mask = convert_to_standard(raw, mask, d=65, bg_color=(0, 0, 0))
    show_and_save(template_id, final_origin, final_mask)


def init_battle_ctrl_icon(template_id: str, noise_threshold: int = 0):
    raw = _read_template_raw_image(template_id)
    if template_id == 'battle_ctrl_02':  # 自动战斗的图标激活之后有动态的光条 用激活前的做模板比较好
        gray = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, np.mean(gray), 255, cv2.THRESH_BINARY)
    else:
        mask = np.zeros((raw.shape[0], raw.shape[1]), dtype=np.uint8)
        b, g, r = cv2.split(raw)
        lower = 170
        mask[np.where(b > lower)] = 255
        mask[np.where(g > lower)] = 255
        mask[np.where(r > lower)] = 255
    final_origin, final_mask = convert_to_standard(raw, mask, width=51, height=35, bg_color=(0, 0, 0))
    show_and_save(template_id, final_origin, final_mask)


def get_four_corner(bw):
    """
    获取四个方向最远的白色像素点的位置
    :param bw: 黑白图
    :return:
    """
    white = np.where(bw == 255)
    left = (white[1][np.argmin(white[1])], white[0][np.argmin(white[1])])
    right = (white[1][np.argmax(white[1])], white[0][np.argmax(white[1])])
    top = (white[1][np.argmin(white[0])], white[0][np.argmin(white[0])])
    bottom = (white[1][np.argmax(white[0])], white[0][np.argmax(white[0])])
    return left, right, top, bottom


def show_and_save(template_id, origin, mask):
    gray = cv2.cvtColor(origin, cv2.COLOR_BGR2GRAY)
    cv2_utils.show_image(origin, win_name='origin')
    cv2_utils.show_image(gray, win_name='gray')
    cv2_utils.show_image(mask, win_name='mask')

    cv2.waitKey(0)

    save_template_image(origin, template_id, 'origin')
    save_template_image(gray, template_id, 'gray')
    save_template_image(mask, template_id, 'mask')
    init_template_feature(template_id)


def save_template_image(img: MatLike, template_id: str, tt: str):
    """
    保存模板图片
    :param img: 模板图片
    :param template_id: 模板id
    :param tt: 模板类型
    :return:
    """
    path = os_utils.get_path_under_work_dir('images', 'template', template_id)
    print(path)
    print(cv2.imwrite(os.path.join(path, '%s.png' % tt), img))


def init_template_feature(template_id: str) -> bool:
    """
    初始化模板的特征值
    :return:
    """
    ih = ImageHolder()
    template = ih.get_template(template_id)
    if template is None:
        return False
    keypoints, descriptors = cv2_utils.feature_detect_and_compute(template.origin, template.mask)
    dir_path = os_utils.get_path_under_work_dir('images', 'template', template_id)
    file_storage = cv2.FileStorage(os.path.join(dir_path, 'features.xml'), cv2.FILE_STORAGE_WRITE)
    # 保存特征点和描述符
    file_storage.write("keypoints", cv2_utils.feature_keypoints_to_np(keypoints))
    file_storage.write("descriptors", descriptors)
    file_storage.release()
    return True


def init_arrow_template(mm: MatLike):
    """
    找一个传送点下来朝正右方的地方 截取小箭头的template 推荐位置 空间站黑塔-支援舱段-月台
    :param mm: 小地图
    :return: 模板
    """
    bw, _ = mini_map.get_arrow_mask(mm)
    d0 = constants.TEMPLATE_ARROW_LEN_PLUS
    # 稍微放大一下 更好地匹配到边缘的结果
    _, bw = cv2_utils.convert_to_standard(bw, bw, width=d0, height=d0)
    rough_template = np.zeros((11 * d0, 11 * d0), dtype=np.uint8)
    for i in range(11):
        for j in range(11):
            offset_x = j * d0
            offset_y = i * d0
            angle = ((i * 11) + j) * 3
            if angle < 360:
                rough_template[offset_y:offset_y+d0, offset_x:offset_x+d0] = cv2_utils.image_rotate(bw, angle)

    precise_template = np.zeros((11 * d0, 11 * d0), dtype=np.uint8)
    for i in range(11):
        for j in range(11):
            offset_x = j * d0
            offset_y = i * d0
            angle = ((i * 11) + j - 60) / 10.0
            precise_template[offset_y:offset_y + d0, offset_x:offset_x + d0] = cv2_utils.image_rotate(bw, angle)

    # 稍微扩大一下模板 方便匹配
    cv2_utils.show_image(rough_template, win_name='rough_template')
    cv2_utils.show_image(precise_template, win_name='precise_template')
    cv2.waitKey(0)

    save_template_image(rough_template, 'arrow_rough', 'mask')
    save_template_image(precise_template, 'arrow_precise', 'mask')


def init_battle_lock():
    """
    初始化界面的锁定怪物图标
    需要找个怪兽锁定后截图 扣取红色的部分
    :return:
    """
    raw = _read_template_raw_image('battle_lock')
    b, g, r = cv2.split(raw)
    mask = np.zeros((raw.shape[0], raw.shape[1]), dtype=np.uint8)
    mask[np.where(r > 230)] = 255

    origin = cv2.bitwise_and(raw, raw, mask=mask)
    cv2_utils.show_image(origin, win_name='origin')
    cv2.waitKey(0)

