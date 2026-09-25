"""MILP that splits spec files across containers run with several workers.

For a container c and a suite k, the suite can't end before
  - its total file time divided by the number of workers, nor
  - its longest file, because a file is never split across workers.
The container ends after its setup and both suites. The model minimizes
the pipeline time, the end of the slowest container.

Those two bounds are what any worker schedule has to respect, so the
model's time is a lower bound. `search.py` then checks the split against
Playwright's real file-order scheduling and improves it.
"""
from __future__ import annotations

import pulp

from .logs import SUITES


def solve(specs: dict[str, dict[str, float]], containers: int, workers: int, setup: float, time_limit: int = 60):
    """Returns (status, model pipeline minutes, split as {container index: [spec, ...]})."""
    names = sorted(specs)
    prob = pulp.LpProblem("ci_split", pulp.LpMinimize)
    x = {(s, c): pulp.LpVariable(f"x_{i}_{c}", cat="Binary") for i, s in enumerate(names) for c in range(containers)}
    suite = {(c, k): pulp.LpVariable(f"suite_{c}_{k}", lowBound=0) for c in range(containers) for k in SUITES}
    pipeline = pulp.LpVariable("pipeline", lowBound=0)
    prob += pipeline

    for s in names:
        prob += pulp.lpSum(x[s, c] for c in range(containers)) == 1, f"once_{names.index(s)}"
    for c in range(containers):
        for k in SUITES:
            prob += suite[c, k] >= pulp.lpSum(specs[s][k] * x[s, c] for s in names) / workers
            for s in names:
                if specs[s][k] > 0:
                    prob += suite[c, k] >= specs[s][k] * x[s, c]
        prob += pipeline >= setup + pulp.lpSum(suite[c, k] for k in SUITES)

    # Containers are interchangeable: pin the longest file to the first one.
    longest = max(names, key=lambda s: max(specs[s].values()))
    prob += x[longest, 0] == 1

    prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit))
    split = {c: [s for s in names if x[s, c].value() > 0.5] for c in range(containers)}
    return pulp.LpStatus[prob.status], pipeline.value(), split


def floor(specs: dict[str, dict[str, float]], setup: float) -> float:
    """No split can beat setup plus the longest file of a suite."""
    return setup + max(max(t.values()) for t in specs.values())
