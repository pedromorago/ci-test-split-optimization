import pytest

from ci_split.data import configuration
from ci_split.playwright_sim import pipeline


@pytest.mark.parametrize("name,expected", [("by-module", 59.73), ("balanced", 34.81)])
def test_one_worker_reproduces_the_measured_pipeline(name, expected):
    containers, setups = configuration(name)
    time, _, _ = pipeline(containers, setups, workers=1)
    assert time == pytest.approx(expected, abs=0.01)


def test_balancing_with_one_worker_keeps_the_cost():
    by_module = pipeline(*configuration("by-module"), workers=1)
    balanced = pipeline(*configuration("balanced"), workers=1)
    assert balanced[1] == pytest.approx(by_module[1], rel=0.01)
