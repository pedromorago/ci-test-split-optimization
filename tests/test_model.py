import pytest

from ci_split.model import floor, solve
from ci_split.playwright_sim import container_time
from ci_split.search import improve

SPECS = {
    "a.spec.ts": {"sanity": 9, "regression": 0},
    "b.spec.ts": {"sanity": 3, "regression": 2},
    "c.spec.ts": {"sanity": 3, "regression": 2},
    "d.spec.ts": {"sanity": 2, "regression": 4},
    "e.spec.ts": {"sanity": 1, "regression": 4},
}


def test_every_spec_is_placed_once():
    status, _, split = solve(SPECS, containers=2, workers=2, setup=10)
    assert status == "Optimal"
    placed = [s for names in split.values() for s in names]
    assert sorted(placed) == sorted(SPECS)


def test_model_time_is_a_lower_bound_of_the_real_schedule():
    _, model_time, split = solve(SPECS, containers=2, workers=2, setup=10)
    real = max(container_time({s: SPECS[s] for s in names}, 10, 2) for names in split.values())
    assert model_time <= real + 1e-6
    assert model_time >= floor(SPECS, 10) - 1e-6


def test_one_worker_is_plain_balancing():
    # With 1 worker a suite takes the sum of its files: total 30 over 2 containers.
    _, model_time, _ = solve(SPECS, containers=2, workers=1, setup=0)
    assert model_time == pytest.approx(15)


def test_search_never_makes_it_worse():
    _, _, split = solve(SPECS, containers=2, workers=2, setup=10)
    before = max(container_time({s: SPECS[s] for s in names}, 10, 2) for names in split.values())
    better, (after, _) = improve(SPECS, split, setup=10, workers=2, iterations=500)
    assert after <= before
    assert sorted(s for names in better.values() for s in names) == sorted(SPECS)
