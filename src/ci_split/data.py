"""Loads the two measured configurations from `data/`."""
from __future__ import annotations

from pathlib import Path

from .logs import SUITES, read_job_durations, read_logs, setup_times

DATA = Path(__file__).resolve().parents[2] / "data"


def configuration(name: str):
    """(containers, setups) for `by-module` or `balanced`.

    containers[container][spec][suite] = minutes per CI cycle.
    """
    durations = read_logs(DATA / "logs" / name)
    setups = setup_times(durations, read_job_durations(DATA / "job_durations.csv", name))
    containers = {}
    for container, suites in durations.items():
        specs: dict[str, dict[str, float]] = {}
        for suite, times in suites.items():
            for spec, minutes in times.items():
                specs.setdefault(spec, dict.fromkeys(SUITES, 0.0))[suite] += minutes
        containers[container] = specs
    return containers, setups


def all_specs(containers) -> dict[str, dict[str, float]]:
    """Every spec file with its time per suite, whatever container it ran in."""
    return {spec: times for specs in containers.values() for spec, times in specs.items()}
