from __future__ import annotations

import copy
import random
import sys

from .core import Pattern
from .series import PSeries
from ..util import wnchoice, scale_lin_exp


class PStochasticPattern(Pattern):
    """
    PStochasticPattern is the superclass of all chance-based patterns.
    It contains its own random number generator and state, so that it can be
    seeded independently of other RNG processes in the application.

    When it is created, a random seed is generated and stored.
    When reset() is called, the pattern's RNG is re-seeded with this same seed,
    allow it to rewind to the beginning of its random pattern.
    """

    def __init__(self):
        self.rng = random.Random()
        self._seed = self.rng.randint(0, sys.maxsize)
        self.rng.seed(self._seed)

    def __repr__(self):
        return "PStochasticPattern()"

    def reset(self):
        super().reset()
        self.rng.seed(self._seed)

    def seed(self, seed=None):
        """
        Seed the pattern's random number generator with a new seed,
        initialising a new pseudo-random sequence.

        Args:
            seed: A hashable value, or None. See pydoc random.
        """
        if seed is None:
            seed = random.randint(0, sys.maxsize)
        self._seed = seed
        self.rng.seed(self._seed)


class PWhite(PStochasticPattern):
    """PWhite: White noise between `min` and `max`.
    If values are given as floats, output values are also floats < max.
    If values are ints, output values are ints <= max (as random.randint)

    >>> PWhite(0, 10).nextn(16)
    [8, 10, 8, 1, 7, 3, 1, 9, 9, 3, 2, 10, 7, 5, 10, 4]

    >>> PWhite(0.0, 10.0).nextn(16)
    [3.6747936220022082, 0.61313530428271923, 9.1515368696591555, ... 6.2963694390145974 ]
    """

    def __init__(self, v_min: float = 0.0, v_max: float = 1.0):
        super().__init__()

        self.min = v_min
        self.max = v_max

    def __repr__(self):
        return f"PWhite({self.min},{self.max})"

    def __next__(self):
        v_min = Pattern.value(self.min)
        v_max = Pattern.value(self.max)

        if isinstance(v_min, float):
            return self.rng.uniform(v_min, v_max)
        else:
            return int(self.rng.uniform(v_min, v_max))


class PBrown(PStochasticPattern):
    """PBrown: Brownian noise.
    Output begins at `initial_value`, and steps up/down
    by uniform random values from [-`step`, `step`]
    inclusive.

    If step is a float, the output is a float pattern.
    If step is an int, the output is an int pattern,
    with min <= values <= max.
    """

    def __init__(
            self,
            initial_value: float = 0,
            step: float = 0.1,
            v_min: float = -sys.maxsize,
            v_max: float = sys.maxsize,
    ):
        """
        Args:
            initial_value (float or int): Initial value
            step (float or int): Maximum value to increase or decrease by each step
            v_min (float or int): Minimum permitted value
            v_min (float or int): Maximum permitted value
        """
        super().__init__()
        self.initial_value = initial_value
        self.value = initial_value
        self.step = step
        self.min = v_min
        self.max = v_max

    def __repr__(self):
        return f"PBrown({self.initial_value}, {self.step}, {self.min}, {self.max})"

    def reset(self):
        super().reset()
        self.value = self.initial_value

    def __next__(self):
        vstep = Pattern.value(self.step)
        vmin = Pattern.value(self.min)
        vmax = Pattern.value(self.max)

        rv = self.value
        if isinstance(vstep, float):
            self.value += self.rng.uniform(-vstep, vstep)
        else:
            # select new offset
            steps = list(range(-vstep, vstep + 1))
            self.value += self.rng.choice(steps)
        self.value = min(max(self.value, vmin), vmax)

        return rv


class PCoin(PStochasticPattern):
    """PCoin: Coin toss, returning either 0 or 1 given some `probability`.
           `probability` is the chance of returning 1, and must be between [0, 1].

           This is a convenience pattern which could also be written
            as `PWhite(0, 1) < probability`

    >>> PCoin(0.75).nextn(16)
    [1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1]
    """

    def __init__(self, probability: float = 0.5, regular: bool = False):
        super().__init__()
        self.probability = Pattern.pattern(probability)
        self.regular = regular

        self.current_value = 1.0 if regular else 0.0

    def __repr__(self):
        return f"PCoin({self.probability})"

    def __next__(self):
        probability = Pattern.value(self.probability)
        # if not (regular := Pattern.value(self.regular)):
        if not (Pattern.value(self.regular)):
            return 1 if self.rng.uniform(0, 1) < probability else 0
        if self.current_value >= 1:
            self.current_value -= 1
            rv = 1
        else:
            rv = 0
        self.current_value += probability
        return rv


class PRandomWalk(PStochasticPattern):
    """PWalk: Random walk around list.
           Jumps between `min` and `max` steps inclusive.

    >>> PRandomWalk([ 0, 2, 5, 8, 11 ], v_min=1, v_max=2).nextn(16)
    [8, 11, 0, 8, 0, 11, 2, 11, 2, 0, 5, 8, 11, 8, 5, 8]
    """

    def __init__(
            self, values=None, v_min: int = 1, v_max: int = 1, wrap: bool = True
    ):
        """

        Args:
            values (list): Array of values to walk around
            v_min (int): Minimum number of steps to move
            v_max (int): Maximum number of steps to move
            wrap (bool): Whether to wrap around the start/end of the array
        """
        super().__init__()
        self.pos = None
        if values is None:
            values = []
        self.values = values
        self.min = v_min
        self.max = v_max
        self.wrap = wrap
        self.reset()

    def __repr__(self):
        return f"PRandomWalk({repr(self.values)}, {self.min}, {self.max}, {self.wrap})"

    def reset(self):
        super().reset()
        self.pos = 0

    def __next__(self):
        vvalues = Pattern.value(self.values)
        vmin = Pattern.value(self.min)
        vmax = Pattern.value(self.max)

        move = self.rng.randint(vmin, vmax)
        move = 0 - move if self.rng.uniform(0, 1) < 0.5 else move
        self.pos += move

        if self.wrap:
            while self.pos < 0:
                self.pos += len(vvalues)
            while self.pos >= len(vvalues):
                self.pos -= len(vvalues)

        return vvalues[self.pos]


class PChoice(PStochasticPattern):
    """PChoice: Pick a random element from `values`, weighted by optional `weights`.
             `weights` and `values` must be the same length.
             weights do not need to be normalised.

    >>> p = PChoice([ 0, 1, 10, 11 ])
    >>> p.nextn(16)
    [11, 1, 0, 10, 1, 11, 1, 0, 11, 1, 11, 1, 1, 11, 11, 1]

    >>> p = PChoice([ 1, 11, 111 ], [ 8, 2, 1 ])
    >>> p.nextn(16)
    [111, 1, 1, 111, 1, 1, 1, 1, 1, 1, 1, 11, 1, 1, 1, 1]
    """

    def __init__(self, values: list, weights: list = None):
        """
        Args:
            values: A list of values
            weights: An optional list of weights, of the same length as values
        """
        super().__init__()
        self.values = values
        self.weights = weights

    def __repr__(self):
        return f"PChoice({repr(self.values)}, {repr(self.weights)})"

    def __next__(self):
        vvalues = Pattern.value(self.values)
        vweights = Pattern.value(self.weights)
        if vweights is not None:
            return wnchoice(vvalues, vweights, rng=self.rng)
        else:
            return self.rng.choice(vvalues)


class PSample(PStochasticPattern):
    """PSample: Pick multiple random elements from `values`, weighted by optional `weights`,
             without replacement. Each return value is a list.

             `weights` and `values` must be the same length.
             weights do not need to be normalised.

    >>> p = PSample([1, 2, 3], count=2, weights=[1, 2, 3])
    >>> p.nextn(16)
    [[3, 2], [2, 3], [3, 2], [3, 1], [2, 3], [3, 2], [2, 3], [3, 1], [3, 2], [3, 2], [2, 3],
     [3, 2], [2, 1], [2, 3], [3, 2], [2, 3]]
    """

    def __init__(self, values: list, count: int, weights: list = None):
        """
        Args:
            values: A list of values
            weights: An optional list of weights, of the same length as values
        """
        super().__init__()
        self.values = values
        self.count = count
        self.weights = weights

    def __repr__(self):
        return f"PSample({repr(self.values)}, {self.count}, {repr(self.weights)})"

    def __next__(self):
        vvalues = copy.copy(Pattern.value(self.values))
        vcount = copy.copy(Pattern.value(self.count))
        vweights = copy.copy(Pattern.value(self.weights))

        if vcount > len(vvalues):
            raise ValueError(
                "Count cannot be larger than the number of available values"
            )

        rv = []
        for _ in range(vcount):
            if vweights:
                index = wnchoice(list(range(len(vvalues))), vweights, rng=self.rng)
                vweights.pop(index)
            else:
                index = self.rng.randrange(0, len(vvalues))

            rv.append(vvalues.pop(index))

        return rv


class PShuffle(PStochasticPattern):
    """PShuffle: Shuffled list.

    >>> p = PShuffle([ 1, 2, 3 ])
    >>> p.nextn(16)
    [1, 3, 2, 3, 2, 1, 2, 3, 1, 2, 3, 1, 1, 2, 3, 1]
    """

    def __init__(self, values: list = None, repeats: int = sys.maxsize):
        """
        Args:
            values (list): List of values
            repeats (int): Number of times to re-shuffle and iterate
        """
        if values is None:
            values = []
        super().__init__()
        self.values_orig = copy.copy(values)
        self.repeats = repeats

        self.pos = 0
        self.rcount = 1
        self.values = copy.copy(self.values_orig)

    def __repr__(self):
        return f"PShuffle({repr(self.values_orig)}, {self.repeats})"

    def reset(self):
        super().reset()
        self.pos = 0
        self.rcount = 0
        self.values = copy.copy(self.values_orig)

    def __next__(self):
        values = Pattern.value(self.values)
        repeats = Pattern.value(self.repeats)

        if self.pos == 0:
            self.rng.shuffle(self.values)

        if self.pos >= len(values):
            self.rcount += 1
            if self.rcount >= repeats:
                raise StopIteration
            self.pos = 0

        rv = values[self.pos]
        self.pos += 1
        return rv


class PShuffleInput(PStochasticPattern):
    """PShuffleInput: Every `n` steps, take `n` values from `pattern` and reorder.

    >>> p = PShuffleInput(PSeries(0, 1), 4)
    >>> p.nextn(16)
    """

    def __init__(self, pattern: Pattern, every: int = 4):
        super().__init__()
        self.pattern = pattern
        self.every = every
        self.values = []
        self.pos = 0

    def __repr__(self):
        return f"PShuffleInput({repr(self.pattern)}, {self.every})"

    def __next__(self):
        if self.pos >= len(self.values):
            self.pos = 0

        if self.pos == 0:
            kevery = Pattern.value(self.every)
            self.values = self.pattern.nextn(kevery)
            self.rng.shuffle(self.values)

        rv = self.values[self.pos]
        self.pos += 1
        return rv


class PSkip(PStochasticPattern):
    """PSkip: Skip events with some probability, 1 - `play`.
    Set <regular> to True to skip events regularly.
    """

    def __init__(self, pattern: Pattern, play: float, regular: bool = False):
        super().__init__()
        self.pattern = pattern
        self.play = play
        self.regular = regular
        self.pos = 0.0

    def __repr__(self):
        return f"PSkip({repr(self.pattern)}, {self.play}, {self.regular})"

    def __next__(self):
        value = Pattern.value(self.pattern)
        play = Pattern.value(self.play)

        if self.regular:
            self.pos += play
            if self.pos >= 1:
                self.pos -= 1
                return value
        elif self.rng.uniform(0, 1) < play:
            return value

        return None


class PFlipFlop(PStochasticPattern):
    """PFlipFlop: flip a binary bit with some probability.
               <initial> is initial value (0 or 1)
               <p_on> is chance of switching from 0->1
               <p_off> is chance of switching from 1->0

    >>> p = PFlipFlop(0, 0.9, 0.5)
    >>> p.nextn(16)
    [1, 0, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 1]
    """

    def __init__(self, initial: int = 0, p_on: float = 0.5, p_off: float = 0.5):
        super().__init__()
        self.initial = initial
        self.value = initial
        self.p_on = p_on
        self.p_off = p_off

    def __repr__(self):
        return f"PFlipFlop({self.initial}, {self.p_on}, {self.p_off})"

    def reset(self):
        super().reset()
        self.value = self.initial

    def __next__(self):
        self.value = Pattern.value(self.value)
        self.p_on = Pattern.value(self.p_on)
        self.p_off = Pattern.value(self.p_off)

        if self.value == 0:
            if self.rng.uniform(0, 1) < self.p_on:
                self.value = 1
        elif self.rng.uniform(0, 1) < self.p_off:
            self.value = 0

        return self.value


class PSwitchOne(PStochasticPattern):
    """PSwitchOne: Capture `length` input values; loop, repeatedly switching two adjacent values."""

    def __init__(self, pattern: Pattern, length: int = 4):
        super().__init__()
        self.pos = None
        self.values = None
        self.pattern = pattern
        self.length = length
        self.reset()

    def __repr__(self):
        return f"PSwitchOne({repr(self.pattern)}, {self.length})"

    def reset(self):
        super().reset()
        self.values = []
        self.pos = 0

    def __next__(self):
        length = self.value(self.length)

        if len(self.values) < length:
            value = next(self.pattern)
            self.values.append(value)
            self.pos += 1
            return value

        if self.pos >= len(self.values):
            index = self.rng.randint(0, len(self.values)) - 1
            index_p = (index + 1) % len(self.values)
            self.values[index], self.values[index_p] = (
                self.values[index_p],
                self.values[index],
            )
            self.pos = 0

        rv = self.values[self.pos]
        self.pos += 1
        return rv


class PRandomExponential(PStochasticPattern):
    """PRandomExponential: Random uniform on exponential curve between `min` and `max`,
                        both of which must be strictly positive.
    If values are given as floats, output values are also floats < max.
    If values are ints, output values are ints <= max (as random.randint)

    >>> PRandomExponential(1, 100).nextn(16)
    [3, 2, 12, 1, 6, 13, 14, 25, 78, 78, 4, 49, 5, 97, 69, 12]

    >>> PRandomExponential(1.0, 100.0).nextn(16)
    [54.84880471711992, 89.53150541306805, 2.4077905492103318, ... ]
    """

    abbreviation = "prandexp"

    def __init__(self, v_min: float = 1.0, v_max: float = 10.0):
        super().__init__()

        self.min = v_min
        self.max = v_max

    def __repr__(self):
        return f"PRandomExponential({self.min}, {self.max})"

    def __next__(self):
        v_min = Pattern.value(self.min)
        v_max = Pattern.value(self.max)

        norm = self.rng.uniform(0, 1)
        rv = scale_lin_exp(norm, 0, 1, v_min, v_max)
        return rv if isinstance(v_min, float) else int(rv)


class PRandomImpulseSequence(PStochasticPattern):
    """PRandomImpulseSequence: Random sequence of impulses with probability `probability`.

    >>> PRandomImpulseSequence(0.3, 16).nextn(16)
    [...]

    """

    abbreviation = "prandimpseq"

    def __init__(self, probability: float = 0.0, length: int = 8):
        super().__init__()

        self.every_index = None
        self.every_count = None
        self.every_action = None
        self.probability = probability
        self.length = length
        self.current_length = 0
        self.values = []
        self.pos = 0
        self.every(0)

    def __repr__(self):
        return f"PRandomImpulseSequence({self.probability}, {self.length})"

    def generate(self):
        probability = Pattern.value(self.probability)
        self.current_length = Pattern.value(self.length)
        self.values = [
            int(self.rng.uniform(0, 1) < probability)
            for _ in range(self.current_length)
        ]
        self.pos = 0

    def every(self, n: int, action: str = None):
        if action == "explore":
            self.every_action = lambda: self.explore()
        elif action == "reset":
            self.every_action = lambda: self.reset()
        elif action == "generate":
            self.every_action = lambda: self.generate()
        else:
            self.every_action = action
        self.every_count = n
        self.every_index = 0

        # return self so this can be used in scheduling:
        # "active": PRandomImpulseSequence(0.3, 8).every(8, "explore"),
        return self

    def explore(self):
        # TODO: Merge function with PExplorer
        p_switch = 0
        p_mutate = 1
        p_rotate = 2
        op = self.rng.choice([p_switch, p_mutate, p_rotate])
        if op == p_switch:
            indices = list(range(len(self.values)))
            self.rng.shuffle(indices)
            self.values[indices[0]], self.values[indices[1]] = (
                self.values[indices[1]],
                self.values[indices[0]],
            )
        elif op == p_mutate:
            index = random.randrange(len(self.values))
            self.values[index] = 1 - self.values[index]
        elif op == p_rotate:
            direction_right = self.rng.uniform(0, 1) < 0.5
            if direction_right:
                self.values = [self.values[-1]] + self.values[:-1]
            else:
                self.values = self.values[1:] + [self.values[0]]

    def __next__(self):
        if self.every_action:
            if self.every_index == self.every_count:
                self.every_action()
                self.every_index = 0
            self.every_index += 1

        if self.pos >= len(self.values):
            self.pos = 0
            self.current_length = Pattern.value(self.length)
            # --------------------------------------------------------------------------------
            # Each time through the cycle, check if the length input has changed.
            # If yes, change the loop length by appending or trimming.
            # --------------------------------------------------------------------------------
            if self.current_length > len(self.values):
                probability = Pattern.value(self.probability)
                range_diff = self.current_length - len(self.values)
                self.values += [
                    int(self.rng.uniform(0, 1) < probability) for _ in range(range_diff)
                ]
            if self.current_length < len(self.values):
                self.values = self.values[: self.current_length]

        rv = self.values[self.pos]
        self.pos += 1
        return rv
