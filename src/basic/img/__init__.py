from typing import List, Optional

from basic import Point


class MatchResult:

    def __init__(self, c, x, y, w, h, template_scale: float = 1, data: str = None):
        self.confidence = c
        self.x = int(x)
        self.y = int(y)
        self.w = int(w)
        self.h = int(h)
        self.template_scale = template_scale
        self.data: str = data

    def __str__(self):
        return '(%.2f, %d, %d, %d, %d, %.2f)' % (self.confidence, self.x, self.y, self.w, self.h, self.template_scale)

    @property
    def left_top(self) -> Point:
        return Point(self.x, self.y)

    @property
    def center(self) -> Point:
        return Point(self.x + self.w // 2, self.y + self.h // 2)

    def add_offset(self, p: Point):
        self.x += p.x
        self.y += p.y


class MatchResultList:
    """
    一个检测目标的多种可能结果。
    一张图片可能有多个检测目标。
    
    该类主张描述 ["绥园", "妥园"], 而非记录各个检测对象OCR结果 ["绥园", "迴星港"]
    然而大部分情况OCR模型最后一层都会做softmax整合, 一个检测对象, 只会返回最好的情况, 故其len常常为1
    """
    def __init__(self, only_best: bool = True):
        self.only_best: bool = only_best
        self.arr: List[MatchResult] = []
        self.max: Optional[MatchResult] = None

    def __str__(self):
        return '[%s]' % ', '.join(str(i) for i in self.arr)

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index < len(self.arr):
            value = self.arr[self.index]
            self.index += 1
            return value
        else:
            raise StopIteration

    def __len__(self):
        return len(self.arr)

    def append(self, a: MatchResult, auto_merge: bool = True, merge_distance: float = 10):
        """
        添加匹配结果，如果开启合并，则保留置信度更高的结果
        :param a: 需要添加的结构
        :param auto_merge: 是否与之前结果进行合并
        :param merge_distance: 多少距离内的
        :return:
        """
        if self.only_best:
            if self.max is None:
                self.max = a
                self.arr.append(a)
            elif a.confidence > self.max.confidence:
                self.max = a
                self.arr[0] = a
        else:
            if auto_merge:
                for i in self.arr:
                    if (i.x - a.x) ** 2 + (i.y - a.y) ** 2 <= merge_distance ** 2:
                        if a.confidence > i.confidence:
                            i.x = a.x
                            i.y = a.y
                            i.confidence = a.confidence
                        return

            self.arr.append(a)
            if self.max is None or a.confidence > self.max.confidence:
                self.max = a
