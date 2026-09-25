# CI test split optimization

[![tests](https://github.com/pedromorago/ci-test-split-optimization/actions/workflows/tests.yml/badge.svg)](https://github.com/pedromorago/ci-test-split-optimization/actions/workflows/tests.yml)

How to split a Playwright end-to-end suite across parallel CI containers, worked out on real, anonymized CI logs. The question is how many containers the pipeline really needs, and which spec files each one should run, once you account for how Playwright schedules files on its workers.

| Split, 5 workers per container | Pipeline | Cost per run |
|---|---:|---:|
| One container per module (7 containers) | 30.63 min | 6.67 USD |
| Balanced for 1 worker (7 containers), what ran in production | 28.25 min | 6.90 USD |
| **Balanced for 5 workers, 4 containers** | **25.95 min** | **4.08 USD** |
| **Balanced for 5 workers, 3 containers** | **27.89 min** | **3.34 USD** |

With 4 containers the pipeline is 8% faster than the split that ran in production and costs 41% less. With 3 it takes about the same time for 52% less.

## The pipeline

- The end-to-end specs ran in 7 CI containers, one per product module.
- Each container spends about 16 minutes on setup before its first test.
- Then it runs two suites back to back, sanity and then regression, each with 5 Playwright workers.
- `fullyParallel` is off, so Playwright hands out whole spec files: each file goes to the next free worker, in file order, and its tests run one after another.
- Each container is billed at 0.04 USD for every minute it runs.

The modules are not the same size. With 1 worker the admin container ran for 59.7 minutes and the smallest one for 23.8.

## What balancing for 1 worker got right, and wrong

The first model balanced the total test time of each container. Measured with 1 worker, it did exactly what it promised: the pipeline went from 59.73 to 34.81 minutes, 42% faster, at the same cost.

Production runs 5 workers per container, and there the same split is only about 8% faster, for 3% more cost (`results/configurations.md`). Three things eat the gain:

1. **Setup.** With 5 workers the 16 minutes of setup are more than half of every container's run, and no split changes them.
2. **Two suites.** Each suite has to finish before the next starts, so workers wait twice.
3. **One long file.** `rules.spec.ts` takes about 9.5 minutes in the sanity suite. Playwright can't split a file, so the container that runs it can't finish in less than its setup plus those 9.5 minutes.

A model of the pipeline has to include the workers and the suites.

## The model

For each spec file and each container, a binary variable says whether the container runs the file. For each container and suite, the suite can't end before:

- its total file time divided by the number of workers, nor
- its longest file.

The container ends after its setup and both suites, and the model minimizes the end of the slowest container ([`src/ci_split/model.py`](src/ci_split/model.py)). Those bounds hold for any worker schedule, so the model's time is a lower bound.

Playwright's real schedule follows file order, so a split that is optimal in the model can end later in CI. A simulator reproduces that schedule ([`playwright_sim.py`](src/ci_split/playwright_sim.py)), and a local search starts from the model's split and moves or swaps files while the simulated pipeline doesn't get longer ([`search.py`](src/ci_split/search.py)). The simulator reproduces the measured CI jobs with 1 worker to the hundredth of a minute.

## Results

For 2 to 7 containers, with the average measured setup ([`results/containers.md`](results/containers.md)):

| Containers | Pipeline | Cost | Time vs production | Cost vs production |
|---:|---:|---:|---:|---:|
| 2 | 33.93 min | 2.71 USD | +20.1% | −60.7% |
| 3 | 27.89 min | 3.34 USD | −1.3% | −51.6% |
| 4 | 25.95 min | 4.08 USD | −8.2% | −40.9% |
| 5 | 25.95 min | 5.00 USD | −8.2% | −27.4% |
| 6 | 25.95 min | 5.77 USD | −8.2% | −16.3% |
| 7 | 25.95 min | 6.40 USD | −8.2% | −7.3% |

From 4 containers up the pipeline sits at 25.95 minutes: the setup plus the sanity part of `rules.spec.ts` plus its short regression part. More containers only add cost. The spec list for each container is in [`results/splits/`](results/splits).

To get below 26 minutes, the split is no longer the lever. `rules.spec.ts` has to be broken up, or the setup made shorter.

## Limits

- Test durations were measured with 1 worker. With 5 workers hitting the same application at once, tests may run slower, so the numbers with 5 workers are estimates to confirm with a few real runs.
- The averages come from 4 CI cycles. When specs change, the split has to be recomputed.
- The solver runs with a time limit, so another run can find a different split with the same or a very close time.

## Run it

Python 3.11 or later.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m pytest                                          # tests
PYTHONPATH=src python scripts/compare_configurations.py  # results/configurations.md
PYTHONPATH=src python scripts/containers_vs_cost.py      # results/containers.md and results/splits/
```

## Data

[`data/`](data) holds the real CI logs, anonymized: names, identifiers, URLs and dates were replaced, and every test status and duration is untouched. See [`data/README.md`](data/README.md).

## License

MIT, see [LICENSE](LICENSE).
