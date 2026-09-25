"""Reads the anonymized CI logs into spec durations.

Each log line kept in `data/logs` is the result line of one test:

    tests  |   ✓   3 [chrome] › src/tests/admin/audit-log.spec.ts › Audit log › caso 3 (3.6s)

Passed (✓) and failed (✘) tests both count: a failed test still holds its
worker for that long. Skipped tests (-) carry no duration and are ignored.
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

SUITES = ("sanity", "regression")

RESULT_LINE = re.compile(
    r"^tests\s+\|\s+(?P<status>[✓✘])\s+\d+\s+\[\w+\]\s+›\s+src/tests/(?P<spec>\S+\.spec\.ts)\s+›.*"
    r"\((?P<value>[\d.]+)(?P<unit>ms|s|m)\)\s*$"
)
LOG_NAME = re.compile(r"^(?P<container>.+)-(?P<suite>sanity|regression)-(?P<cycle>\d+)\.log$")

_TO_MINUTES = {"ms": 1 / 60000, "s": 1 / 60, "m": 1.0}


def parse_line(line: str) -> tuple[str, float] | None:
    """Returns (spec, minutes) for a passed or failed test line, else None."""
    m = RESULT_LINE.match(line.rstrip("\n"))
    if not m:
        return None
    return m["spec"], float(m["value"]) * _TO_MINUTES[m["unit"]]


# durations[container][suite][spec] = average minutes per CI cycle
Durations = dict[str, dict[str, dict[str, float]]]


def read_logs(folder: str | Path) -> Durations:
    """Average time per spec, per suite and container, over the CI cycles in `folder`."""
    totals: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    cycles: dict = defaultdict(set)
    for path in sorted(Path(folder).glob("*.log")):
        name = LOG_NAME.match(path.name)
        if not name:
            raise ValueError(f"unexpected log name: {path.name}")
        container, suite = name["container"], name["suite"]
        cycles[container, suite].add(name["cycle"])
        totals[container][suite]  # a suite with only skipped tests still exists
        for line in path.open(encoding="utf-8"):
            parsed = parse_line(line)
            if parsed:
                spec, minutes = parsed
                totals[container][suite][spec] += minutes
    return {
        c: {s: {spec: t / len(cycles[c, s]) for spec, t in specs.items()} for s, specs in suites.items()}
        for c, suites in totals.items()
    }


def net_time(durations: Durations, container: str) -> float:
    """Minutes of test execution in a container, both suites, one worker."""
    return sum(sum(specs.values()) for specs in durations[container].values())


def read_job_durations(path: str | Path, config: str) -> dict[str, float]:
    """CI job duration per container for one configuration (`by-module` or `balanced`)."""
    with open(path, newline="", encoding="utf-8") as f:
        return {r["container"]: float(r["job_duration_min"]) for r in csv.DictReader(f) if r["config"] == config}


def setup_times(durations: Durations, jobs: dict[str, float]) -> dict[str, float]:
    """Setup of each container: job duration minus the time its tests took."""
    return {c: jobs[c] - net_time(durations, c) for c in jobs}


def by_spec(durations: Durations) -> dict[str, dict[str, float]]:
    """Per spec file, its time in each suite, whatever container it ran in."""
    out: dict[str, dict[str, float]] = {}
    for suites in durations.values():
        for suite, specs in suites.items():
            for spec, t in specs.items():
                out.setdefault(spec, dict.fromkeys(SUITES, 0.0))[suite] += t
    return out
