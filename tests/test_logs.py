from pathlib import Path

import pytest

from ci_split.logs import by_spec, net_time, parse_line, read_job_durations, read_logs, setup_times

DATA = Path(__file__).resolve().parents[1] / "data"


def test_parse_line_units():
    line = "tests  |   ✓   3 [chrome] › src/tests/admin/audit-log.spec.ts › Audit log › caso 3 ({})"
    assert parse_line(line.format("3.6s")) == ("admin/audit-log.spec.ts", pytest.approx(0.06))
    assert parse_line(line.format("1.7m")) == ("admin/audit-log.spec.ts", pytest.approx(1.7))
    assert parse_line(line.format("600ms")) == ("admin/audit-log.spec.ts", pytest.approx(0.01))


def test_failed_tests_count_and_skipped_do_not():
    failed = "tests  |   ✘  18 [chrome] › src/tests/admin/business-unit.spec.ts › Business unit › caso 4 (1.7m)"
    skipped = "tests  |   -   1 [chrome] › src/tests/admin/archive.spec.ts › Archive › caso 1"
    assert parse_line(failed) == ("admin/business-unit.spec.ts", pytest.approx(1.7))
    assert parse_line(skipped) is None


@pytest.fixture(scope="module")
def by_module():
    return read_logs(DATA / "logs" / "by-module")


def test_every_container_has_both_suites(by_module):
    assert sorted(by_module) == ["admin", "catalog", "editor", "projects-1", "projects-2", "reporting", "rules"]
    assert all(set(s) == {"sanity", "regression"} for s in by_module.values())
    # Some modules run only skipped tests in regression: the suite exists but takes no time.
    assert sum(by_module["editor"]["regression"].values()) == 0


def test_largest_module_dominates(by_module):
    # The admin module alone holds about a third of all test time.
    total = sum(net_time(by_module, c) for c in by_module)
    assert net_time(by_module, "admin") == pytest.approx(43.02, abs=0.01)
    assert total == pytest.approx(126.42, abs=0.01)


def test_setup_is_about_16_minutes_everywhere(by_module):
    setups = setup_times(by_module, read_job_durations(DATA / "job_durations.csv", "by-module"))
    assert all(15.5 < s < 17.0 for s in setups.values())


def test_specs_are_unique_across_containers(by_module):
    specs = by_spec(by_module)
    assert sum(len(s) for suites in by_module.values() for s in suites.values()) >= len(specs)
    assert max(specs.items(), key=lambda kv: kv[1]["sanity"])[0] == "rules/rules.spec.ts"
