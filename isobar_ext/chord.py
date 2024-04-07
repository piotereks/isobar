import copy
import random


class Chord:
    """Represents a chord made up of 1 or more note intervals."""

    dict = {}

    def __init__(self, intervals=None, root=0, name="unnamed chord"):
        if intervals is None:
            intervals = []
        self.intervals = intervals
        self.name = name
        self.root = root
        if name not in Chord.dict:
            Chord.dict[name] = self

    def __str__(self):
        return f'{self.name} [{",".join(str(n) for n in self.semitones)}]'

    @property
    def semitones(self):
        return [self.root] + [
            sum(self.intervals[: n + 1], self.root)
            for n in range(len(self.intervals))
        ]

    @staticmethod
    def byname(name):
        return Chord.dict[name]

    @staticmethod
    def random():
        key = random.choice(list(Chord.dict.keys()))
        c = copy.deepcopy(Chord.dict[key])
        c.root = random.randint(0, 12)
        return c

    @staticmethod
    def arbitrary(name="chord"):
        intervals_poss = [2, 3, 3, 4, 4, 5, 6]
        intervals = []
        top = random.randint(12, 18)
        n = 0
        while True:
            interval = random.choice(intervals_poss)
            n += interval
            if n > top:
                break
            intervals.append(interval)

        return Chord(intervals, 0, name)


Chord.major = Chord([4, 3, 5], 0, "major")
Chord.minor = Chord([3, 4, 5], 0, "minor")
Chord.diminished = Chord([3, 3, 6], 0, "diminished")
Chord.augmented = Chord([4, 4, 4], 0, "diminished")
Chord.sus4 = Chord([5, 2, 5], 0, "sus4")
Chord.sus2 = Chord([7, 2, 5], 0, "sus4")
