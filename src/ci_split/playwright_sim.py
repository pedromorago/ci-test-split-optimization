"""How long a container takes when Playwright runs it with several workers.

Without `fullyParallel`, Playwright hands out whole spec files: each file
goes to the next free worker, in file order, and its tests run one after
another. A suite ends when its last worker ends. In the pipeline studied
here each container runs two suites back to back, sanity then regression,
after a setup that doesn't depend on the number of workers.
"""
from __future__ import annotations

import heapq

from .logs import SUITES

USD_PER_CONTAINER_MINUTE = 0.04


def suite_time(file_minutes: list[float], workers: int) -> float:
    """Time for one suite: files go, in the order given, to the first free worker."""
    if workers < 1:
        raise ValueError("workers must be at least 1")
    free_at = [0.0] * workers
    for minutes in file_minutes:
        heapq.heappush(free_at, heapq.heappop(free_at) + minutes)
    return max(free_at)


def container_time(specs: dict[str, dict[str, float]], setup: float, workers: int) -> float:
    """Setup, then each suite in turn, files in alphabetical order (Playwright's default)."""
    total = setup
    for suite in SUITES:
        files = [specs[name][suite] for name in sorted(specs) if specs[name][suite] > 0]
        total += suite_time(files, workers)
    return total


def pipeline(containers: dict[str, dict[str, dict[str, float]]], setups: dict[str, float], workers: int):
    """(pipeline minutes, cost in USD, minutes per container).

    The pipeline ends with its slowest container. Each container is billed
    for as long as it runs.
    """
    times = {c: container_time(specs, setups[c], workers) for c, specs in containers.items()}
    return max(times.values()), USD_PER_CONTAINER_MINUTE * sum(times.values()), times
