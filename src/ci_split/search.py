"""Local search on the real schedule.

Playwright assigns files in alphabetical order, not in the order the MILP
assumes is possible, so a split that is optimal in the model can end a
little later in CI. Starting from the model's split, this moves and swaps
files between containers and keeps any change that doesn't make the
pipeline longer, or the total billed time, whichever comes first.
"""
from __future__ import annotations

import random

from .playwright_sim import container_time


def improve(specs, split, setup: float, workers: int, iterations: int = 20000, seed: int = 1):
    rng = random.Random(seed)
    groups = {c: set(names) for c, names in split.items()}

    def t(c):
        return container_time({s: specs[s] for s in groups[c]}, setup, workers)

    times = {c: t(c) for c in groups}
    score = (max(times.values()), sum(times.values()))
    for _ in range(iterations):
        slow = max(times, key=times.get)
        other = rng.choice([c for c in groups if c != slow])
        a = rng.choice(sorted(groups[slow]))
        b = rng.choice(sorted(groups[other])) if groups[other] and rng.random() < 0.5 else None
        groups[slow].discard(a)
        groups[other].add(a)
        if b:
            groups[other].discard(b)
            groups[slow].add(b)
        new = {**times, slow: t(slow), other: t(other)}
        new_score = (max(new.values()), sum(new.values()))
        if new_score <= score:
            times, score = new, new_score
        else:
            groups[other].discard(a)
            groups[slow].add(a)
            if b:
                groups[slow].discard(b)
                groups[other].add(b)
    return {c: sorted(g) for c, g in groups.items()}, score
