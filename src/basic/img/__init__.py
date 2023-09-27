from typing import List


class MatchResult:

    def __init__(self, c, x, y, w, h):
        self.confidence = c
        self.x = int(x)
        self.y = int(y)
        self.w = int(w)
        self.h = int(h)
        self.cx = int(self.x + self.w // 2)
        self.cy = int(self.y + self.h // 2)

    def __str__(self):
        return '(%.2f, %d, %d, %d, %d)' % (self.confidence, self.x, self.y, self.w, self.h)


class MatchResultList:

    def __init__(self):
        self.arr: List[MatchResult] = []
        self.max: MatchResult = None

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