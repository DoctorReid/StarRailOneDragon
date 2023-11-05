class Point:
    """
    坐标 会转化成整数
    """
    def __init__(self, x, y):
        self.x: int = int(x)
        self.y: int = int(y)

    def tuple(self):
        return self.x, self.y

    def __str__(self):
        return '(%d, %d)' % (self.x, self.y)


class Rect:
    def __init__(self, x1, y1, x2, y2):
        self.x1: int = int(x1)
        self.y1: int = int(y1)
        self.x2: int = int(x2)
        self.y2: int = int(y2)

    @property
    def center(self) -> Point:
        return Point((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    def __str__(self):
        return '(%d, %d, %d, %d)' % (self.x1, self.y1, self.x2, self.y2)
