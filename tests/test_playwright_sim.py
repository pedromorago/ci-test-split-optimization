import pytest

from ci_split.playwright_sim import container_time, pipeline, suite_time


def test_one_worker_is_the_sum():
    assert suite_time([3, 1, 2], 1) == 6


def test_files_go_to_the_first_free_worker_in_order():
    # 5 and 4 start together; 3 goes to the worker that frees at 4.
    assert suite_time([5, 4, 3], 2) == 7
    # The same files, longest first in a different order, end sooner.
    assert suite_time([3, 4, 5], 2) == 8


def test_a_file_is_never_split():
    assert suite_time([9.5, 1, 1, 1], 5) == 9.5


def test_more_workers_than_files():
    assert suite_time([2, 1], 5) == 2
    assert suite_time([], 5) == 0


def test_invalid_workers():
    with pytest.raises(ValueError):
        suite_time([1], 0)


def test_suites_run_one_after_the_other():
    specs = {
        "a.spec.ts": {"sanity": 4, "regression": 1},
        "b.spec.ts": {"sanity": 1, "regression": 3},
    }
    # setup 10 + sanity max(4, 1) + regression max(1, 3)
    assert container_time(specs, setup=10, workers=2) == 17
    assert container_time(specs, setup=10, workers=1) == 19


def test_pipeline_time_and_cost():
    containers = {"x": {"a.spec.ts": {"sanity": 5, "regression": 0}}, "y": {"b.spec.ts": {"sanity": 1, "regression": 0}}}
    time, cost, per = pipeline(containers, {"x": 10, "y": 10}, workers=5)
    assert time == 15
    assert per == {"x": 15, "y": 11}
    assert cost == pytest.approx(0.04 * 26)
