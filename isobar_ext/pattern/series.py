from __future__ import annotations

import sys

from .core import Pattern


#  taken out from sequence due to circular dependency


class PSeries(Pattern):
    """ PSeries: Arithmetic series, beginning at `start`, increment by `step`

        >>> p = PSeries(3, 9)
        >>> p.nextn(16)
        [3, 12, 21, 30, 39, 48, 57, 66, 75, 84, 93, 102, 111, 120, 129, 138]
        """

    def __init__(self, start: float = 0, step: float = 1, length: int = sys.maxsize):
        self.start = start
        self.value = start
        self.step = step
        self.length = length
        self.count = 0

    def __repr__(self):
        return f"PSeries({self.start}, {self.step}, {self.length})"

    def reset(self):
        super().reset()

        self.value = self.start
        self.count = 0

    def __next__(self):
        length = Pattern.value(self.length)
        if self.count >= length:
            # return None
            raise StopIteration
        step = Pattern.value(self.step)
        n = self.value
        self.value += step
        self.count += 1
        return n
