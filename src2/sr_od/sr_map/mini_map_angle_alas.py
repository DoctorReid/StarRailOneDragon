from functools import lru_cache

import cv2
import numpy as np
from cv2.typing import MatLike
from scipy import signal


@lru_cache
def RotationRemapData(d: int):
    mx = np.zeros((d, d), dtype=np.float32)
    my = np.zeros((d, d), dtype=np.float32)
    for i in range(d):
        for j in range(d):
            mx[i, j] = d / 2 + i / 2 * np.cos(2 * np.pi * j / d)
            my[i, j] = d / 2 + i / 2 * np.sin(2 * np.pi * j / d)
    return mx, my


def peak_confidence(arr, **kwargs):
    """
    Evaluate the prominence of the highest peak

    Args:
        arr (np.ndarray): Shape (N,)
        **kwargs: Additional kwargs for signal.find_peaks

    Returns:
        float: 0-1
    """
    para = {
        'height': 0,
        'prominence': 10,
    }
    para.update(kwargs)
    length = len(arr)
    peaks, properties = signal.find_peaks(np.concatenate((arr, arr, arr)), **para)
    peaks = [h for p, h in zip(peaks, properties['peak_heights']) if length <= p < length * 2]
    peaks = sorted(peaks, reverse=True)

    count = len(peaks)
    if count > 1:
        highest, second = peaks[0], peaks[1]
    elif count == 1:
        highest, second = 1, 0
    else:
        highest, second = 1, 0
    confidence = (highest - second) / highest
    return confidence


def convolve(arr, kernel=3):
    """
    Args:
        arr (np.ndarray): Shape (N,)
        kernel (int):

    Returns:
        np.ndarray:
    """
    return sum(np.roll(arr, i) * (kernel - abs(i)) // kernel for i in range(-kernel + 1, kernel))


def calculate(minimap: MatLike, scale: int = 1):
    """
    计算小地图上角色的朝向 参考自 ALAZ
    https://github.com/LmeSzinc/StarRailCopilot/wiki/MinimapTracking#%E6%98%9F%E7%A9%B9%E9%93%81%E9%81%93%E8%A7%86%E9%87%8E%E6%9C%9D%E5%90%91%E8%AF%86%E5%88%AB
    https://github.com/LmeSzinc/StarRailCopilot/blob/db3e78498ea06b0d3548263773b0f2bfa9adba0d/tasks/map/minimap/minimap.py#L261
    :param minimap:
    :param scale:
    :return: 1.875倍数的角度
    """
    d = minimap.shape[0]

    # Extract
    _, _, v = cv2.split(cv2.cvtColor(minimap, cv2.COLOR_RGB2YUV))

    image = cv2.subtract(128, v)

    image = cv2.GaussianBlur(image, (3, 3), 0)
    # Expand circle into rectangle
    m1, m2 = RotationRemapData(d)
    remap = cv2.remap(image, m1, m2, cv2.INTER_LINEAR)[d * 1 // 10:d * 6 // 10].astype(np.float32)
    remap = cv2.resize(remap, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    # Find derivative
    gradx = cv2.Scharr(remap, cv2.CV_32F, 1, 0)

    # Magic parameters for scipy.find_peaks
    para = {
        'height': 35,
        'wlen': d * scale,
    }
    l = np.bincount(signal.find_peaks(gradx.ravel(), **para)[0] % (d * scale), minlength=d * scale)
    r = np.bincount(signal.find_peaks(-gradx.ravel(), **para)[0] % (d * scale), minlength=d * scale)
    l, r = np.maximum(l - r, 0), np.maximum(r - l, 0)

    conv0 = []
    kernel = 2 * scale
    r_expanded = np.concatenate([r, r, r])
    r_length = len(r)

    # Faster than nested calling np.roll()
    def roll_r(shift):
        return r_expanded[r_length - shift:r_length * 2 - shift]

    def convolve_r(ker, shift):
        return sum(roll_r(shift + i) * (ker - abs(i)) // ker for i in range(-ker + 1, ker))

    for offset in range(-kernel + 1, kernel):
        result = l * convolve_r(ker=3 * kernel, shift=-d * scale // 4 + offset)
        conv0 += [result]

    conv0 = np.maximum(conv0, 1)
    maximum = np.max(conv0, axis=0)
    rotation_confidence = round(peak_confidence(maximum), 3)
    if rotation_confidence > 0.3:
        # Good match
        result = maximum
    else:
        # Convolve again to reduce noice
        average = np.mean(conv0, axis=0)
        minimum = np.min(conv0, axis=0)
        result = convolve(maximum * average * minimum, 2 * scale)
        rotation_confidence = round(peak_confidence(maximum), 3)

    # Convert match point to degree
    degree = np.argmax(result) / (d * scale) * 360 + 135
    degree = degree - 1.875  # 跟alas的+3不一样 这边认为 空间站黑塔-支援舱段-月台 落地后为正右方 0度 以此为基准调整的值
    while degree > 360:
        degree -= 360

    degree -= 90
    if degree < 0:
        degree += 360

    return degree
