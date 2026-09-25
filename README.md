# pl-big-operator-input

This directory is a course demo of a new element.

## Instructors

To include the element in your course, use:

```sh
git clone --branch release https://github.com/SybelBlue/pl-big-operator-input.git elements/pl-big-operator-input
```

### For details on the element, [read the `pl-big-operator-input` docs](elements/pl-big-operator-input/README.md)

## Developers

### Prerequisites

Install the following tools before getting started:

- [Python](https://www.python.org/) 3.13 or newer
- [uv](https://docs.astral.sh/uv/)
- [pnpm](https://pnpm.io/) 11.19 or newer
- [GNU Make](https://www.gnu.org/software/make/)
- [Docker](https://www.docker.com/) (optional, for running PrairieLearn in a container)

### Developer Quickstart

Clone the repository, enter its directory, and install the project dependencies:

```sh
export PRAIRIELEARN_PATH=/path/to/PrairieLearn
make install-prairielearn # omit this if the clone already exists
make deps
```

Run the test suite:

```sh
make test
```

Run the same full set of validation checks used by CI:

```sh
make ci-dryrun
```

Start PrairieLearn for local development:

```sh
make dev
```

The development runner will print the local URL to open. To run the official PrairieLearn Docker image instead, use:

```sh
make docker
```

### Repository layout

```text
courseInstances/    Course instances and assessments
elements/           Course-specific PrairieLearn elements and tests
questions/          PrairieLearn questions
serverFilesCourse/  Shared Python helpers and tests
scripts/            Repository maintenance scripts
infoCourse.json     Course metadata, topics, tags, and modules
```

Start customizing the template by updating `infoCourse.json`, the starter course instance under `courseInstances/StarterSemester`, and the example content under `questions/starter`.

### Make targets

| Command | Description |
| --- | --- |
| `make deps` | Fetch PrairieLearn schemas and install Python and Node dependencies |
| `make install-prairielearn` | Clone PrairieLearn into `PRAIRIELEARN_PATH` |
| `make test` | Run helper, element, and question tests |
| `make test-helpers` | Run tests for shared helpers and custom elements |
| `make test-content` | Run question tests |
| `make test-e2e-fuzz` | Fuzz questions affected by the current Git diff |
| `make typecheck` | Type-check Python code with Pyright |
| `make format` | Format Python, JSON, HTML, and Mustache files |
| `make ci-dryrun` | Run tests, type checking, formatting checks, schema checks, and vendor verification |
| `make dev` | Launch the local PrairieLearn development runner |
| `make docker` | Launch PrairieLearn using the official Docker image |
| `make fetch-pl-schemas` | Refresh the local PrairieLearn schemas |
| `make sync-vendor` | Restore vendored dependencies from `plvendor-lock.yaml` |
| `make verify-vendor` | Verify vendored dependencies against their pinned upstream commits |
| `make clean` | Remove local dependencies, caches, and build artifacts |

Pass additional options to pytest with `PYTEST_ARGS`. For example:

```sh
make test PYTEST_ARGS="-x -vv"
```

The question tests run the real Python element lifecycle from the PrairieLearn
revision pinned in `uv.lock`. Set `PRAIRIELEARN_PATH` to a PrairieLearn Git clone
that contains that revision. `make test` checks every question with three generated
variant seeds; on pull requests, CI also checks diff-selected questions with ten
additional fuzz seeds. Useful focused commands include:

```sh
make test-e2e QUESTION_PATHS=questions/s.4
make test-e2e E2E_SEED_COUNT=10
make test-e2e-fuzz E2E_FUZZ_SEED=12345
make test-e2e-fuzz-diff-only E2E_DIFF_BASE=origin/main
```

The diff-only runner tests changed question directories. A non-ignored change
outside `questions/` tests every question; `.question-e2e.diffignore` lists files
that cannot affect question behavior. Every fuzz run reports a master seed and a
replay command. To retain a failing concrete variant seed as a permanent regression
case, run:

```sh
make add-e2e-regression-seed \
  QUESTION_PATH=questions/s.4 \
  VARIANT_SEED=123456789
```

### Typical development workflow

1. Add or edit questions in `questions/`.
2. Reference them from an assessment in `courseInstances/`.
3. Preview the course with `make dev`.
4. Run `make format` and `make ci-dryrun` before committing.
