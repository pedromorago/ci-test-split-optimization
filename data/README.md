# Data

CI logs from a real end-to-end suite (Playwright, Chromium), anonymized.

## `logs/by-module/`

The original setup: one CI container per product module. 56 logs, one per
container, suite and CI cycle, named `<container>-<suite>-<cycle>.log`.
Seven containers, two suites (`sanity` and `regression`), four cycles.

## `logs/balanced/`

One cycle (14 logs) after the specs were redistributed across the same
seven containers by a balancing model. In these logs the folder in each
spec path is the container the spec was moved to, so `rules/user.spec.ts`
is `user.spec.ts` running in the `rules` container.

## `job_durations.csv`

The duration of each CI job (one container, both suites), as reported by
the CI system. The setup of a container is
this duration minus the time its tests took, and the analysis derives it
that way.

## What was anonymized

Product, module, spec, test, container and CI job names were replaced by
consistent fictitious ones, internal identifiers by consistent fake values,
test management URLs were removed, and dates were shifted by a fixed number
of days. Each log keeps only the result line of every test. The status and
the duration of every test are untouched, so every number in this
repository can be recomputed from these files.
