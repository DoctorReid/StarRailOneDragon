from pydantic import BaseModel


class Point(BaseModel):
    """坐标 会转化成整数"""

    x: int
    y: int

    def __init__(self, x, y):
        super().__init__(x=int(x), y=int(y))

    def tuple(self):
        return self.x, self.y

    def __str__(self):
        return '(%d, %d)' % (self.x, self.y)

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)


class Rect(BaseModel):

    x1: int
    y1: int
    x2: int
    y2: int

    def __init__(self, x1, y1, x2, y2):
        super().__init__(x1=x1, y1=y1, x2=x2, y2=y2)

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
