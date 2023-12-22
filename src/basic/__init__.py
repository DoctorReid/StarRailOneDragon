from typing import Union


class Point:

    def __init__(self, x: Union[int, float], y: Union[int, float]):
        """
        一个点 坐标会转化成整数
        :param x: 横坐标
        :param y: 纵坐标
        """

        self.x: int = int(x)
        """横坐标"""
        self.y: int = int(y)
        """纵坐标"""

    def tuple(self):
        return self.x, self.y

    def __str__(self):
        return '(%d, %d)' % (self.x, self.y)

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)


class Rect:

    def __init__(self, x1: Union[int, float], y1: Union[int, float], x2: Union[int, float], y2: Union[int, float]):
        """
        一个矩形 坐标会转化成整数
        :param x1: 左上角 横坐标
        :param y1: 左上角 纵坐标
        :param x2: 右下角 横坐标
        :param y2: 右下角 纵坐标
        """

        self.x1: int = int(x1)
        self.y1: int = int(y1)
        self.x2: int = int(x2)
        self.y2: int = int(y2)

    @property
    def center(self) -> Point:
        return Point((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    def __str__(self):
        return '(%d, %d, %d, %d)' % (self.x1, self.y1, self.x2, self.y2)

    @property
    def left_top(self) -> Point:
        return Point(self.x1, self.y1)

    @property
    def right_bottom(self) -> Point:
        return Point(self.x2, self.y2)
