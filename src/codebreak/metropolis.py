"""Metropolis-Hastings (simulated annealing) substitution cipher solver.

Starting from an initial guess, repeatedly swaps two random alphabet
characters throughout the message. A swap that improves the n-gram score is
always kept; a swap that makes things worse is kept anyway with probability
exp(delta_score / temperature), which lets the search escape local optima.
The temperature is cooled in `intervals` steps from `t_max` down to `t_min`
over the run.
"""

import math
import random
from dataclasses import dataclass, field

from .alphabet import ALPHABET
from .ngrams import NgramScorer
from .substitution import swap_chars


@dataclass
class MetropolisTrace:
    """Per-iteration record of the search, for benchmarking/visualisation."""

    scores: list[float] = field(default_factory=list)
    temperatures: list[float] = field(default_factory=list)
    accepted: list[int] = field(default_factory=list)  # cumulative accepted swaps


@dataclass
class MetropolisResult:
    message: str
    score: float
    trace: MetropolisTrace | None = None


def metropolis_algorithm(
    message: str,
    scorer: NgramScorer,
    t_min: float,
    t_max: float,
    iterations: int,
    intervals: int = 4,
    alphabet: str = ALPHABET,
    rng: random.Random | None = None,
    record: bool = False,
) -> MetropolisResult:
    rng = rng if rng is not None else random
    t_scalar = (t_min / t_max) ** (1 / intervals)
    temperature = t_max
    cooling_step = max(iterations // intervals, 1)

    best_score = float("-inf")
    best_message = message
    trace = MetropolisTrace() if record else None
    accepted_total = 0

    for i in range(iterations):
        score = scorer.score(message)
        new_message = swap_chars(message, *rng.sample(alphabet, 2))
        new_score = scorer.score(new_message)

        if score > best_score:
            best_score = score
            best_message = message

        accepted = new_score > score or rng.random() < math.exp((new_score - score) / temperature)
        if accepted:
            message = new_message
            accepted_total += 1

        if trace is not None:
            trace.scores.append(score)
            trace.temperatures.append(temperature)
            trace.accepted.append(accepted_total)

        if (i + 1) % cooling_step == 0:
            temperature = max(round(temperature * t_scalar, 3), t_min)

    return MetropolisResult(message=best_message, score=best_score, trace=trace)
